# 🚀 BUILD DMG NOW - Pre-Flight Checklist

**Ready to build your first production DMG!**
**Time**: 20 minutes (5 min setup + 15 min build)
**Result**: Professional signed & notarized installer

---

## ✅ **PRE-FLIGHT (5 MINUTES)**

### **Step 1: Find Your Signing Identity (30s)**

```bash
security find-identity -p codesigning
```

**Look for:**
```
1) ABC123DEF456... "Developer ID Application: Your Name (TEAM123)"
   Valid identities only
```

**Copy the full identity name:** `Developer ID Application: Your Name (TEAM123)`

---

### **Step 2: Get Team ID (30s)**

**Method 1: From identity above**
```
The part in parentheses: (TEAM123) → Your Team ID is TEAM123
```

**Method 2: Developer website**
```
Open: https://developer.apple.com/account/#!/membership
Look for: Team ID: XXXXXXXXXX
```

---

### **Step 3: Get App-Specific Password (2 min)**

1. Go to: https://appleid.apple.com
2. Sign In
3. Security → App-Specific Passwords
4. Click "Generate Password"
5. Label: "NeuroForge Notary"
6. Copy the password (xxxx-xxxx-xxxx-xxxx)

---

### **Step 4: Create Notary Profile (1 min)**

```bash
xcrun notarytool store-credentials "neuroforge-notary" \
  --apple-id "YOUR_APPLE_ID@email.com" \
  --team-id "YOUR_TEAM_ID" \
  --password "xxxx-xxxx-xxxx-xxxx"
```

**Expected:**
```
Credentials saved to Keychain.
To use them, specify `--keychain-profile "neuroforge-notary"`
```

---

### **Step 5: Configure .env (1 min)**

```bash
cd ~/Documents/GitHub/NeuroForgeApp
cp env.template .env
nano .env  # or: open .env
```

**Fill in (use YOUR values):**
```bash
TEAM_ID=ABC123DEF456
BUNDLE_ID=com.neuroforge.app
APP_SCHEME=NeuroForgeApp
APP_NAME=NeuroForgeApp
SIGN_IDENTITY="Developer ID Application: Your Name (ABC123DEF456)"
NOTARY_PROFILE=neuroforge-notary
```

**Save and close**

---

## 🚀 **LAUNCH SEQUENCE**

### **Build DMG (ONE COMMAND):**

```bash
cd ~/Documents/GitHub/NeuroForgeApp
make -f Makefile.dmg dmg
```

---

## 📊 **WHAT YOU'LL SEE (15-20 min)**

```
📦 Building NeuroForgeApp for Release...
🔨 Archiving... (2-3 min)
   [xcodebuild output]
   ✅ Built: build-dmg/export/NeuroForgeApp.app

✍️  Signing NeuroForgeApp.app with: Developer ID Application...
   ✅ Signed successfully

🔍 Verifying signature...
   ✅ Verification passed

📦 Zipping for notary submission...
   ✅ Zipped: build-dmg/NeuroForgeApp.zip

☁️  Submitting to Apple notary service...
   (This can take 5-15 minutes)
   [Progress updates from Apple]
   ✅ Notarization complete

📎 Stapling notarization ticket...
   ✅ Ticket stapled

💿 Creating DMG installer...
   ✅ DMG created: build-dmg/NeuroForgeApp.dmg

🎉 ==========================================
🎉  DMG BUILD COMPLETE!
🎉 ==========================================

📦 Signed, notarized, and stapled DMG ready:
   build-dmg/NeuroForgeApp.dmg

✅ Verification:
   ✅ Signature valid

🚀 Next steps:
   1. Test: open build-dmg/NeuroForgeApp.dmg
   2. Distribute: upload to GitHub Release
   3. Users: double-click DMG, drag to Applications
```

---

## 🧪 **TEST YOUR DMG**

```bash
# Open the DMG
open build-dmg/NeuroForgeApp.dmg

# Window appears with:
# - NeuroForgeApp.app icon
# - Applications folder shortcut
# - Background (if customized)

# Drag NeuroForgeApp to Applications
# Launch from Applications folder
# Should launch with NO security warnings ✅
```

**Verify Features:**
- ⌘⌥I - Provider Inspector
- ⌘⇧T - Prompt Sidebar
- Type "ping" - Get response
- All features work!

---

## 🛠️ **IF ANYTHING FAILS**

### **"No identity found"**
```bash
# Check certificates in Keychain
open -a "Keychain Access"

# Look for: "Developer ID Application: ..."
# If missing: developer.apple.com → Certificates → Create
```

### **"User interaction is not allowed"**
```
Cause: Wrong password or notary profile not found
Fix: Re-run notarytool store-credentials with correct app-specific password
```

### **"Invalid entitlements"**
```bash
# Verify plist is valid
xmllint --noout entitlements.plist

# Should output nothing (means valid)
```

### **"Notarization failed"**
```bash
# Get detailed log
xcrun notarytool log <RequestID> \
  --keychain-profile "neuroforge-notary"

# Common issues:
# - Unsigned binaries → Re-run: make -f Makefile.dmg sign
# - Wrong bundle ID → Check Info.plist matches .env
```

---

## 📦 **AFTER SUCCESSFUL BUILD**

### **1. Test Installation:**
```bash
# On your Mac
open build-dmg/NeuroForgeApp.dmg
# Install and verify

# (Optional) Test on clean Mac or VM
```

### **2. Upload to GitHub:**
```bash
# Tag release
git tag v0.9.2-dmg1
git push --tags

# Upload DMG
gh release create v0.9.2-dmg1 \
  build-dmg/NeuroForgeApp.dmg \
  --title "NeuroForge v0.9.2 - macOS Installer" \
  --notes "Professional signed & notarized DMG installer.

Installation:
1. Download NeuroForgeApp.dmg
2. Double-click to mount
3. Drag NeuroForgeApp to Applications
4. Launch and enjoy!

Features:
- Provider Inspector (⌘⌥I)
- Prompt Sidebar (⌘⇧T)
- Vision + RAG integration
- Model-agnostic routing
- Health monitoring"
```

### **3. Share:**
```
Send users the GitHub Release link
They download, double-click, drag, done!
No Terminal required ✅
No security warnings ✅
```

---

## 🔥 **READY TO GO?**

### **Your Checklist:**
- [ ] Have Developer ID Application certificate
- [ ] Created notary profile (`xcrun notarytool store-credentials`)
- [ ] Configured `.env` file
- [ ] Ready to run `make -f Makefile.dmg dmg`

### **Expected Timeline:**
```
Setup:       5 min
Build:       2-3 min
Notarize:    5-15 min (Apple's servers)
Package:     1 min
Total:       15-20 min
```

---

## 🎯 **THE COMMAND**

```bash
cd ~/Documents/GitHub/NeuroForgeApp

# Setup (if not done)
cp env.template .env
# Edit .env with your values

# Light the fuse! 🔥
make -f Makefile.dmg dmg
```

---

## ✨ **AFTER BUILD**

You'll have:
- ✅ Professional DMG installer
- ✅ Signed with your Developer ID
- ✅ Notarized by Apple
- ✅ No security warnings
- ✅ Drag-to-install UX
- ✅ Ready to distribute

**Users just:** Download → Double-click → Drag → Launch → Done!

---

**READY TO BUILD** 🚀
**Command**: `make -f Makefile.dmg dmg`
**Time**: 20 minutes
**Result**: Professional installer ✅
