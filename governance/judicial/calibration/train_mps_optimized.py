#!/usr/bin/env python3
"""
MPS-Optimized Avatar Training for Apple Silicon
Trains a neural avatar using the collected Yael Shelbia dataset
"""

import os
import sys
import argparse
from pathlib import Path
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import transforms
from PIL import Image
from tqdm import tqdm
import json

# Device selection (MPS for Apple Silicon GPU)
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
print(f"🚀 Using device: {device}")
if device.type == "mps":
    print("✅ Apple Silicon GPU acceleration enabled!")

class SimpleAvatarDataset(torch.utils.data.Dataset):
    """Dataset loader for avatar training images"""
    
    def __init__(self, image_dir, transform=None):
        self.image_dir = Path(image_dir)
        self.image_paths = list(self.image_dir.glob("*.jpg")) + list(self.image_dir.glob("*.png"))
        self.transform = transform or transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
        ])
        
        print(f"✅ Loaded {len(self.image_paths)} training images")
    
    def __len__(self):
        return len(self.image_paths)
    
    def __getitem__(self, idx):
        img_path = self.image_paths[idx]
        try:
            image = Image.open(img_path).convert('RGB')
            if self.transform:
                image = self.transform(image)
            return image, 0  # Dummy label
        except Exception as e:
            print(f"⚠️  Failed to load {img_path}: {e}")
            # Return black image as fallback
            return torch.zeros((3, 256, 256)), 0

class SimpleAvatarModel(nn.Module):
    """Simplified avatar feature extractor"""
    
    def __init__(self, latent_dim=512):
        super().__init__()
        
        # Feature encoder
        self.encoder = nn.Sequential(
            # 256x256 → 128x128
            nn.Conv2d(3, 64, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(64),
            nn.LeakyReLU(0.2),
            
            # 128x128 → 64x64
            nn.Conv2d(64, 128, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(128),
            nn.LeakyReLU(0.2),
            
            # 64x64 → 32x32
            nn.Conv2d(128, 256, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(256),
            nn.LeakyReLU(0.2),
            
            # 32x32 → 16x16
            nn.Conv2d(256, 512, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(512),
            nn.LeakyReLU(0.2),
            
            # 16x16 → 8x8
            nn.Conv2d(512, latent_dim, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(latent_dim),
            nn.LeakyReLU(0.2),
        )
        
        # Decoder (for reconstruction loss)
        self.decoder = nn.Sequential(
            # 8x8 → 16x16
            nn.ConvTranspose2d(latent_dim, 512, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(),
            
            # 16x16 → 32x32
            nn.ConvTranspose2d(512, 256, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            
            # 32x32 → 64x64
            nn.ConvTranspose2d(256, 128, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            
            # 64x64 → 128x128
            nn.ConvTranspose2d(128, 64, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            
            # 128x128 → 256x256
            nn.ConvTranspose2d(64, 3, kernel_size=4, stride=2, padding=1),
            nn.Tanh()
        )
    
    def forward(self, x):
        latent = self.encoder(x)
        reconstruction = self.decoder(latent)
        return latent, reconstruction

def train_avatar(epochs=5, batch_size=16, learning_rate=0.0002):
    """Train avatar model with MPS acceleration"""
    
    print("🎭 Starting Avatar Training")
    print("=" * 50)
    print()
    
    # Load dataset
    data_dir = Path("data/yael_shelbia/images")
    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        return False
    
    dataset = SimpleAvatarDataset(data_dir)
    dataloader = torch.utils.data.DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=0  # MPS works best with num_workers=0
    )
    
    # Initialize model
    model = SimpleAvatarModel().to(device)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    
    # Create output directory
    output_dir = Path("output/yael_shelbia")
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_dir = output_dir / "checkpoints"
    checkpoint_dir.mkdir(exist_ok=True)
    
    # Training loop
    print(f"🏋️  Training on {device} for {epochs} epochs...")
    print(f"   Dataset: {len(dataset)} images")
    print(f"   Batch size: {batch_size}")
    print(f"   Learning rate: {learning_rate}")
    print()
    
    for epoch in range(epochs):
        model.train()
        epoch_loss = 0.0
        
        pbar = tqdm(dataloader, desc=f"Epoch {epoch + 1}/{epochs}")
        for batch_idx, (images, _) in enumerate(pbar):
            images = images.to(device)
            
            # Forward pass
            latent, reconstruction = model(images)
            loss = criterion(reconstruction, images)
            
            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item()
            pbar.set_postfix({"loss": f"{loss.item():.4f}"})
        
        avg_loss = epoch_loss / len(dataloader)
        print(f"📊 Epoch {epoch + 1}/{epochs} - Avg Loss: {avg_loss:.4f}")
        
        # Save checkpoint
        checkpoint_path = checkpoint_dir / f"epoch_{epoch + 1}.pt"
        torch.save({
            'epoch': epoch + 1,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'loss': avg_loss,
        }, checkpoint_path)
        print(f"💾 Saved checkpoint: {checkpoint_path}")
    
    # Save final model
    final_model_path = output_dir / "avatar_model.pt"
    torch.save(model.state_dict(), final_model_path)
    
    # Save model info
    model_info = {
        "identity": "yael_shelbia",
        "training_images": len(dataset),
        "epochs": epochs,
        "device": str(device),
        "batch_size": batch_size,
        "learning_rate": learning_rate,
        "final_loss": avg_loss,
        "model_path": str(final_model_path),
        "status": "trained"
    }
    
    info_path = output_dir / "model_info.json"
    with open(info_path, 'w') as f:
        json.dump(model_info, f, indent=2)
    
    print()
    print("🎉 Training Complete!")
    print("=" * 50)
    print(f"✅ Model saved: {final_model_path}")
    print(f"✅ Info saved: {info_path}")
    print(f"✅ Checkpoints: {checkpoint_dir}")
    print()
    print("🎯 Next steps:")
    print("   1. Test inference: python3 test_avatar_inference.py")
    print("   2. Convert to Core ML: python3 convert_to_coreml.py")
    print("   3. Integrate into NeuroForgeApp")
    print()
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Train avatar on Apple Silicon")
    parser.add_argument("--epochs", type=int, default=5, help="Number of epochs")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size")
    parser.add_argument("--lr", type=float, default=0.0002, help="Learning rate")
    
    args = parser.parse_args()
    
    success = train_avatar(
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr
    )
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

