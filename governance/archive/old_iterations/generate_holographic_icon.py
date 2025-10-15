#!/usr/bin/env python3
"""
Generate NeuroForge holographic app icon in all required macOS sizes.
Creates a red/orange/dark-blue/white holographic face design.
"""

import os
import json
from PIL import Image, ImageDraw
import math

def create_holographic_icon(size):
    """Create the NeuroForge holographic face icon at specified size"""
    # Create transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Calculate scaling factors
    scale = size / 1024.0
    center = size // 2

    # Define face shape points (front-facing, slightly left profile)
    face_points = []

    # Define face shape (front-facing with slight angle)
    base_points = [
        (180, 140),   # top left
        (220, 120),   # top center-left
        (280, 110),   # top center
        (340, 120),   # top center-right
        (380, 140),   # top right
        (400, 180),   # right temple
        (410, 240),   # right cheek
        (400, 300),   # right jaw
        (380, 340),   # right neck
        (350, 370),   # right shoulder
        (300, 380),   # center neck
        (250, 370),   # left shoulder
        (220, 340),   # left neck
        (200, 300),   # left jaw
        (190, 240),   # left cheek
        (180, 180),   # left temple
    ]

    # Scale and center the points
    for x, y in base_points:
        face_points.append((
            int(center + (x - 256) * scale),
            int(center + (y - 256) * scale)
        ))

    # Create holographic gradient effect
    def holographic_gradient(x, y, base_color, intensity=1.0):
        # Create holographic shimmer effect
        shimmer = math.sin(x * 0.02 + y * 0.015) * 0.3 + 0.7
        ripple = math.sin((x * x + y * y) * 0.001) * 0.2 + 0.8

        # Base holographic colors: red/orange/dark-blue/white
        r, g, b = base_color

        # Apply holographic effects
        r = int(r * shimmer * ripple * intensity)
        g = int(g * shimmer * ripple * intensity)
        b = int(b * shimmer * ripple * intensity)

        # Add color shifting based on position
        hue_shift = math.sin(x * 0.01) * 30
        if hue_shift > 0:
            r = min(255, r + int(hue_shift * 2))
            b = max(0, b - int(hue_shift))
        else:
            r = max(0, r + int(hue_shift))
            b = min(255, b - int(hue_shift * 2))

        return (r, g, b, 255)

    # Draw holographic face outline with gradient
    outline_width = max(2, int(8 * scale))

    # Create holographic glow effect
    for i in range(outline_width * 3, 0, -1):
        alpha = int(80 * (outline_width * 3 - i) / (outline_width * 3))
        for j, (x, y) in enumerate(face_points):
            next_point = face_points[(j + 1) % len(face_points)]

            # Holographic color gradient
            base_colors = [
                (255, 100, 100),  # Red
                (255, 150, 50),   # Orange
                (50, 100, 255),   # Dark blue
                (255, 255, 255),  # White
            ]

            color_idx = int((j / len(face_points)) * len(base_colors))
            base_color = base_colors[color_idx]
            holographic_color = holographic_gradient(x, y, base_color, alpha/255.0)

            # Draw gradient line segment
            draw.line([x, y, next_point[0], next_point[1]],
                     fill=holographic_color, width=i)

    # Fill face with holographic pattern
    if size >= 64:  # Only draw detail on larger icons
        # Create holographic fill pattern
        fill_points = []
        for x, y in face_points:
            # Create inner face outline (slightly smaller)
            inner_x = x + (center - x) * 0.1
            inner_y = y + (center - y) * 0.1
            fill_points.append((int(inner_x), int(inner_y)))

        # Draw holographic face fill
        for y in range(size):
            for x in range(size):
                # Check if point is inside face
                if is_point_in_polygon(x, y, fill_points):
                    # Create holographic pixel
                    distance = math.sqrt((x - center)**2 + (y - center)**2)
                    intensity = 1.0 - (distance / (size * 0.4))
                    intensity = max(0.1, intensity)

                    # Choose holographic color based on position
                    color_phase = (x + y) * 0.01
                    if color_phase % 4 < 1:
                        base_color = (255, 100, 100)  # Red
                    elif color_phase % 4 < 2:
                        base_color = (255, 150, 50)   # Orange
                    elif color_phase % 4 < 3:
                        base_color = (50, 100, 255)   # Dark blue
                    else:
                        base_color = (255, 255, 255)  # White

                    holographic_color = holographic_gradient(x, y, base_color, intensity)

                    # Apply some transparency for holographic effect
                    holographic_color = (holographic_color[0], holographic_color[1],
                                       holographic_color[2], int(180 * intensity))

                    img.putpixel((x, y), holographic_color)

    # Add holographic neural network overlay for larger icons
    if size >= 128:
        # Neural network pattern overlay
        nodes = [
            (center + int(30 * scale), center - int(20 * scale)),  # forehead
            (center - int(20 * scale), center - int(10 * scale)),  # temple
            (center + int(20 * scale), center + int(30 * scale)),  # cheek
            (center - int(30 * scale), center + int(20 * scale)),  # jaw
        ]

        node_size = max(2, int(8 * scale))
        line_width = max(1, int(4 * scale))

        # Draw holographic neural connections
        for i, node1 in enumerate(nodes):
            for j, node2 in enumerate(nodes[i+1:], i+1):
                if abs(i - j) <= 2:
                    # Holographic connection line
                    for k in range(line_width):
                        alpha = int(150 * (line_width - k) / line_width)
                        color_shift = (i + j) * 0.5

                        if color_shift % 4 < 1:
                            base_color = (255, 100, 100)  # Red
                        elif color_shift % 4 < 2:
                            base_color = (255, 150, 50)   # Orange
                        elif color_shift % 4 < 3:
                            base_color = (50, 100, 255)   # Dark blue
                        else:
                            base_color = (255, 255, 255)  # White

                        holographic_color = (base_color[0], base_color[1], base_color[2], alpha)
                        draw.line([node1, node2], fill=holographic_color, width=k+1)

        # Draw holographic neural nodes
        for i, node in enumerate(nodes):
            node_size = max(2, int(8 * scale))

            # Node glow effect
            for r in range(node_size * 3, 0, -1):
                alpha = int(120 * (node_size * 3 - r) / (node_size * 3))
                color_shift = i * 0.5

                if color_shift % 4 < 1:
                    base_color = (255, 100, 100)  # Red
                elif color_shift % 4 < 2:
                    base_color = (255, 150, 50)   # Orange
                elif color_shift % 4 < 3:
                    base_color = (50, 100, 255)   # Dark blue
                else:
                    base_color = (255, 255, 255)  # White

                holographic_color = (base_color[0], base_color[1], base_color[2], alpha)
                draw.ellipse([node[0] - r, node[1] - r, node[0] + r, node[1] + r],
                           fill=holographic_color)

    return img

def is_point_in_polygon(x, y, polygon):
    """Check if point is inside polygon"""
    n = len(polygon)
    inside = False

    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside

def generate_appiconset():
    """Generate complete AppIcon.appiconset for Xcode"""
    iconset_dir = "/Users/christianmerrill/Documents/GitHub/NeuroForgeApp/Resources/Assets.xcassets/AppIcon.appiconset"
    os.makedirs(iconset_dir, exist_ok=True)

    print("🎨 Generating NeuroForge holographic icon set...")

    # macOS app icon sizes
    sizes = [
        (16, "icon_16x16.png", "mac"),
        (32, "icon_16x16@2x.png", "mac"),
        (32, "icon_32x32.png", "mac"),
        (64, "icon_32x32@2x.png", "mac"),
        (128, "icon_128x128.png", "mac"),
        (256, "icon_128x128@2x.png", "mac"),
        (256, "icon_256x256.png", "mac"),
        (512, "icon_256x256@2x.png", "mac"),
        (512, "icon_512x512.png", "mac"),
        (1024, "icon_512x512@2x.png", "mac"),
    ]

    # Generate all icon files
    for size, filename, idiom in sizes:
        print(f"  Creating {filename} ({size}x{size})...")
        icon = create_holographic_icon(size)
        icon.save(os.path.join(iconset_dir, filename), "PNG")

    # Create Contents.json for Xcode
    contents = {
        "images": [
            {
                "filename": "icon_16x16.png",
                "idiom": "mac",
                "scale": "1x",
                "size": "16x16"
            },
            {
                "filename": "icon_16x16@2x.png",
                "idiom": "mac",
                "scale": "2x",
                "size": "16x16"
            },
            {
                "filename": "icon_32x32.png",
                "idiom": "mac",
                "scale": "1x",
                "size": "32x32"
            },
            {
                "filename": "icon_32x32@2x.png",
                "idiom": "mac",
                "scale": "2x",
                "size": "32x32"
            },
            {
                "filename": "icon_128x128.png",
                "idiom": "mac",
                "scale": "1x",
                "size": "128x128"
            },
            {
                "filename": "icon_128x128@2x.png",
                "idiom": "mac",
                "scale": "2x",
                "size": "128x128"
            },
            {
                "filename": "icon_256x256.png",
                "idiom": "mac",
                "scale": "1x",
                "size": "256x256"
            },
            {
                "filename": "icon_256x256@2x.png",
                "idiom": "mac",
                "scale": "2x",
                "size": "256x256"
            },
            {
                "filename": "icon_512x512.png",
                "idiom": "mac",
                "scale": "1x",
                "size": "512x512"
            },
            {
                "filename": "icon_512x512@2x.png",
                "idiom": "mac",
                "scale": "2x",
                "size": "512x512"
            }
        ],
        "info": {
            "author": "NeuroForge",
            "version": 1
        }
    }

    with open(os.path.join(iconset_dir, "Contents.json"), 'w') as f:
        json.dump(contents, f, indent=2)

    print(f"✅ Generated complete AppIcon.appiconset in {iconset_dir}")
    return iconset_dir

if __name__ == "__main__":
    print("🚀 NeuroForge Holographic Icon Generator")
    print("=" * 50)

    # Generate complete appiconset
    iconset_dir = generate_appiconset()

    print("\n🎉 Holographic icon generation complete!")
    print(f"📁 AppIcon.appiconset: {iconset_dir}")
    print("\nNext steps:")
    print("1. The AppIcon.appiconset is ready for Xcode")
    print("2. Update Package.swift to include Resources")
    print("3. Update Info.plist with CFBundleIconName")
    print("4. Run: swift build && swift run")
