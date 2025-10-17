#!/usr/bin/env python3
"""
Generate mock embeddings for model profiles (no ML dependencies).

Creates deterministic embeddings based on domain and description
using simple hashing + normalization.
"""

import json
import hashlib
import numpy as np
from pathlib import Path


def generate_mock_embedding(text: str, dim: int = 384) -> list:
    """
    Generate deterministic mock embedding from text.
    
    Uses hash of text to seed random number generator for reproducibility.
    
    Args:
        text: Input text
        dim: Embedding dimension
    
    Returns:
        Normalized embedding vector
    """
    # Hash text to get deterministic seed
    seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**32)
    
    # Generate random vector with this seed
    rng = np.random.RandomState(seed)
    embedding = rng.randn(dim).astype(np.float32)
    
    # Normalize to unit length
    embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
    
    return embedding.tolist()


def main():
    """Generate mock embeddings for all models."""
    profiles_path = Path("governance/routing/model_profiles.json")
    
    print(f"Loading profiles from {profiles_path}...")
    with open(profiles_path) as f:
        data = json.load(f)
    
    models = data.get('models', [])
    print(f"Found {len(models)} models\n")
    
    for model in models:
        model_id = model['model_id']
        domain = model.get('domain', 'general')
        description = model.get('metadata', {}).get('description', model_id)
        
        # Generate embedding based on domain + description
        text = f"Domain: {domain}. {description}"
        embedding = generate_mock_embedding(text, dim=384)
        
        model['domain_embedding'] = embedding
        model['is_approximate'] = True
        model['confidence'] = 0.8  # Mock embeddings have lower confidence
        
        print(f"✅ {model_id}: Generated {len(embedding)}-dim embedding")
    
    # Write back
    print(f"\nWriting updated profiles to {profiles_path}...")
    with open(profiles_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Complete! {len(models)} models updated with embeddings.\n")


if __name__ == '__main__':
    main()

