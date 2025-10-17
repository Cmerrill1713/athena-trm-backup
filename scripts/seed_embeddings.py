#!/usr/bin/env python3
"""
Bootstrap domain embeddings for model profiles.

Uses sentence-transformers to generate approximate embeddings
from model descriptions when real embeddings are not available.
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List

# Check if sentence-transformers is available
try:
    from sentence_transformers import SentenceTransformer
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    print("WARNING: sentence-transformers not installed.")
    print("Install with: pip install sentence-transformers")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EmbeddingBootstrapper:
    """Bootstrap domain embeddings for models."""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize with a sentence transformer model.
        
        Args:
            model_name: HuggingFace model name (default: all-MiniLM-L6-v2, 384-dim)
        """
        if not HAS_TRANSFORMERS:
            raise ImportError(
                "sentence-transformers required. "
                "Install with: pip install sentence-transformers"
            )
        
        logger.info(f"Loading sentence transformer: {model_name}")
        self.embedder = SentenceTransformer(model_name)
        logger.info(f"Model loaded. Embedding dimension: {self.embedder.get_sentence_embedding_dimension()}")
    
    def bootstrap_embedding(
        self,
        model_id: str,
        domain: str,
        description: str
    ) -> List[float]:
        """
        Generate approximate embedding from model description.
        
        Args:
            model_id: Model identifier
            domain: Domain category
            description: Model description
        
        Returns:
            Embedding vector
        """
        # Combine domain and description for better context
        text = f"Domain: {domain}. {description}"
        
        logger.debug(f"Generating embedding for {model_id}: {text[:100]}...")
        embedding = self.embedder.encode(text, convert_to_numpy=True)
        
        return embedding.tolist()
    
    def process_profiles(
        self,
        profiles_path: Path,
        output_path: Path,
        force: bool = False
    ):
        """
        Process model profiles and add embeddings.
        
        Args:
            profiles_path: Input profiles JSON
            output_path: Output profiles JSON with embeddings
            force: Overwrite existing embeddings
        """
        logger.info(f"Loading profiles from {profiles_path}")
        with open(profiles_path) as f:
            data = json.load(f)
        
        models = data.get('models', [])
        updated = 0
        skipped = 0
        
        for model in models:
            model_id = model['model_id']
            
            # Check if embedding exists and is not empty
            has_embedding = (
                'domain_embedding' in model 
                and model['domain_embedding']
                and len(model['domain_embedding']) > 0
            )
            
            if has_embedding and not force:
                logger.info(f"Skipping {model_id} (already has embedding)")
                skipped += 1
                continue
            
            # Generate embedding
            domain = model.get('domain', 'general')
            description = model.get('metadata', {}).get('description', model_id)
            
            embedding = self.bootstrap_embedding(model_id, domain, description)
            
            model['domain_embedding'] = embedding
            model['is_approximate'] = True
            model['confidence'] = 0.6  # Mark as approximate
            
            logger.info(
                f"Generated embedding for {model_id} "
                f"(domain: {domain}, dim: {len(embedding)})"
            )
            updated += 1
        
        # Write output
        logger.info(f"Writing updated profiles to {output_path}")
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(
            f"✅ Complete! Updated: {updated}, Skipped: {skipped}, "
            f"Total: {len(models)}"
        )


def main():
    parser = argparse.ArgumentParser(
        description='Bootstrap domain embeddings for model profiles'
    )
    parser.add_argument(
        '--input',
        type=Path,
        default=Path('governance/routing/model_profiles.json'),
        help='Input model profiles JSON'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('governance/routing/model_profiles.json'),
        help='Output model profiles JSON (can be same as input)'
    )
    parser.add_argument(
        '--model',
        type=str,
        default='all-MiniLM-L6-v2',
        help='Sentence transformer model name'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Overwrite existing embeddings'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable debug logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if not HAS_TRANSFORMERS:
        logger.error(
            "sentence-transformers not installed. "
            "Install with: pip install sentence-transformers"
        )
        return 1
    
    try:
        bootstrapper = EmbeddingBootstrapper(model_name=args.model)
        bootstrapper.process_profiles(
            profiles_path=args.input,
            output_path=args.output,
            force=args.force
        )
        return 0
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    exit(main())

