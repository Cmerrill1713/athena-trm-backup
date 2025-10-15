"""
Thin wrapper so trm_router.py can call tiny model regardless of internal layout.
Replace TODOs with your actual TRM load/forward (you already have pretrain/evaluate code).
"""
import json
import pathlib
from typing import Dict


class TinyModel:
    """Stub TRM model - replace with your actual implementation"""

    def __init__(self, ckpt: pathlib.Path):
        self.ckpt = ckpt
        # TODO: Load actual model weights
        print(f"📦 Loaded TRM from {ckpt}")

    def forward(self, embedding, num_loops=4) -> Dict[str, float]:
        """
        TODO: Real forward pass; return logits dict for policy
        
        Expected output format:
        {
            "caps_code": 0.0-1.0,
            "caps_rag": 0.0-1.0,
            "caps_reason": 0.0-1.0,
            "caps_vision": 0.0-1.0,
            "model_mlx": 0.0-1.0,
            "model_openai": 0.0-1.0,
            "model_anthropic": 0.0-1.0,
            "model_local": 0.0-1.0,
            ...
        }
        """
        # Stub: return reasonable defaults
        return {
            "caps_code": 0.7,
            "caps_rag": 0.8,
            "caps_reason": 0.6,
            "caps_vision": 0.3,
            "model_mlx": 0.6,
            "model_openai": 0.3,
            "model_anthropic": 0.1,
            "model_local": 0.0
        }


def load_trm(model_path: str) -> TinyModel:
    """
    Load TRM model from checkpoint
    
    Args:
        model_path: Path to model checkpoint directory
    
    Returns:
        Loaded TinyModel instance
    """
    ckpt = pathlib.Path(model_path)
    if not ckpt.exists():
        raise FileNotFoundError(f"Model checkpoint not found: {ckpt}")
    return TinyModel(ckpt)


def trm_forward(model: TinyModel, embedding, num_loops=4) -> Dict[str, float]:
    """
    Run forward pass through TRM
    
    Args:
        model: Loaded TinyModel instance
        embedding: Input embedding (vector)
        num_loops: Number of recursive reasoning loops
    
    Returns:
        Policy logits dictionary
    """
    return model.forward(embedding, num_loops=num_loops)


if __name__ == "__main__":
    # Quick test
    import sys

    try:
        model = load_trm("checkpoints/latest")
        logits = trm_forward(model, [0.1] * 32, num_loops=4)
        print("✅ TRM inference test:")
        print(json.dumps(logits, indent=2))
    except FileNotFoundError as e:
        print(f"⚠️  {e}")
        print("   This is expected if you haven't trained a model yet")
        print("   The stub returns reasonable defaults")
        sys.exit(0)

