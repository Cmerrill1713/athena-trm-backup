# 🚀 Athena Frontend Setup - One-Click Build & Test

**Zero-configuration setup for SwiftUI app with Athena pop-out windows**

This setup script automates the entire development environment, builds your SwiftUI app, and demonstrates the critical pop-out windows.

## 🎯 Quick Start (One Command)

Tell Cursor to run:

```bash
./setup_athena_frontend.sh
```

That's it! The script will:
- ✅ Install Xcode Command Line Tools
- ✅ Set up Homebrew and development tools
- ✅ Create Python virtual environment
- ✅ Build the SwiftUI app
- ✅ Launch app with pop-out windows enabled
- ✅ Run automated demo of all three pop-out windows

## 📦 What Gets Installed

### Development Tools
- **Xcode Command Line Tools** - Required for Swift compilation
- **Homebrew** - macOS package manager
- **SwiftLint** - Swift code quality checker
- **Python 3.11** - For demo scripts and tooling
- **fd** - Fast file finder for build artifacts

### Python Environment
- **Virtual environment** (`.venv`) - Isolated Python setup
- **Demo dependencies** - For testing pop-out windows

## 🛠️ Manual Commands (If Needed)

```bash
# Full setup
make bootstrap

# Just build
make build

# Just run (after build)
make run

# Just demo (Python script)
make demo

# Clean everything
make clean
```

## 🎨 Custom Configuration

### Different Scheme/App Name
```bash
# If your Xcode scheme isn't "NeuroForgeApp"
SCHEME="MyCustomScheme" ./setup_athena_frontend.sh

# If your app name differs
APP_NAME="MyCustomApp" ./setup_athena_frontend.sh

# Both together
SCHEME="MyScheme" APP_NAME="MyApp" ./setup_athena_frontend.sh
```

### Feature Flags
The setup automatically enables:
- `POPUPS_ENABLED=1` - Enables pop-out windows
- `AUTOEXEC_GUARD=1` - Guards emergency auto-execute in dev

## 🔍 What Happens During Setup

### Phase 1: Environment Setup
```
1) Ensure Xcode & CLT ✓
   - Checks for Command Line Tools
   - Activates Xcode.app
   - Verifies xcodebuild works

2) Homebrew + tooling ✓
   - Installs Homebrew if missing
   - Installs dev tools via Brewfile
   - Updates Homebrew packages
```

### Phase 2: Python Environment
```
3) Python venv for demo ✓
   - Creates .venv directory
   - Installs pip dependencies
   - Sets up demo script environment
```

### Phase 3: Swift Build
```
4) Resolve SwiftPM deps ✓
   - Resolves package dependencies
   - Prepares for compilation

5) Detect Xcode project ✓
   - Finds .xcodeproj or .xcworkspace
   - Validates project structure

6) Build app (Release) ✓
   - Compiles SwiftUI app
   - Links all frameworks
   - Produces .app bundle
```

### Phase 4: Launch & Demo
```
7) Launch app with dev flags ✓
   - Finds built .app file
   - Sets environment variables
   - Opens app in background

8) Trigger Athena pop-out windows demo ✓
   - Runs Python smoke test
   - Validates all three windows
   - Confirms accessibility
```

## 🎯 Expected Results

After setup completes, you should see:

### ✅ App Launches
- NeuroForge SwiftUI app opens
- Modern NavigationStack dashboard visible
- All UI elements render correctly

### ✅ Pop-out Windows Demo
```
🚀 Athena Pop-out Windows Smoke Test
==================================================
✅ Critical Alert Window: DB p95 latency breach
✅ Tribunal Decision Window: RAG CE router rollback
✅ System Emergency Window: Cluster instability detected
```

### ✅ Three Windows Appear Sequentially
1. **🚨 Critical Alert** - Red flashing header, impact assessment, action buttons
2. **⚖️ Tribunal Decision** - Case details, AI recommendation, decision options
3. **🔥 System Emergency** - Countdown timer, risk levels, escalation contacts

## 🔧 Troubleshooting

### Xcode Signing Issues
```bash
# In Xcode: Targets → Your App → Signing & Capabilities
# Check "Automatically manage signing" and select your team
```

### Can't Find .app After Build
```bash
# Find the built app
fd -t d '\.app$' build DerivedData . -H
```

### Demo Doesn't Trigger Pop-outs
```bash
# Check environment variables
echo $POPUPS_ENABLED $AUTOEXEC_GUARD

# Or launch with flags
POPUPS_ENABLED=1 AUTOEXEC_GUARD=1 open "NeuroForgeApp.app"
```

### Module Import Issues
```bash
# Clean and resolve
swift package clean && swift package resolve
```

### Permission Issues
```bash
# Xcode might need accessibility permissions
# System Settings → Privacy & Security → Accessibility
```

## 🧪 Testing & Validation

### Acceptance Checklist
Run after setup:
```bash
python3 demo_athena_popouts.py --checklist
```

### Regression Tests
```bash
python3 demo_athena_popouts.py --regression
```

### Individual Window Tests
```bash
# Test just critical alerts
python3 demo_athena_popouts.py --critical "Custom alert message"

# Test just tribunal decisions
python3 demo_athena_popouts.py --tribunal "Custom case"

# Test just system emergencies
python3 demo_athena_popouts.py --emergency "Custom emergency"
```

## 🎨 In-App Testing

### Keyboard Shortcuts
- **Cmd+Opt+Ctrl+P** - Trigger demo pop-out windows
- **Tab** - Navigate between UI elements
- **Space/Enter** - Activate buttons
- **Esc** - Close windows

### Accessibility Testing
- **Cmd+F5** - Enable VoiceOver
- **Ctrl+Opt+Cmd+8** - Toggle accessibility inspector
- Test with keyboard-only navigation

## 📊 Performance Expectations

- **Setup Time**: 5-15 minutes (depends on Homebrew installs)
- **Build Time**: 2-5 minutes (SwiftUI compilation)
- **Launch Time**: < 10 seconds
- **Demo Time**: < 30 seconds

## 🔒 Security Notes

- **Local Only**: All tools run locally on your Mac
- **No Cloud Dependencies**: No external API calls during setup
- **Isolated Environment**: Python venv prevents system pollution
- **Standard Permissions**: Only requests typical macOS development permissions

## 🚀 Production Deployment

For production builds:
```bash
# Archive for distribution
xcodebuild -project NeuroForgeApp.xcodeproj -scheme NeuroForgeApp -configuration Release -archivePath build/NeuroForgeApp.xcarchive archive

# Export .app
xcodebuild -exportArchive -archivePath build/NeuroForgeApp.xcarchive -exportPath build/ -exportOptionsPlist export-options.plist
```

## 📚 Files Created

- `setup_athena_frontend.sh` - Main automation script
- `Brewfile` - Homebrew dependencies
- `Makefile` - Convenient build commands
- `.venv/` - Python virtual environment
- `ATHENA_FRONTEND_SETUP_README.md` - This documentation

## 🎯 Success Criteria

✅ **Xcode builds successfully** (no compilation errors)  
✅ **App launches without crashing**  
✅ **All three pop-out windows appear**  
✅ **Windows have proper titles and content**  
✅ **Buttons respond to clicks**  
✅ **Demo script runs without errors**  
✅ **Accessibility features work**  

---

**Ready to build and test Athena's critical pop-out windows? Just run `./setup_athena_frontend.sh` and watch the magic happen!** 🚀✨

**Cursor will handle everything automatically - you just watch the pop-outs appear!** 🎯🪟
