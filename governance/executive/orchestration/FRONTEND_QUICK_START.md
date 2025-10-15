# 🚀 NeuroForge Frontend - Quick Start Guide

## ✅ Current Status

**App is LIVE and WORKING!** PID: 71247

### Text Input Fix
- ✅ Typing works reliably
- ✅ ⌘K hotkey for refocus
- ✅ No more keyboard stealing

### E2E Testing
- ✅ Headless tests pass
- ✅ Pop-out windows working
- ✅ JSON reports generated

## 🎯 Quick Commands

### Launch the App
```bash
cd NeuroForgeApp && .build/debug/NeuroForgeApp &
```

### Build the App
```bash
cd NeuroForgeApp && swift build
```

### Run E2E Test
```bash
make frontside-e2e
```

### Trigger Pop-outs (while app is running)
```bash
open "athena://trigger?kind=critical"
open "athena://trigger?kind=tribunal"
open "athena://trigger?kind=emergency"
```

### Using the CLI Tool
```bash
bin/athenactl show-critical
bin/athenactl show-tribunal
bin/athenactl show-emergency
bin/athenactl e2e
```

## 🔑 Key Features

1. **Focus Management** - ⌘K always returns focus to chat input
2. **URL Scheme** - External triggers via `athena://` URLs
3. **E2E Mode** - Set `ATHENA_E2E=1` for headless testing
4. **Preview Stripping** - Automatic preview removal for CI
5. **Smoke Tests** - Compile-time validation

## 📍 Current Location

The app is in: `/Users/christianmerrill/Documents/GitHub/NeuroForgeApp/`

Build artifacts: `NeuroForgeApp/.build/debug/NeuroForgeApp`

## 🐛 If Text Input Stops Working

Press **⌘K** to refocus the chat input field.

The `InputFocusCoordinator` automatically suspends global key monitors while typing.

## 🎨 App Features Working

- ✅ Chat interface with `ChatComposer`
- ✅ Pop-out windows (Critical, Tribunal, Emergency)
- ✅ Athena Dashboard
- ✅ Profile management
- ✅ Voice integration hooks
- ✅ Focus coordinator

## 🔄 Next Steps

1. **Restore Dashboard Toggles** - Now that text input works
2. **Backend Integration** - Connect to Bridge API
3. **Voice Features** - Wire up voice controls
4. **CI Integration** - Add `make frontside-e2e` to GitHub Actions

## 💡 Tips

- Use `make frontside-e2e` for CI-safe testing
- Use `⌘K` if you lose focus in chat
- Check `~/athena_e2e.json` for E2E test results
- All pop-outs work via `athena://` URL scheme

**Everything is ready to go! 🎉**
