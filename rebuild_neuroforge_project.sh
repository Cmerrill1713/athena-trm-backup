#!/bin/bash
set -e

echo "🔧 Rebuilding NeuroForgeApp with fresh Xcode project..."

cd NeuroForgeApp

# Backup the corrupted project
mv NeuroForgeApp.xcodeproj NeuroForgeApp.xcodeproj.broken 2>/dev/null || true

# Create Info.plist if missing
if [ ! -f Info.plist ]; then
cat > Info.plist << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>en</string>
    <key>CFBundleExecutable</key>
    <string>$(EXECUTABLE_NAME)</string>
    <key>CFBundleIdentifier</key>
    <string>$(PRODUCT_BUNDLE_IDENTIFIER)</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>$(PRODUCT_NAME)</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSMinimumSystemVersion</key>
    <string>14.0</string>
    <key>NSHumanReadableCopyright</key>
    <string>Copyright © 2025. All rights reserved.</string>
    <key>NSPrincipalClass</key>
    <string>NSApplication</string>
</dict>
</plist>
PLIST
fi

# Use xcodebuild to create a minimal project
# We'll use swift package as the base
cd ..
cp -r AthenaPopoutDemo NeuroForgeApp_Clean
cd NeuroForgeApp_Clean

# Rename the package
sed -i.bak 's/AthenaPopoutDemo/NeuroForgeApp/g' Package.swift
rm -f Package.swift.bak

# Generate Xcode project  
swift package generate-xcodeproj 2>/dev/null || \
  (echo "⚠️  generate-xcodeproj deprecated, using 'open Package.swift' instead" && \
   echo "✅ Use: open Package.swift in Xcode")

echo ""
echo "✅ Clean NeuroForgeApp ready!"
echo ""
echo "📂 Location: NeuroForgeApp_Clean/"
echo ""
echo "Next steps:"
echo "  cd ../NeuroForgeApp_Clean"
echo "  open Package.swift  # Opens in Xcode"
echo "  # Or build via CLI:"
echo "  swift build"
echo "  swift run"
