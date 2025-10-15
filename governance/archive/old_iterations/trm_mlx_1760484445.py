"""
TRM (Tiny Recursive Model) - MLX Implementation

Optimized for Apple Silicon using MLX framework.
Significantly faster than PyTorch on M-series chips.
"""

import math
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import mlx.core as mx
import mlx.nn as nn
from mlx.utils import tree_flatten, tree_unflatten


@dataclass
class TRMCarry:
    """Carry state for TRM reasoning."""
    z_H: mx.array
    z_L: mx.array
    steps: mx.array
    halted: mx.array


class RMSNorm(nn.Module):
    """Root Mean Square Layer Normalization."""

    def __init__(self, dim: int, eps: float = 1e-5):
        super().__init__()
        self.eps = eps
        self.weight = mx.ones((dim,))

    def __call__(self, x: mx.array) -> mx.array:
        """Apply RMS normalization."""
        # Compute RMS
        rms = mx.sqrt(mx.mean(x * x, axis=-1, keepdims=True) + self.eps)
        # Normalize and scale
        return (x / rms) * self.weight


class RotaryEmbedding(nn.Module):
    """Rotary Position Embedding (RoPE)."""

    def __init__(self, dim: int, max_seq_len: int = 2048, base: float = 10000.0):
        super().__init__()
        self.dim = dim
        self.max_seq_len = max_seq_len
        self.base = base

        # Precompute frequencies
        inv_freq = 1.0 / (base ** (mx.arange(0, dim, 2) / dim))
        self.inv_freq = inv_freq

    def __call__(self, seq_len: int) -> Tuple[mx.array, mx.array]:
        """Generate cos and sin for rotary embeddings."""
        # Position indices
        t = mx.arange(seq_len, dtype=mx.float32)

        # Compute frequencies
        freqs = mx.outer(t, self.inv_freq)

        # Repeat for pairs (to match head_dim)
        emb = mx.concatenate([freqs, freqs], axis=-1)

        # Return cos/sin with shape (seq_len, head_dim)
        return mx.cos(emb), mx.sin(emb)


def apply_rotary_pos_emb(x: mx.array, cos: mx.array, sin: mx.array) -> mx.array:
    """Apply rotary position embeddings."""
    # x shape: (batch, num_heads, seq_len, head_dim)
    # cos/sin shape: (seq_len, head_dim)

    # Split x into first and second half
    d = x.shape[-1] // 2
    x1 = x[..., :d]
    x2 = x[..., d:]

    # Also split cos/sin to match
    cos = cos[..., :d]
    sin = sin[..., :d]

    # Reshape cos/sin for broadcasting: (1, 1, seq_len, d)
    cos = cos[None, None, :, :]
    sin = sin[None, None, :, :]

    # Apply rotation
    return mx.concatenate([
        x1 * cos - x2 * sin,
        x2 * cos + x1 * sin
    ], axis=-1)


class SwiGLU(nn.Module):
    """SwiGLU activation function."""

    def __init__(self, hidden_size: int, expansion: float = 4.0):
        super().__init__()
        self.hidden_size = hidden_size
        self.intermediate_size = int(hidden_size * expansion)

        self.w1 = nn.Linear(hidden_size, self.intermediate_size, bias=False)
        self.w2 = nn.Linear(self.intermediate_size, hidden_size, bias=False)
        self.w3 = nn.Linear(hidden_size, self.intermediate_size, bias=False)

    def __call__(self, x: mx.array) -> mx.array:
        """Forward pass."""
        return self.w2(nn.silu(self.w1(x)) * self.w3(x))


class Attention(nn.Module):
    """Multi-head attention."""

    def __init__(
        self,
        hidden_size: int,
        num_heads: int,
        head_dim: Optional[int] = None,
    ):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_heads = num_heads
        self.head_dim = head_dim or (hidden_size // num_heads)

        self.q_proj = nn.Linear(hidden_size, num_heads * self.head_dim, bias=False)
        self.k_proj = nn.Linear(hidden_size, num_heads * self.head_dim, bias=False)
        self.v_proj = nn.Linear(hidden_size, num_heads * self.head_dim, bias=False)
        self.o_proj = nn.Linear(num_heads * self.head_dim, hidden_size, bias=False)

        self.scale = self.head_dim ** -0.5

    def __call__(
        self,
        x: mx.array,
        cos: Optional[mx.array] = None,
        sin: Optional[mx.array] = None,
    ) -> mx.array:
        """Forward pass."""
        B, L, _ = x.shape

        # Project to Q, K, V
        q = self.q_proj(x)
        k = self.k_proj(x)
        v = self.v_proj(x)

        # Reshape for multi-head attention
        q = q.reshape(B, L, self.num_heads, self.head_dim).transpose(0, 2, 1, 3)
        k = k.reshape(B, L, self.num_heads, self.head_dim).transpose(0, 2, 1, 3)
        v = v.reshape(B, L, self.num_heads, self.head_dim).transpose(0, 2, 1, 3)

        # Apply rotary embeddings if provided
        if cos is not None and sin is not None:
            # Trim cos/sin to sequence length
            cos_trimmed = cos[:L, :]
            sin_trimmed = sin[:L, :]
            q = apply_rotary_pos_emb(q, cos_trimmed, sin_trimmed)
            k = apply_rotary_pos_emb(k, cos_trimmed, sin_trimmed)

        # Scaled dot-product attention
        scores = (q @ k.transpose(0, 1, 3, 2)) * self.scale
        attn = mx.softmax(scores, axis=-1)

        # Apply attention to values
        out = attn @ v

        # Reshape and project
        out = out.transpose(0, 2, 1, 3).reshape(B, L, -1)
        return self.o_proj(out)


class TRMBlock(nn.Module):
    """TRM transformer block."""

    def __init__(
        self,
        hidden_size: int,
        num_heads: int,
        expansion: float = 4.0,
        eps: float = 1e-5,
    ):
        super().__init__()
        self.self_attn = Attention(hidden_size, num_heads)
        self.mlp = SwiGLU(hidden_size, expansion)
        self.norm1 = RMSNorm(hidden_size, eps)
        self.norm2 = RMSNorm(hidden_size, eps)

    def __call__(
        self,
        x: mx.array,
        cos: Optional[mx.array] = None,
        sin: Optional[mx.array] = None,
    ) -> mx.array:
        """Forward pass."""
        # Self-attention with post-norm
        x = self.norm1(x + self.self_attn(x, cos, sin))

        # MLP with post-norm
        x = self.norm2(x + self.mlp(x))

        return x


class TRMReasoningModule(nn.Module):
    """TRM reasoning module with multiple layers."""

    def __init__(self, layers: list):
        super().__init__()
        self.layers = layers

    def __call__(
        self,
        hidden_states: mx.array,
        input_injection: mx.array,
        cos: Optional[mx.array] = None,
        sin: Optional[mx.array] = None,
    ) -> mx.array:
        """Forward pass with input injection."""
        hidden_states = hidden_states + input_injection

        for layer in self.layers:
            hidden_states = layer(hidden_states, cos, sin)

        return hidden_states


class TRMInner(nn.Module):
    """Inner TRM model."""

    def __init__(self, config: Dict):
        super().__init__()
        self.config = config

        # I/O layers
        self.embed_scale = math.sqrt(config['hidden_size'])
        self.embed_tokens = nn.Embedding(config['vocab_size'], config['hidden_size'])
        self.lm_head = nn.Linear(config['hidden_size'], config['vocab_size'], bias=False)
        self.q_head = nn.Linear(config['hidden_size'], 2, bias=True)

        # Puzzle embeddings
        self.puzzle_emb_len = -(config.get('puzzle_emb_ndim', 0) // -config['hidden_size'])
        if config.get('puzzle_emb_ndim', 0) > 0:
            self.puzzle_emb = nn.Embedding(
                config['num_puzzle_identifiers'],
                config['puzzle_emb_ndim']
            )

        # Position encodings
        if config.get('pos_encodings') == 'rope':
            self.rotary_emb = RotaryEmbedding(
                config['hidden_size'] // config['num_heads'],
                config['seq_len'] + self.puzzle_emb_len
            )
        elif config.get('pos_encodings') == 'learned':
            self.embed_pos = nn.Embedding(
                config['seq_len'] + self.puzzle_emb_len,
                config['hidden_size']
            )

        # Reasoning layers
        self.L_level = TRMReasoningModule([
            TRMBlock(
                config['hidden_size'],
                config['num_heads'],
                config.get('expansion', 4.0)
            )
            for _ in range(config['L_layers'])
        ])

        # Initial states
        self.H_init = mx.random.normal((config['hidden_size'],))
        self.L_init = mx.random.normal((config['hidden_size'],))

    def input_embeddings(
        self,
        inputs: mx.array,
        puzzle_ids: Optional[mx.array] = None
    ) -> mx.array:
        """Compute input embeddings."""
        # Token embeddings
        embedding = self.embed_tokens(inputs)

        # Add puzzle embeddings if provided
        if puzzle_ids is not None and hasattr(self, 'puzzle_emb'):
            puzzle_emb = self.puzzle_emb(puzzle_ids)
            # Reshape and concatenate
            puzzle_emb = puzzle_emb.reshape(-1, self.puzzle_emb_len, self.config['hidden_size'])
            embedding = mx.concatenate([puzzle_emb, embedding], axis=1)

        # Add position embeddings
        if hasattr(self, 'embed_pos'):
            embedding = 0.707106781 * (embedding + self.embed_pos.weight)

        # Scale
        return self.embed_scale * embedding

    def __call__(
        self,
        inputs: mx.array,
        puzzle_ids: Optional[mx.array] = None,
        z_H: Optional[mx.array] = None,
        z_L: Optional[mx.array] = None,
    ) -> Tuple[mx.array, mx.array, mx.array, mx.array]:
        """Forward pass."""
        batch_size, seq_len = inputs.shape

        # Get position embeddings
        cos, sin = None, None
        if hasattr(self, 'rotary_emb'):
            cos, sin = self.rotary_emb(seq_len + self.puzzle_emb_len)

        # Input embeddings
        input_emb = self.input_embeddings(inputs, puzzle_ids)

        # Determine actual sequence length (including puzzle embeddings)
        actual_seq_len = input_emb.shape[1]

        # Initialize states if needed
        if z_H is None:
            z_H = mx.broadcast_to(
                self.H_init,
                (batch_size, actual_seq_len, self.config['hidden_size'])
            )
        if z_L is None:
            z_L = mx.broadcast_to(
                self.L_init,
                (batch_size, actual_seq_len, self.config['hidden_size'])
            )

        # Recursive reasoning
        H_cycles = self.config.get('H_cycles', 3)
        L_cycles = self.config.get('L_cycles', 6)

        # Most cycles without gradient (for efficiency during training)
        # In inference mode, all cycles are computed
        for h_step in range(H_cycles):
            for l_step in range(L_cycles):
                z_L = self.L_level(z_L, z_H + input_emb, cos, sin)
            z_H = self.L_level(z_H, z_L, cos, sin)

        # Output projections
        logits = self.lm_head(z_H[:, self.puzzle_emb_len:])
        q_logits = self.q_head(z_H[:, 0])  # Use first position for halting

        return z_H, z_L, logits, q_logits


class TRMMLX(nn.Module):
    """
    TRM (Tiny Recursive Model) - MLX Implementation
    
    Optimized for Apple Silicon with MLX framework.
    """

    def __init__(self, config: Dict):
        super().__init__()
        self.config = config
        self.inner = TRMInner(config)

    def __call__(
        self,
        inputs: mx.array,
        puzzle_ids: Optional[mx.array] = None,
        max_steps: int = 16,
    ) -> Dict[str, mx.array]:
        """
        Forward pass with recursive reasoning.
        
        Args:
            inputs: Input token IDs [batch, seq_len]
            puzzle_ids: Puzzle identifiers [batch]
            max_steps: Maximum reasoning steps
            
        Returns:
            Dictionary with outputs and metadata
        """
        batch_size = inputs.shape[0]

        # Initial carry states
        z_H = None
        z_L = None
        halted = mx.zeros((batch_size,), dtype=mx.bool_)
        steps = mx.zeros((batch_size,), dtype=mx.int32)

        # Recursive reasoning loop
        for step in range(max_steps):
            # Update states
            z_H, z_L, logits, q_logits = self.inner(inputs, puzzle_ids, z_H, z_L)

            # Update step counter
            steps = steps + 1

            # Check halting condition
            q_halt = q_logits[:, 0]
            halted = halted | (q_halt > 0) | (steps >= max_steps)

            # Break if all sequences halted
            if mx.all(halted):
                break

        return {
            'logits': logits,
            'q_logits': q_logits,
            'z_H': z_H,
            'z_L': z_L,
            'steps': steps,
            'halted': halted,
        }

    def generate(
        self,
        inputs: mx.array,
        puzzle_ids: Optional[mx.array] = None,
        max_steps: int = 16,
        temperature: float = 1.0,
    ) -> mx.array:
        """
        Generate output tokens.
        
        Args:
            inputs: Input token IDs
            puzzle_ids: Puzzle identifiers
            max_steps: Maximum reasoning steps
            temperature: Sampling temperature
            
        Returns:
            Generated token IDs
        """
        outputs = self(inputs, puzzle_ids, max_steps)
        logits = outputs['logits']

        # Sample or take argmax
        if temperature > 0:
            probs = mx.softmax(logits / temperature, axis=-1)
            # Sample from distribution
            tokens = mx.random.categorical(probs, axis=-1)
        else:
            tokens = mx.argmax(logits, axis=-1)

        return tokens


def count_parameters(model: nn.Module) -> int:
    """Count total parameters in model."""
    nparams = sum(
        x.size for k, x in tree_flatten(model.parameters())
    )
    return nparams


def save_model(model: nn.Module, path: str):
    """Save model weights to file."""
    weights = dict(tree_flatten(model.parameters()))
    mx.savez(path, **weights)
    print(f"Model saved to {path}")


def load_model(model: nn.Module, path: str):
    """Load model weights from file."""
    weights = mx.load(path)
    model.update(tree_unflatten(list(weights.items())))
    print(f"Model loaded from {path}")
    return model


# Example usage
if __name__ == "__main__":
    # Configuration
    config = {
        'batch_size': 2,
        'seq_len': 128,
        'vocab_size': 50000,
        'num_puzzle_identifiers': 1000,
        'hidden_size': 512,
        'expansion': 4,
        'num_heads': 8,
        'H_cycles': 3,
        'L_cycles': 6,
        'L_layers': 2,
        'pos_encodings': 'rope',
        'halt_max_steps': 16,
        'puzzle_emb_ndim': 512,
    }

    # Create model
    model = TRMMLX(config)

    print("TRM-MLX Model")
    print(f"Parameters: {count_parameters(model):,}")
    print("Device: Apple Silicon (MLX)")

    # Test forward pass
    inputs = mx.random.randint(0, config['vocab_size'], (2, 128))
    puzzle_ids = mx.array([0, 1])

    outputs = model(inputs, puzzle_ids, max_steps=3)

    print("\nOutput shapes:")
    print(f"  Logits: {outputs['logits'].shape}")
    print(f"  Steps: {outputs['steps']}")
    print(f"  Halted: {outputs['halted']}")

