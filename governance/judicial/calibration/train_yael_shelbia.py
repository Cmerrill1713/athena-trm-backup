#!/usr/bin/env python3
"""
Yael Shelbia Avatar Training Script
===================================

Trains a photorealistic 3D avatar using SplattingAvatar framework.
Optimized for Athena's appearance and expression requirements.

Usage:
    python train_yael_shelbia.py --data_path data/yael_shelbia [--epochs 20]

Requirements:
    - 50+ high-quality face images/videos
    - PyTorch with CUDA support (optional but recommended)
    - 8GB+ RAM, GPU with 4GB+ VRAM
"""

import os
import sys
import argparse
import torch
from pathlib import Path

# Add SplattingAvatar to path
sys.path.append('.')

def setup_environment():
    """Setup training environment and dependencies"""
    print("🎭 Setting up Yael Shelbia avatar training environment...")

    # Check for CUDA
    if torch.cuda.is_available():
        print(f"✅ CUDA available: {torch.cuda.get_device_name()}")
        device = torch.device("cuda")
    else:
        print("⚠️  CUDA not available, using CPU (slower)")
        device = torch.device("cpu")

    return device

def validate_data(data_path: str) -> bool:
    """Validate training data"""
    data_dir = Path(data_path)

    if not data_dir.exists():
        print(f"❌ Training data directory not found: {data_path}")
        print("   Please create data/yael_shelbia/ and add face images/videos")
        return False

    # Count image files
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    image_files = []
    for ext in image_extensions:
        image_files.extend(list(data_dir.glob(f'**/*{ext}')))

    if len(image_files) < 10:
        print(f"⚠️  Only {len(image_files)} images found. Recommended: 50+")
        return False

    print(f"✅ Found {len(image_files)} training images")
    return True

def create_training_config(data_path: str, output_path: str, epochs: int = 20):
    """Create SplattingAvatar training configuration"""

    config = {
        # Data configuration
        "data": {
            "data_path": data_path,
            "identity": "yael_shelbia",
            "image_size": 512,
            "batch_size": 4,
        },

        # Model configuration
        "model": {
            "gaussian_count": 50000,  # Number of 3D Gaussians
            "sh_degree": 3,           # Spherical harmonics degree
            "opacity_threshold": 0.005,
        },

        # Training configuration
        "training": {
            "epochs": epochs,
            "learning_rate": 0.00016,
            "position_lr_init": 0.00016,
            "position_lr_final": 0.0000016,
            "position_lr_delay_mult": 0.01,
            "position_lr_max_steps": 30000,
            "feature_lr": 0.0025,
            "opacity_lr": 0.05,
            "scaling_lr": 0.005,
            "rotation_lr": 0.001,
        },

        # Loss weights
        "loss": {
            "rgb_weight": 1.0,
            "mask_weight": 1.0,
            "depth_weight": 0.1,
            "normal_weight": 0.1,
        },

        # Output configuration
        "output": {
            "output_path": output_path,
            "checkpoint_interval": 1000,
            "eval_interval": 500,
        },

        # Athena-specific optimizations
        "athena": {
            "expression_support": True,
            "viseme_count": 6,  # ah, oh, ee, oo, mm, rest
            "head_pose_range": [-15, 15],  # degrees
            "eye_tracking": False,  # Can be added later
        }
    }

    return config

def train_avatar(config: dict, device: torch.device):
    """Run SplattingAvatar training"""
    print("🚀 Starting Yael Shelbia avatar training...")

    # Import SplattingAvatar components
    try:
        from train import Trainer
        from data.dataset import FaceDataset
        from model.gaussian_model import GaussianModel
    except ImportError as e:
        print(f"❌ Failed to import SplattingAvatar components: {e}")
        print("   Make sure you're in the SplattingAvatar directory")
        return False

    # Initialize dataset
    dataset = FaceDataset(
        data_path=config["data"]["data_path"],
        image_size=config["data"]["image_size"]
    )

    # Initialize model
    model = GaussianModel(
        sh_degree=config["model"]["sh_degree"],
        gaussian_count=config["model"]["gaussian_count"]
    )

    # Initialize trainer
    trainer = Trainer(
        model=model,
        dataset=dataset,
        config=config,
        device=device
    )

    # Run training
    try:
        trainer.train()
        print("✅ Training completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Training failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Train Yael Shelbia avatar")
    parser.add_argument("--data_path", type=str, default="data/yael_shelbia",
                       help="Path to training data directory")
    parser.add_argument("--output_path", type=str, default="output/yael_shelbia",
                       help="Path to output directory")
    parser.add_argument("--epochs", type=int, default=20,
                       help="Number of training epochs")
    parser.add_argument("--skip_validation", action="store_true",
                       help="Skip data validation")

    args = parser.parse_args()

    # Setup
    device = setup_environment()

    # Validate data
    if not args.skip_validation and not validate_data(args.data_path):
        return 1

    # Create configuration
    config = create_training_config(args.data_path, args.output_path, args.epochs)

    # Run training
    success = train_avatar(config, device)

    if success:
        print("\n🎭 Yael Shelbia avatar training complete!")
        print(f"   Model saved to: {args.output_path}")
        print("\nNext steps:")
        print("   1. Run: python run_viewer.py --identity yael_shelbia")
        print("   2. Update AvatarBridge.renderMode = .local")
        print("   3. Build NeuroForgeApp to see the avatar")
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())
