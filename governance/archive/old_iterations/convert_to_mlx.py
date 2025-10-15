#!/usr/bin/env python3
"""
Convert PyTorch TRM model to MLX format

This script converts trained PyTorch TRM checkpoints to MLX format
for optimal performance on Apple Silicon.
"""

import argparse
import json
from pathlib import Path

import mlx.core as mx
import torch

from models.recursive_reasoning.trm_mlx import TRMMLX, save_model


def convert_pytorch_to_mlx(pytorch_checkpoint: str, output_path: str, config: dict):
    """
    Convert PyTorch checkpoint to MLX format.
    
    Args:
        pytorch_checkpoint: Path to PyTorch .pt file
        output_path: Path to save MLX .npz file
        config: Model configuration
    """
    print(f"Converting {pytorch_checkpoint} to MLX format...")

    # Load PyTorch model
    print("Loading PyTorch checkpoint...")
    state_dict = torch.load(pytorch_checkpoint, map_location='cpu')

    # Create MLX model
    print("Creating MLX model...")
    mlx_model = TRMMLX(config)

    # Convert weights
    print("Converting weights...")
    mlx_weights = {}

    for key, value in state_dict.items():
        # Remove module prefix if present
        clean_key = key.replace('_orig_mod.', '').replace('model.inner.', 'inner.')

        # Convert PyTorch tensor to MLX array
        numpy_value = value.cpu().numpy()
        mlx_value = mx.array(numpy_value)

        mlx_weights[clean_key] = mlx_value
        print(f"  {clean_key}: {mlx_value.shape}")

    # Update model
    from mlx.utils import tree_unflatten
    mlx_model.update(tree_unflatten(list(mlx_weights.items())))

    # Save MLX model
    print(f"\nSaving MLX model to {output_path}...")
    save_model(mlx_model, output_path)

    # Save config
    config_path = str(Path(output_path).with_suffix('.json'))
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"Config saved to {config_path}")

    # Verify
    print("\nVerifying conversion...")
    from models.recursive_reasoning.trm_mlx import count_parameters, load_model

    verify_model = TRMMLX(config)
    load_model(verify_model, output_path)

    print(f"✓ MLX model parameters: {count_parameters(verify_model):,}")
    print("✓ Conversion complete!")

    return mlx_model


def main():
    parser = argparse.ArgumentParser(description='Convert PyTorch TRM to MLX')
    parser.add_argument('--checkpoint', type=str, required=True,
                       help='Path to PyTorch checkpoint (.pt)')
    parser.add_argument('--output', type=str, required=True,
                       help='Path to save MLX model (.npz)')
    parser.add_argument('--config', type=str,
                       help='Path to config JSON (optional, will use defaults)')

    args = parser.parse_args()

    # Load or create config
    if args.config:
        with open(args.config) as f:
            config = json.load(f)
    else:
        # Default config
        config = {
            'batch_size': 1,
            'seq_len': 900,  # 30x30 grid
            'vocab_size': 50000,
            'num_puzzle_identifiers': 1000,
            'hidden_size': 512,
            'expansion': 4,
            'num_heads': 8,
            'H_cycles': 3,
            'L_cycles': 6,
            'L_layers': 2,
            'H_layers': 0,
            'pos_encodings': 'rope',
            'halt_max_steps': 16,
            'halt_exploration_prob': 0.0,
            'puzzle_emb_ndim': 512,
            'mlp_t': False,
            'puzzle_emb_len': 16,
            'no_ACT_continue': True,
        }

    # Convert
    convert_pytorch_to_mlx(args.checkpoint, args.output, config)

    print("\n" + "="*60)
    print("Next steps:")
    print(f"1. Test MLX model: python test_mlx_model.py --model {args.output}")
    print("2. Use in MacOS-Agent: See MacOS-Agent/trm_integration_mlx.py")
    print("3. Use in PydanticAI: See pydantic-ai/examples/trm_agent_mlx.py")
    print("="*60)


if __name__ == "__main__":
    main()

