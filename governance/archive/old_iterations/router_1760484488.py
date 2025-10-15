#!/usr/bin/env python3
"""
TRM Routing Inference
Minimal MLX-based routing policy generator
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import mlx.core as mx
    import mlx.nn as nn
    from models.trm import TinyRecursiveModel  # Your existing TRM
except ImportError as e:
    print(f"⚠️  MLX not available: {e}")
    mx, nn = None, None


class TRMRouter:
    """Lightweight TRM-based routing policy generator"""

    def __init__(self, model_path: Optional[str] = None):
        if mx is None:
            raise RuntimeError("MLX not available - install with: pip install mlx mlx-lm")

        self.model_path = model_path or os.getenv(
            "TRM_ROUTER_PATH",
            str(Path(__file__).parent.parent / "checkpoints" / "latest")
        )
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load TRM model and adapter if present"""
        try:
            # Load base model
            config_path = Path(self.model_path) / "config.json"
            if not config_path.exists():
                print(f"⚠️  No config at {config_path}, using defaults")
                from models.trm import TRMConfig
                config = TRMConfig()
            else:
                with open(config_path) as f:
                    config_dict = json.load(f)
                from models.trm import TRMConfig
                config = TRMConfig(**config_dict)

            self.model = TinyRecursiveModel(config)

            # Load weights if available
            weights_path = Path(self.model_path) / "model.safetensors"
            if weights_path.exists():
                weights = mx.load(str(weights_path))
                self.model.update(weights)
                print(f"✅ Loaded TRM from {self.model_path}")
            else:
                print("⚠️  No weights found, using random init")

            mx.eval(self.model)

        except Exception as e:
            print(f"❌ Failed to load TRM: {e}")
            raise

    def embed_prompt(self, prompt: str, meta: Dict[str, Any]) -> mx.array:
        """Create simple embedding from prompt + metadata"""
        # Simplified: hash to fixed-size vector
        # In production, use your sentence-transformer or similar
        import hashlib

        text = f"{prompt} {json.dumps(meta)}"
        hash_bytes = hashlib.sha256(text.encode()).digest()

        # Convert to floats in [-1, 1]
        embedding = []
        for byte in hash_bytes[:32]:  # 32 dims
            embedding.append((byte - 128) / 128.0)

        return mx.array(embedding, dtype=mx.float32)

    def forward(self, embedding: mx.array, num_loops: int = 4) -> mx.array:
        """Run TRM forward pass"""
        try:
            # Reshape for model
            x = mx.expand_dims(embedding, 0)  # [1, dim]

            # Run recursive loops
            output = self.model(x, num_loops=num_loops)

            return output[0]  # Remove batch dim

        except Exception as e:
            print(f"❌ TRM forward failed: {e}")
            raise

    def decode_policy(self, logits: mx.array) -> Dict[str, Any]:
        """Convert logits to routing policy"""
        # Simplified: map output dims to policy fields
        # Dims 0-3: capability scores (code, search, vision, reasoning)
        # Dims 4-7: model selection logits
        # Dims 8-11: budget/context params

        logits_list = logits.tolist()

        # Capability scores (0-3)
        capabilities = {
            "code": float(logits_list[0]) if len(logits_list) > 0 else 0.5,
            "search": float(logits_list[1]) if len(logits_list) > 1 else 0.5,
            "vision": float(logits_list[2]) if len(logits_list) > 2 else 0.5,
            "reasoning": float(logits_list[3]) if len(logits_list) > 3 else 0.5,
        }

        # Model selection (4-7)
        model_scores = logits_list[4:8] if len(logits_list) >= 8 else [0.25] * 4
        models = ["mlx:qwen", "openai:gpt-4", "anthropic:claude", "local:llama"]
        best_model = models[model_scores.index(max(model_scores))]

        # Budget params (8-11)
        max_tokens = int(min(max(logits_list[8] * 4000, 512), 8192)) if len(logits_list) > 8 else 2048
        context_window = int(min(max(logits_list[9] * 32000, 4096), 128000)) if len(logits_list) > 9 else 16384

        return {
            "capabilities": capabilities,
            "selected_model": best_model,
            "max_tokens": max_tokens,
            "context_window": context_window,
            "temperature": 0.7,
            "source": "trm"
        }

    def route(self, prompt: str, meta: Dict[str, Any]) -> Dict[str, Any]:
        """Complete routing: embed → forward → decode"""
        try:
            embedding = self.embed_prompt(prompt, meta)
            logits = self.forward(embedding, num_loops=4)
            policy = self.decode_policy(logits)
            return policy
        except Exception as e:
            # Fallback to heuristic
            print(f"⚠️  TRM routing failed, using heuristic fallback: {e}")
            return self._heuristic_fallback(prompt, meta)

    def _heuristic_fallback(self, prompt: str, meta: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback routing policy if TRM fails"""
        # Simple keyword-based routing
        prompt_lower = prompt.lower()

        if any(word in prompt_lower for word in ["code", "implement", "function", "class"]):
            model = "mlx:qwen"
            caps = {"code": 0.9, "search": 0.3, "vision": 0.1, "reasoning": 0.6}
        elif any(word in prompt_lower for word in ["search", "find", "lookup"]):
            model = "openai:gpt-4"
            caps = {"code": 0.3, "search": 0.9, "vision": 0.2, "reasoning": 0.5}
        else:
            model = "anthropic:claude"
            caps = {"code": 0.5, "search": 0.5, "vision": 0.3, "reasoning": 0.8}

        return {
            "capabilities": caps,
            "selected_model": model,
            "max_tokens": 2048,
            "context_window": 16384,
            "temperature": 0.7,
            "source": "heuristic_fallback"
        }


# Singleton instance
_router_instance: Optional[TRMRouter] = None

def get_router() -> TRMRouter:
    """Get or create router instance"""
    global _router_instance
    if _router_instance is None:
        _router_instance = TRMRouter()
    return _router_instance


def trm_route(prompt: str, meta: Dict[str, Any] = None) -> Dict[str, Any]:
    """Quick helper for routing"""
    router = get_router()
    return router.route(prompt, meta or {})


if __name__ == "__main__":
    # Demo
    router = TRMRouter()

    test_prompts = [
        ("Write a Python function to parse JSON", {}),
        ("Find documentation on async/await in Rust", {}),
        ("Explain transformer architecture", {}),
    ]

    for prompt, meta in test_prompts:
        print(f"\n📝 Prompt: {prompt}")
        policy = router.route(prompt, meta)
        print(f"🎯 Policy: {json.dumps(policy, indent=2)}")

