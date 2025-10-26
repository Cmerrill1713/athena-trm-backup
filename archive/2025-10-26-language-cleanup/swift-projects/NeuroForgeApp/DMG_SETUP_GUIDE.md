# NeuroForge DMG Packaging - Setup Guide

**Purpose**: Create signed, notarized DMG installer for NeuroForge
**Time**: 5 min setup + 15-20 min first build
**Result**: Professional `.dmg` file anyone can install

---

## 🎯 **WHAT YOU'LL GET**

A production-ready `.dmg` installer with:
- ✅ **Codesigned** - Signed with your Developer ID
- ✅ **Notarized** - Approved by Apple
- ✅ **Stapled** - Ticket embedded (works offline)
- ✅ **Drag-install** - Users drag to Applications
- ✅ **Gatekeeper Pass** - No security warnings

**Result:** `NeuroForgeApp.dmg` → Double-click → Drag to Applications → Done!

---

## ⚙️ **ONE-TIME SETUP (5 minutes)**

### **Step 1: Check Certificates**

```bash
# Open Keychain Access
open -a "Keychain Access"

# Look for:
# ✅ "Developer ID Application: Your Name (TEAMID)"
# ✅ "Apple Worldwide Developer Relations Certification Authority"
```

**If missing:**
1. Go to: https://developer.apple.com/account/resources/certificates
2. Create "Developer ID Application" certificate
3. Download and install in Keychain

---

### **Step 2: Create Notary Profile**

```bash
# Store Apple ID credentials securely
xcrun notarytool store-credentials "neuroforge-notary" \
  --apple-id "YOUR_APPLE_ID_EMAIL" \
  --team-id "YOUR_TEAM_ID" \
  --password "APP_SPECIFIC_PASSWORD"
```

**To get app-specific password:**
1. Go to: https://appleid.apple.com
2. Sign In → Security → App-Specific Passwords
3. Generate new password
4. Use it in command above

---

### **Step 3: Configure Environment**

```bash
cd ~/Documents/GitHub/NeuroForgeApp

# Copy template
cp .env.template .env

# Edit .env with your values
nano .env  # or your preferred editor
```

**Required values:**
```bash
TEAM_ID="YOUR_TEAM_ID"                    # From developer.apple.com
BUNDLE_ID="com.neuroforge.app"            # Must match Info.plist
APP_SCHEME="NeuroForgeApp"                # Xcode scheme name
APP_NAME="NeuroForgeApp"                  # App bundle name
SIGN_IDENTITY="Developer ID Application: Your Name (TEAM_ID)"
NOTARY_PROFILE="neuroforge-notary"        # Name from Step 2
```

**Find your Team ID:**
```bash
# Method 1: Developer website
open https://developer.apple.com/account/#!/membership

# Method 2: From certificate
security find-identity -v -p codesigning | grep "Developer ID Application"
```

---

### **Step 4: Verify Setup**

```bash
# Check certificate
security find-identity -v -p codesigning

# Should show:
# 1) ABC123... "Developer ID Application: Your Name (TEAMID)"

# Check notary profile
xcrun notarytool history --keychain-profile "neuroforge-notary"

# Should connect without errors
```

---

## 🚀 **BUILD DMG (ONE COMMAND)**

After setup is complete:

```bash
cd ~/Documents/GitHub/NeuroForgeApp
make -f Makefile.dmg dmg
```

**What happens:**
```
📦 Building NeuroForgeApp for Release...
🔨 Archiving... (2-3 min)
📤 Exporting...
✍️  Signing app...
🔍 Verifying signature...
📦 Zipping for notary...
☁️  Submitting to Apple notary service... (5-15 min)
📎 Stapling notarization ticket...
💿 Creating DMG installer...

🎉 DMG BUILD COMPLETE!
📦 build-dmg/NeuroForgeApp.dmg
```

**Total time:** 15-20 minutes (mostly Apple notary wait)

---

## ✅ **VERIFY DMG**

```bash
# Open build directory
make -f Makefile.dmg open

# Test DMG
open build-dmg/NeuroForgeApp.dmg
# Drag NeuroForgeApp to Applications
# Launch from Applications folder

# Should:
# ✅ No security warning
# ✅ App launches immediately
# ✅ All features work
```

---

## 🧪 **QUICK TARGETS**

### **Build Only (No Notarize):**
```bash
make -f Makefile.dmg build sign package
# Fast local test DMG (not notarized)
```

### **Re-Sign Existing Build:**
```bash
make -f Makefile.dmg sign verify
```

### **Re-Notarize:**
```bash
make -f Makefile.dmg notarize staple
```

### **Clean Start:**
```bash
make -f Makefile.dmg clean
make -f Makefile.dmg dmg
```

---

## 🛠️ **TROUBLESHOOTING**

### **"User interaction is not allowed"**
```
Fix: Use app-specific password, not regular Apple ID password
Create at: https://appleid.apple.com → Security → App-Specific Passwords
```

### **"No identity found"**
```bash
# Check available identities
security find-identity -v -p codesigning

# If none, create certificate at:
# developer.apple.com → Certificates → Create "Developer ID Application"
```

### **"Invalid entitlements"**
```
Fix: Verify entitlements.plist exists and is valid
Check: xmllint --noout entitlements.plist
```

### **"Export failed"**
```
Fix: Check TEAM_ID matches certificate
Verify: security find-identity -v | grep "$(TEAM_ID)"
```

### **"Notarization failed"**
```bash
# Check notary log
xcrun notarytool log <submission-id> \
  --keychain-profile "$(NOTARY_PROFILE)"

# Common issues:
# - Unsigned binaries (run: make -f Makefile.dmg sign)
# - Invalid entitlements (check entitlements.plist)
# - Missing hardened runtime (automatic with --options runtime)
```

### **"Staple failed"**
```
Cause: Notarization not complete
Fix: Wait for notarization to finish, then retry:
      make -f Makefile.dmg staple
```

---

## 📦 **DISTRIBUTION**

### **Upload to GitHub Release:**
```bash
# Tag release
git tag v0.9.2-dmg
git push --tags

# Upload DMG
gh release create v0.9.2-dmg \
  build-dmg/NeuroForgeApp.dmg \
  --title "NeuroForge v0.9.2" \
  --notes "Signed and notarized DMG installer"
```

### **Share Directly:**
```
Users can:
1. Download NeuroForgeApp.dmg
2. Double-click to mount
3. Drag NeuroForgeApp to Applications
4. Launch from Applications folder
5. No Terminal, no security warnings!
```

---

## 🔄 **SPARKLE AUTO-UPDATES (NEXT)**

After DMG is working, add auto-updates:
1. Add Sparkle framework
2. Generate appcast
3. Host on GitHub Pages
4. Users get automatic updates

**Let me know when you want to add this!**

---

## ✅ **CHECKLIST**

Setup (one-time):
- [ ] Developer ID Application certificate in Keychain
- [ ] Notary profile created (`xcrun notarytool store-credentials`)
- [ ] `.env` file configured with Team ID, signing identity
- [ ] `entitlements.plist` exists

Build:
- [ ] `make -f Makefile.dmg dmg` completes successfully
- [ ] DMG appears in `build-dmg/`
- [ ] Opens without security warnings
- [ ] App launches and works

Ship:
- [ ] Upload to GitHub Release
- [ ] Test download and install
- [ ] Distribute to users

---

## 🎯 **QUICK REFERENCE**

```bash
# Full build
make -f Makefile.dmg dmg

# Fast build (no notarize)
make -f Makefile.dmg build sign package

# Clean and rebuild
make -f Makefile.dmg clean dmg

# Open build directory
make -f Makefile.dmg open

# Verify signatures
make -f Makefile.dmg verify
```

---

## 📚 **NEXT STEPS**

After first successful DMG:
1. ✅ Test installation on clean Mac
2. ✅ Upload to GitHub Release
3. ✅ (Optional) Add Sparkle auto-updates
4. ✅ (Optional) Create installer customization
5. ✅ Ship to main and tag v0.9.2-green

---

**SETUP GUIDE COMPLETE** ✅
**Next**: Configure `.env` and run `make -f Makefile.dmg dmg`! 🚀
