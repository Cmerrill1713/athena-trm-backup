"""
Neural Context Encoder
======================

Learned context representations to replace rule-based routing heuristics.
Uses transformer-based encoding to capture subtle query features.

Features:
- Transformer encoder for query understanding
- Learned embeddings for ambiguity, domain, structure, complexity
- Training on historical optimization outcomes
- Confidence scoring with fallback to rule-based
- Efficient inference for real-time routing
"""

import logging
import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset

logger = logging.getLogger(__name__)

# Lazy import to avoid circular dependencies
def _get_federated_imports():
    try:
        from .federated_training import FederatedConfig, ModelUpdate, get_federated_client
        return FederatedConfig, get_federated_client, ModelUpdate
    except ImportError:
        return None, None, None

@dataclass
class QueryContext:
    """Neural context representation."""
    query_text: str
    embedding: np.ndarray
    confidence: float
    features: Dict[str, float]
    raw_features: Dict[str, Any]  # Keep rule-based for fallback

@dataclass
class ContextTrainingExample:
    """Training example for context encoder."""
    query_text: str
    strategy: str  # Target strategy that worked well
    reward: float  # How well it performed
    context_features: Dict[str, Any]  # Rule-based features
    timestamp: datetime

class PositionalEncoding(nn.Module):
    """Standard positional encoding for transformer."""

    def __init__(self, d_model: int, max_len: int = 5000):
        super().__init__()
        position = torch.arange(max_len).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2) * (-math.log(10000.0) / d_model))
        pe = torch.zeros(max_len, 1, d_model)
        pe[:, 0, 0::2] = torch.sin(position * div_term)
        pe[:, 0, 1::2] = torch.cos(position * div_term)
        self.register_buffer('pe', pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.pe[:x.size(0)]

class NeuralContextEncoder(nn.Module):
    """
    Transformer-based context encoder for query understanding.

    Architecture:
    - Token embedding layer
    - Positional encoding
    - Transformer encoder layers
    - Context projection heads (ambiguity, domain, complexity, etc.)
    """

    def __init__(self,
                 vocab_size: int = 30000,
                 d_model: int = 256,
                 nhead: int = 8,
                 num_layers: int = 4,
                 dim_feedforward: int = 512,
                 max_seq_len: int = 512,
                 num_domains: int = 10,
                 dropout: float = 0.1):
        super().__init__()

        self.d_model = d_model
        self.max_seq_len = max_seq_len

        # Token embeddings
        self.token_embedding = nn.Embedding(vocab_size, d_model)
        self.positional_encoding = PositionalEncoding(d_model, max_seq_len)

        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers)

        # Context projection heads
        self.complexity_head = nn.Linear(d_model, 1)  # 0-1 complexity score
        self.ambiguity_head = nn.Linear(d_model, 1)   # 0-1 ambiguity score
        self.domain_head = nn.Linear(d_model, num_domains)  # Domain classification
        self.intent_head = nn.Linear(d_model, 5)      # Intent categories
        self.structural_head = nn.Linear(d_model, 3)  # Question structure

        # Global context representation
        self.context_projection = nn.Linear(d_model, 128)  # Final context vector

        self.dropout = nn.Dropout(dropout)

    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor = None) -> Dict[str, torch.Tensor]:
        """
        Forward pass through context encoder.

        Args:
            input_ids: Token IDs [batch_size, seq_len]
            attention_mask: Attention mask [batch_size, seq_len]

        Returns:
            Dict with context features and final embedding
        """
        # Token embeddings + positional encoding
        embeddings = self.token_embedding(input_ids)  # [batch, seq_len, d_model]
        embeddings = self.positional_encoding(embeddings.transpose(0, 1)).transpose(0, 1)
        embeddings = self.dropout(embeddings)

        # Transformer encoding
        if attention_mask is not None:
            # Convert attention mask for transformer (1 for attend, 0 for mask)
            transformer_mask = attention_mask == 0
            encoded = self.transformer_encoder(embeddings, src_key_padding_mask=transformer_mask)
        else:
            encoded = self.transformer_encoder(embeddings)

        # Global representation (mean pooling)
        if attention_mask is not None:
            # Mask out padding tokens
            expanded_mask = attention_mask.unsqueeze(-1).expand(encoded.size())
            encoded = encoded * expanded_mask
            pooled = encoded.sum(dim=1) / attention_mask.sum(dim=1, keepdim=True)
        else:
            pooled = encoded.mean(dim=1)  # [batch, d_model]

        # Context projections
        complexity_score = torch.sigmoid(self.complexity_head(pooled))  # [batch, 1]
        ambiguity_score = torch.sigmoid(self.ambiguity_head(pooled))    # [batch, 1]

        domain_logits = self.domain_head(pooled)  # [batch, num_domains]
        intent_logits = self.intent_head(pooled)  # [batch, 5]
        structural_logits = self.structural_head(pooled)  # [batch, 3]

        # Final context embedding
        context_embedding = self.context_projection(pooled)  # [batch, 128]

        return {
            'context_embedding': context_embedding,
            'complexity_score': complexity_score.squeeze(-1),
            'ambiguity_score': ambiguity_score.squeeze(-1),
            'domain_logits': domain_logits,
            'intent_logits': intent_logits,
            'structural_logits': structural_logits,
            'pooled_representation': pooled
        }

class ContextDataset(Dataset):
    """Dataset for training context encoder."""

    def __init__(self, examples: List[ContextTrainingExample], tokenizer, max_length: int = 512):
        self.examples = examples
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        example = self.examples[idx]

        # Tokenize query
        encoded = self.tokenizer(
            example.query_text,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )

        # Strategy to target (one-hot or index)
        strategy_map = {
            'cosine_only': 0, 'cross_encoder': 1, 'hybrid': 2,
            'baseline': 3, 'personalized': 4
        }
        strategy_idx = strategy_map.get(example.strategy, 3)  # Default to baseline

        # Context features for auxiliary losses
        complexity = min(example.context_features.get('query_complexity', 0.5), 1.0)
        ambiguity = example.context_features.get('ambiguity', 0.5)

        return {
            'input_ids': encoded['input_ids'].squeeze(),
            'attention_mask': encoded['attention_mask'].squeeze(),
            'strategy_target': strategy_idx,
            'complexity_target': complexity,
            'ambiguity_target': ambiguity,
            'reward': example.reward
        }

class ContextEncoderTrainer:
    """
    Training pipeline for neural context encoder.

    Features:
    - Multi-task learning (strategy prediction + feature regression)
    - Sample weighting by reward
    - Early stopping and model checkpointing
    - Curriculum learning (easy to hard examples)
    """

    def __init__(self,
                 model: NeuralContextEncoder,
                 tokenizer,
                 learning_rate: float = 1e-4,
                 weight_decay: float = 1e-5,
                 device: str = 'auto'):
        self.model = model
        self.tokenizer = tokenizer
        self.device = device if device != 'auto' else ('cuda' if torch.cuda.is_available() else 'cpu')

        self.model.to(self.device)

        # Multi-task loss functions
        self.strategy_loss_fn = nn.CrossEntropyLoss()
        self.complexity_loss_fn = nn.MSELoss()
        self.ambiguity_loss_fn = nn.MSELoss()
        self.domain_loss_fn = nn.CrossEntropyLoss()

        # Optimizer
        self.optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay
        )

        # Learning rate scheduler
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode='min', factor=0.5, patience=3, verbose=True
        )

    def train_epoch(self, dataloader: DataLoader) -> Dict[str, float]:
        """Train for one epoch."""
        self.model.train()
        total_loss = 0
        strategy_correct = 0
        total_samples = 0

        for batch in dataloader:
            input_ids = batch['input_ids'].to(self.device)
            attention_mask = batch['attention_mask'].to(self.device)
            strategy_targets = batch['strategy_target'].to(self.device)
            complexity_targets = batch['complexity_target'].to(self.device)
            ambiguity_targets = batch['ambiguity_target'].to(self.device)
            rewards = batch['reward']

            self.optimizer.zero_grad()

            # Forward pass
            outputs = self.model(input_ids, attention_mask)

            # Multi-task losses
            strategy_loss = self.strategy_loss_fn(outputs['intent_logits'], strategy_targets)
            complexity_loss = self.complexity_loss_fn(outputs['complexity_score'], complexity_targets)
            ambiguity_loss = self.ambiguity_loss_fn(outputs['ambiguity_score'], ambiguity_targets)

            # Sample weighting by reward (higher reward = higher weight)
            sample_weights = torch.tensor(rewards, dtype=torch.float).to(self.device)
            total_loss_batch = (
                0.5 * strategy_loss +
                0.25 * complexity_loss +
                0.25 * ambiguity_loss
            )
            weighted_loss = total_loss_batch * sample_weights.mean()

            # Backward pass
            weighted_loss.backward()
            self.optimizer.step()

            # Metrics
            total_loss += weighted_loss.item()
            _, strategy_preds = torch.max(outputs['intent_logits'], 1)
            strategy_correct += (strategy_preds == strategy_targets).sum().item()
            total_samples += input_ids.size(0)

        return {
            'loss': total_loss / len(dataloader),
            'strategy_accuracy': strategy_correct / total_samples
        }

    def validate(self, dataloader: DataLoader) -> Dict[str, float]:
        """Validation."""
        self.model.eval()
        total_loss = 0
        strategy_correct = 0
        total_samples = 0

        with torch.no_grad():
            for batch in dataloader:
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                strategy_targets = batch['strategy_target'].to(self.device)
                complexity_targets = batch['complexity_target'].to(self.device)
                ambiguity_targets = batch['ambiguity_target'].to(self.device)

                outputs = self.model(input_ids, attention_mask)

                strategy_loss = self.strategy_loss_fn(outputs['intent_logits'], strategy_targets)
                complexity_loss = self.complexity_loss_fn(outputs['complexity_score'], complexity_targets)
                ambiguity_loss = self.ambiguity_loss_fn(outputs['ambiguity_score'], ambiguity_targets)

                total_loss_batch = 0.5 * strategy_loss + 0.25 * complexity_loss + 0.25 * ambiguity_loss
                total_loss += total_loss_batch.item()

                _, strategy_preds = torch.max(outputs['intent_logits'], 1)
                strategy_correct += (strategy_preds == strategy_targets).sum().item()
                total_samples += input_ids.size(0)

        return {
            'loss': total_loss / len(dataloader),
            'strategy_accuracy': strategy_correct / total_samples
        }

    def train(self, train_dataset: ContextDataset, val_dataset: ContextDataset,
              num_epochs: int = 10, batch_size: int = 16, patience: int = 5) -> Dict[str, List[float]]:
        """Full training pipeline with early stopping."""
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

        history = {'train_loss': [], 'train_acc': [], 'val_loss': [], 'val_acc': []}

        best_val_loss = float('inf')
        patience_counter = 0

        for epoch in range(num_epochs):
            # Train
            train_metrics = self.train_epoch(train_loader)
            self.scheduler.step(train_metrics['loss'])

            # Validate
            val_metrics = self.validate(val_loader)

            # Log
            logger.info(f"Epoch {epoch+1}/{num_epochs}")
            logger.info(".4f")
            logger.info(".4f")

            # History
            history['train_loss'].append(train_metrics['loss'])
            history['train_acc'].append(train_metrics['strategy_accuracy'])
            history['val_loss'].append(val_metrics['loss'])
            history['val_acc'].append(val_metrics['strategy_accuracy'])

            # Early stopping
            if val_metrics['loss'] < best_val_loss:
                best_val_loss = val_metrics['loss']
                patience_counter = 0
                # Save best model
                torch.save(self.model.state_dict(), 'best_context_encoder.pt')
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    logger.info(f"Early stopping at epoch {epoch+1}")
                    break

        # Load best model
        self.model.load_state_dict(torch.load('best_context_encoder.pt'))

        return history

class NeuralContextAnalyzer:
    """
    Integration layer for neural context analysis.

    Features:
    - Neural encoding with fallback to rule-based
    - Confidence scoring and uncertainty estimation
    - Real-time inference optimization
    - Continuous learning from new data
    """

    def __init__(self,
                 model_path: Optional[str] = None,
                 tokenizer_name: str = 'bert-base-uncased',
                 confidence_threshold: float = 0.7,
                 device: str = 'auto',
                 enable_federation: bool = False,
                 federated_config: Optional[Any] = None):
        self.confidence_threshold = confidence_threshold
        self.device = device if device != 'auto' else ('cuda' if torch.cuda.is_available() else 'cpu')

        # Load tokenizer (using transformers if available, fallback to simple)
        try:
            from transformers import AutoTokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
            self.using_transformers = True
        except ImportError:
            # Simple fallback tokenizer
            self.tokenizer = self._create_simple_tokenizer()
            self.using_transformers = False

        # Load model if available
        self.model = None
        self.is_trained = False
        if model_path and self._load_model(model_path):
            self.is_trained = True
            logger.info("Loaded trained neural context encoder")
        else:
            logger.info("Using rule-based context analysis (neural model not available)")

        # Training data buffer
        self.training_buffer: List[ContextTrainingExample] = []
        self.max_buffer_size = 10000

        # Federated learning setup
        self.enable_federation = enable_federation
        self.federated_config = federated_config
        self.federated_client = None

        if self.enable_federation:
            FederatedConfig, get_federated_client_fn, _ = _get_federated_imports()
            if FederatedConfig and get_federated_client_fn:
                if self.federated_config is None:
                    self.federated_config = FederatedConfig()
                self.federated_client = get_federated_client_fn(self.federated_config, self.model)
                logger.info("Federated learning enabled for context encoder")
            else:
                logger.warning("Federated learning requested but imports unavailable")

    def _create_simple_tokenizer(self):
        """Simple fallback tokenizer when transformers not available."""
        class SimpleTokenizer:
            def __init__(self):
                self.vocab = {'[PAD]': 0, '[UNK]': 1}
                self.next_id = 2

            def __call__(self, text, max_length=512, padding=True, truncation=True, return_tensors='pt'):
                tokens = text.lower().split()
                token_ids = []

                for token in tokens[:max_length-2]:  # Reserve for special tokens
                    if token not in self.vocab:
                        if len(self.vocab) < 30000:  # Vocab limit
                            self.vocab[token] = self.next_id
                            self.next_id += 1
                        else:
                            token_ids.append(self.vocab['[UNK]'])
                            continue
                    token_ids.append(self.vocab[token])

                # Add special tokens (simplified)
                token_ids = [0] + token_ids + [1]  # PAD + content + UNK

                # Padding/truncation
                if len(token_ids) < max_length:
                    token_ids.extend([0] * (max_length - len(token_ids)))
                else:
                    token_ids = token_ids[:max_length]

                attention_mask = [1 if tid > 0 else 0 for tid in token_ids]

                if return_tensors == 'pt':
                    return {
                        'input_ids': torch.tensor([token_ids]),
                        'attention_mask': torch.tensor([attention_mask])
                    }
                else:
                    return {
                        'input_ids': [token_ids],
                        'attention_mask': [attention_mask]
                    }

        return SimpleTokenizer()

    def _load_model(self, model_path: str) -> bool:
        """Load trained neural context encoder."""
        try:
            # Try to determine model architecture from saved state
            checkpoint = torch.load(model_path, map_location=self.device)

            # Infer architecture from checkpoint
            if 'token_embedding.weight' in checkpoint:
                # Assume our NeuralContextEncoder architecture
                vocab_size = checkpoint['token_embedding.weight'].size(0)
                d_model = checkpoint['token_embedding.weight'].size(1)

                self.model = NeuralContextEncoder(vocab_size=vocab_size, d_model=d_model)
                self.model.load_state_dict(checkpoint)
                self.model.to(self.device)
                self.model.eval()
                return True

        except Exception as e:
            logger.warning(f"Failed to load neural model: {e}")
            return False

        return False

    def analyze_query(self, query: str) -> QueryContext:
        """
        Analyze query context using neural encoder with fallback.

        Returns QueryContext with embedding, confidence, and features.
        """
        # Always compute rule-based features as fallback
        rule_based_features = self._compute_rule_based_features(query)

        if self.is_trained and self.model is not None:
            # Neural analysis
            neural_features = self._compute_neural_features(query)
            confidence = neural_features.get('confidence', 0.0)

            if confidence >= self.confidence_threshold:
                # Use neural features
                return QueryContext(
                    query_text=query,
                    embedding=neural_features['embedding'],
                    confidence=confidence,
                    features={
                        'complexity': neural_features['complexity'],
                        'ambiguity': neural_features['ambiguity'],
                        'domain': neural_features['domain'],
                        'intent': neural_features['intent'],
                        'structure': neural_features['structure']
                    },
                    raw_features=rule_based_features
                )

        # Fallback to rule-based
        return QueryContext(
            query_text=query,
            embedding=np.array([]),  # Empty for rule-based
            confidence=0.5,  # Medium confidence
            features=rule_based_features,
            raw_features=rule_based_features
        )

    def _compute_neural_features(self, query: str) -> Dict[str, Any]:
        """Compute features using neural model."""
        try:
            # Tokenize
            encoded = self.tokenizer(query, return_tensors='pt', max_length=512, truncation=True)
            input_ids = encoded['input_ids'].to(self.device)
            attention_mask = encoded.get('attention_mask', None)
            if attention_mask is not None:
                attention_mask = attention_mask.to(self.device)

            # Forward pass
            with torch.no_grad():
                outputs = self.model(input_ids, attention_mask)

            # Extract features
            complexity = outputs['complexity_score'].cpu().item()
            ambiguity = outputs['ambiguity_score'].cpu().item()

            # Domain classification
            domain_logits = outputs['domain_logits'].cpu().numpy()
            domain_idx = np.argmax(domain_logits, axis=-1)[0]

            # Intent classification
            intent_logits = outputs['intent_logits'].cpu().numpy()
            intent_probs = F.softmax(torch.tensor(intent_logits), dim=-1).numpy()[0]
            intent_idx = np.argmax(intent_probs)

            # Structural classification
            structural_logits = outputs['structural_logits'].cpu().numpy()
            structural_probs = F.softmax(torch.tensor(structural_logits), dim=-1).numpy()[0]
            structural_idx = np.argmax(structural_probs)

            # Context embedding
            embedding = outputs['context_embedding'].cpu().numpy().flatten()

            # Confidence based on prediction certainty
            intent_confidence = np.max(intent_probs)
            structural_confidence = np.max(structural_probs)
            overall_confidence = (intent_confidence + structural_confidence) / 2

            return {
                'embedding': embedding,
                'complexity': complexity,
                'ambiguity': ambiguity,
                'domain': domain_idx,
                'intent': intent_idx,
                'structure': structural_idx,
                'confidence': overall_confidence
            }

        except Exception as e:
            logger.warning(f"Neural feature computation failed: {e}")
            return {'confidence': 0.0}

    def _compute_rule_based_features(self, query: str) -> Dict[str, float]:
        """Rule-based feature computation as fallback."""
        # Query length (normalized)
        length_score = min(len(query.split()) / 50.0, 1.0)

        # Complexity via entropy
        words = query.lower().split()
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1

        total_words = len(words)
        if total_words == 0:
            entropy = 0.0
        else:
            entropy = -sum((count/total_words) * math.log(count/total_words)
                          for count in word_freq.values()) / math.log(total_words)
        complexity = min(entropy, 1.0)

        # Ambiguity via question words and uncertainty
        ambiguity_indicators = ['or', 'maybe', 'perhaps', 'could', 'might', 'how', 'what', 'why']
        ambiguity_score = min(sum(1 for word in words if word in ambiguity_indicators) / 5.0, 1.0)

        # Simple intent detection
        intent_scores = {
            'simple': 0.8 if length_score < 0.3 and complexity < 0.3 else 0.2,
            'complex': 0.8 if complexity > 0.7 else 0.2,
            'diagnostic': 0.9 if any(word in query.lower() for word in ['diagnosis', 'symptom', 'medical', 'clinical']) else 0.1,
            'policy': 0.9 if any(word in query.lower() for word in ['policy', 'compliance', 'legal', 'regulation']) else 0.1,
            'general': 0.5
        }
        intent = max(intent_scores.items(), key=lambda x: x[1])[0]

        # Domain classification (simplified)
        domain_keywords = {
            'technical': ['api', 'code', 'software', 'algorithm', 'system'],
            'medical': ['patient', 'treatment', 'diagnosis', 'clinical'],
            'legal': ['contract', 'liability', 'compliance', 'regulation'],
            'business': ['revenue', 'customer', 'market', 'strategy'],
            'general': []
        }

        domain_scores = {}
        for domain, keywords in domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in query.lower()) / max(len(keywords), 1)
            domain_scores[domain] = score

        domain = max(domain_scores.items(), key=lambda x: x[1])
        domain_score = domain[1]

        return {
            'query_length': length_score,
            'query_complexity': complexity,
            'ambiguity': ambiguity_score,
            'intent': intent,
            'domain': domain[0],
            'domain_confidence': domain_score
        }

    def add_training_example(self, query: str, strategy: str, reward: float,
                           context_features: Dict[str, Any]):
        """Add example to training buffer."""
        example = ContextTrainingExample(
            query_text=query,
            strategy=strategy,
            reward=reward,
            context_features=context_features,
            timestamp=datetime.now()
        )

        self.training_buffer.append(example)

        # Maintain buffer size
        if len(self.training_buffer) > self.max_buffer_size:
            self.training_buffer = self.training_buffer[-self.max_buffer_size:]

    def train_on_buffer(self, epochs: int = 5, batch_size: int = 16) -> bool:
        """Train neural model on accumulated examples."""
        if len(self.training_buffer) < 100:
            logger.info(f"Insufficient training data: {len(self.training_buffer)} < 100")
            return False

        try:
            # Create datasets
            train_size = int(0.8 * len(self.training_buffer))
            train_examples = self.training_buffer[:train_size]
            val_examples = self.training_buffer[train_size:]

            train_dataset = ContextDataset(train_examples, self.tokenizer)
            val_dataset = ContextDataset(val_examples, self.tokenizer)

            # Initialize model if not exists
            if self.model is None:
                self.model = NeuralContextEncoder()

            # Train
            trainer = ContextEncoderTrainer(self.model, self.tokenizer)
            history = trainer.train(train_dataset, val_dataset, epochs, batch_size)

            # Check if training was successful
            final_val_acc = history['val_acc'][-1]
            if final_val_acc > 0.6:  # Reasonable accuracy threshold
                self.is_trained = True
                logger.info(f"Neural context encoder trained successfully (val_acc: {final_val_acc:.3f})")
                return True
            else:
                logger.warning(f"Training completed but accuracy too low: {final_val_acc:.3f}")
                return False

        except Exception as e:
            logger.error(f"Training failed: {e}")
            return False

    def participate_in_federated_round(self, round_id: str, training_metrics: Dict) -> bool:
        """Participate in a federated learning round."""
        if not self.enable_federation or not self.federated_client:
            logger.warning("Federated learning not enabled")
            return False

        return self.federated_client.participate_in_round(round_id, training_metrics)

    def sync_with_global_model(self, version: Optional[str] = None) -> bool:
        """Sync local model with latest global federated model."""
        if not self.enable_federation or not self.federated_client:
            logger.warning("Federated learning not enabled")
            return False

        try:
            global_params = self.federated_client.get_global_model(version)
            if global_params:
                self.federated_client.update_local_model(global_params)
                logger.info("Successfully synced with global federated model")
                return True
            else:
                logger.info("No global model available for sync")
                return False

        except Exception as e:
            logger.error(f"Failed to sync with global model: {e}")
            return False

    def check_federated_rounds(self) -> List[str]:
        """Check for available federated rounds to participate in."""
        if not self.enable_federation or not self.federated_client:
            return []

        try:
            # This would typically query the coordinator for active rounds
            # For now, return empty list - would be implemented with actual coordinator communication
            return []
        except Exception as e:
            logger.error(f"Failed to check federated rounds: {e}")
            return []

    def get_federation_stats(self) -> Dict:
        """Get federated learning statistics."""
        if not self.enable_federation or not self.federated_client:
            return {'federation_enabled': False}

        try:
            coordinator = self.federated_client.coordinator
            active_rounds = list(coordinator.active_rounds.keys())
            completed_rounds = len(coordinator.completed_rounds)
            total_participations = sum(len(r.updates_received) for r in coordinator.completed_rounds
                                     if self.federated_config.deployment_id in r.participants)

            return {
                'federation_enabled': True,
                'deployment_id': self.federated_config.deployment_id,
                'active_rounds': active_rounds,
                'completed_rounds': completed_rounds,
                'total_participations': total_participations,
                'coordinator_url': self.federated_config.coordinator_url
            }

        except Exception as e:
            logger.error(f"Failed to get federation stats: {e}")
            return {'federation_enabled': True, 'error': str(e)}

    def opt_out_of_federation(self):
        """Opt out of federated learning."""
        if self.enable_federation and self.federated_client:
            try:
                self.federated_client.coordinator.registry.opt_out_deployment(
                    self.federated_config.deployment_id)
                logger.info("Opted out of federated learning")
            except Exception as e:
                logger.error(f"Failed to opt out of federation: {e}")

    def get_stats(self) -> Dict:
        """Get analyzer statistics."""
        return {
            'is_trained': self.is_trained,
            'buffer_size': len(self.training_buffer),
            'using_transformers': self.using_transformers,
            'confidence_threshold': self.confidence_threshold,
            'device': self.device
        }

# Global analyzer instance
_neural_analyzer = None

def get_neural_context_analyzer(model_path: Optional[str] = None) -> NeuralContextAnalyzer:
    """Get or create global neural context analyzer instance."""
    global _neural_analyzer
    if _neural_analyzer is None:
        _neural_analyzer = NeuralContextAnalyzer(model_path=model_path)
    return _neural_analyzer
