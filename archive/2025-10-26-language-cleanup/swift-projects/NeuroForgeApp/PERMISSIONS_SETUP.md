# macOS UI Testing Permissions Setup

## 🔐 Required Permissions

Before running UI tests, you need to grant macOS permissions for automation:

### 1. Accessibility Permission

**System Settings → Privacy & Security → Accessibility**

Add these applications:
- ✅ **Xcode** (for running tests from Xcode)
- ✅ **Terminal** (for CLI test execution)
- ✅ **iTerm** (if using iTerm instead of Terminal)

### 2. Automation Permission

**System Settings → Privacy & Security → Automation**

Allow:
- ✅ **Xcode** to control **System Events**

---

## 🚀 Quick Setup

### Method 1: First Run from Xcode (Recommended)
```bash
cd /Users/christianmerrill/Documents/GitHub/NeuroForgeApp
make open  # Opens Xcode
# Press ⌘U to run tests
# Accept all permission prompts when they appear
```

### Method 2: Manual Permission Grant
1. Open **System Settings**
2. Go to **Privacy & Security → Accessibility**
3. Click the **+** button
4. Add **Xcode** and **Terminal**
5. Go to **Privacy & Security → Automation**
6. Allow **Xcode** to control **System Events**

---

## ✅ Verification

After granting permissions, test with:
```bash
make xctest
```

If permissions are correct, you'll see:
- Tests run without permission dialogs
- Screenshots are captured
- UI interactions work properly

---

## 🐛 Troubleshooting

### Permission Denied Errors
- **Re-grant permissions** in System Settings
- **Restart Terminal/Xcode** after permission changes
- **Run first test from Xcode GUI** to accept prompts

### UI Not Responding
- **Check Accessibility permission** for Terminal/Xcode
- **Verify Automation permission** for System Events
- **Try running from Xcode GUI first**

### Tests Fail to Launch App
- **Confirm app builds successfully** (`make build`)
- **Check backend is running** (`make green`)
- **Verify project configuration** (XcodeGen generated correctly)

---

## 📱 Permission Status Check

You can verify permissions are working by:
1. **Running a simple test** from Xcode
2. **Checking System Settings** for enabled apps
3. **Looking for permission dialogs** during test execution

---

**Once permissions are set up, you can run UI tests from both CLI and Xcode!** 🎉
