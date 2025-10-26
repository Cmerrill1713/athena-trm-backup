# NeuroForge App Icon Assets

This directory contains the complete macOS-compliant icon setup for NeuroForge.

## 📁 Files

### Generated Icons
- `NeuroForgeIcon.icns` - Complete macOS icon bundle
- `NeuroForgeIcon.iconset/` - Individual PNG files for all sizes

### Required macOS Sizes
```
icon_16x16.png          (16×16)
icon_16x16@2x.png       (32×32)
icon_32x32.png          (32×32)
icon_32x32@2x.png       (64×64)
icon_128x128.png        (128×128)
icon_128x128@2x.png     (256×256)
icon_256x256.png        (256×256)
icon_256x256@2x.png     (512×512)
icon_512x512.png        (512×512)
icon_512x512@2x.png     (1024×1024)
```

## 🎨 Icon Design

The NeuroForge icon features:
- **Glowing red neural network head silhouette**
- **Circuitry/neural pathways inside the head**
- **Transparent background**
- **High contrast for visibility at all sizes**
- **macOS-compliant design**

## 🔧 Usage

### In Swift Package
The icon is automatically included via `Package.swift`:
```swift
resources: [.process("Assets")]
```

### In Xcode Project
1. Open `Assets/NeuroForgeIcon.iconset/`
2. Drag all PNG files to Xcode's AppIcon.appiconset
3. Or use the `NeuroForgeIcon.icns` file directly

### Programmatic Access
```swift
// Set icon programmatically
AppIcon.setIcon()
```

## 🚀 Generation

To regenerate icons:
```bash
python3 Assets/generate_icon.py
```

This will:
1. Create all required PNG sizes
2. Generate the .iconset directory
3. Convert to .icns format
4. Update all files

## ✅ macOS Compliance

✅ **All required sizes included**
✅ **Transparent background**
✅ **Square format (macOS adds rounded corners)**
✅ **High resolution for Retina displays**
✅ **Proper .icns format**
✅ **Info.plist configuration**

## 📱 Where Icons Appear

- **Dock** - Main application icon
- **Launchpad** - App grid
- **App Switcher** (⌘+Tab) - Application switcher
- **Finder** - File previews and sidebar
- **Spotlight** - Search results
- **Mission Control** - App thumbnails

---

**Generated:** October 12, 2025
**Design:** Glowing neural network head
**Format:** .icns + .iconset
**Status:** Production Ready ✅
