#!/usr/bin/env python3
"""
Generate NeuroForge app icon in all required macOS sizes.
Creates a glowing red neural network head icon programmatically.
"""

import os
from PIL import Image, ImageDraw

def create_neural_icon(size):
    """Create the NeuroForge neural network head icon at specified size"""
    # Create transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Calculate scaling factors
    scale = size / 1024.0
    center = size // 2

    # Head outline (left-facing profile)
    head_points = []

    # Define head shape points (scaled)
    base_points = [
        (150, 200),   # back of head
        (200, 180),   # top back
        (280, 160),   # top
        (350, 180),   # forehead
        (380, 220),   # nose
        (390, 280),   # mouth
        (380, 340),   # chin
        (350, 380),   # neck
        (300, 400),   # neck bottom
        (250, 420),   # back neck
        (200, 400),   # back bottom
        (180, 380),   # back
        (160, 350),   # back mid
        (140, 300),   # back upper
        (130, 250),   # back top
    ]

    # Scale and center the points
    for x, y in base_points:
        head_points.append((
            int(center + (x - 256) * scale),
            int(center + (y - 256) * scale)
        ))

    # Draw head outline with glowing effect
    outline_width = max(2, int(8 * scale))

    # Outer glow
    for i in range(outline_width * 2, 0, -1):
        alpha = int(50 * (outline_width * 2 - i) / (outline_width * 2))
        color = (255, 80, 80, alpha)
        draw.polygon(head_points, outline=color, width=i)

    # Main head fill
    draw.polygon(head_points, fill=(200, 40, 40, 255))

    # Inner circuitry/neural network
    if size >= 64:  # Only draw detail on larger icons
        # Neural nodes and connections
        nodes = [
            (center + int(50 * scale), center - int(30 * scale)),  # forehead node
            (center + int(20 * scale), center - int(10 * scale)),  # top node
            (center - int(20 * scale), center + int(20 * scale)),  # back node
            (center + int(30 * scale), center + int(40 * scale)),  # lower node
        ]

        node_size = max(1, int(6 * scale))
        line_width = max(1, int(3 * scale))

        # Draw connections
        for i, node1 in enumerate(nodes):
            for j, node2 in enumerate(nodes[i+1:], i+1):
                if abs(i - j) <= 2:  # Connect nearby nodes
                    draw.line([node1, node2], fill=(255, 120, 120, 200), width=line_width)

        # Draw nodes
        for node in nodes:
            # Node glow
            for r in range(node_size * 2, 0, -1):
                alpha = int(100 * (node_size * 2 - r) / (node_size * 2))
                color = (255, 150, 100, alpha)
                draw.ellipse([node[0] - r, node[1] - r, node[0] + r, node[1] + r], fill=color)

            # Main node
            draw.ellipse([node[0] - node_size, node[1] - node_size,
                         node[0] + node_size, node[1] + node_size],
                        fill=(255, 180, 120, 255))

    return img

def generate_all_sizes():
    """Generate all required macOS icon sizes"""
    sizes = [
        (16, "icon_16x16.png"),
        (32, "icon_16x16@2x.png"),
        (32, "icon_32x32.png"),
        (64, "icon_32x32@2x.png"),
        (128, "icon_128x128.png"),
        (256, "icon_128x128@2x.png"),
        (256, "icon_256x256.png"),
        (512, "icon_256x256@2x.png"),
        (512, "icon_512x512.png"),
        (1024, "icon_512x512@2x.png"),
    ]

    iconset_dir = "/Users/christianmerrill/Documents/GitHub/NeuroForgeApp/Assets/NeuroForgeIcon.iconset"
    os.makedirs(iconset_dir, exist_ok=True)

    print("🎨 Generating NeuroForge icon sizes...")

    for size, filename in sizes:
        print(f"  Creating {filename} ({size}x{size})...")
        icon = create_neural_icon(size)
        icon.save(os.path.join(iconset_dir, filename), "PNG")

    print(f"✅ Generated {len(sizes)} icon sizes in {iconset_dir}")
    return iconset_dir

def create_icns_file(iconset_dir):
    """Convert iconset to .icns file"""
    icns_path = "/Users/christianmerrill/Documents/GitHub/NeuroForgeApp/Assets/NeuroForgeIcon.icns"

    print("🔧 Converting to .icns format...")
    os.system(f"iconutil -c icns '{iconset_dir}' -o '{icns_path}'")

    if os.path.exists(icns_path):
        print(f"✅ Created {icns_path}")
        return icns_path
    else:
        print("❌ Failed to create .icns file")
        return None

if __name__ == "__main__":
    print("🚀 NeuroForge Icon Generator")
    print("=" * 50)

    # Generate all sizes
    iconset_dir = generate_all_sizes()

    # Create .icns file
    icns_path = create_icns_file(iconset_dir)

    print("\n🎉 Icon generation complete!")
    print(f"📁 Iconset: {iconset_dir}")
    print(f"📄 .icns file: {icns_path}")
    print("\nNext steps:")
    print("1. The iconset is ready for Xcode Assets.xcassets")
    print("2. The .icns file can be used directly in Swift Package")
    print("3. Run: swift build && swift run")
