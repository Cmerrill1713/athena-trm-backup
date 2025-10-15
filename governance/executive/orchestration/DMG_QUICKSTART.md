# DMG Packaging - Quick Start

**Build a signed, notarized DMG in 3 steps**

---

## 📋 **3-STEP SETUP**

### **1. Create Notary Profile (2 min)**

```bash
xcrun notarytool store-credentials "neuroforge-notary" \
  --apple-id "YOUR_APPLE_ID@email.com" \
  --team-id "YOUR_TEAM_ID" \
  --password "app-specific-password"
```

**Get app-specific password:**
- https://appleid.apple.com
- Security → App-Specific Passwords → Generate

---

### **2. Configure .env (1 min)**

```bash
cd ~/Documents/GitHub/NeuroForgeApp
cp env.template .env
nano .env  # Fill in your values
```

**Required:**
- `TEAM_ID` - From developer.apple.com
- `SIGN_IDENTITY` - From Keychain Access
- `NOTARY_PROFILE` - "neuroforge-notary" (from Step 1)

---

### **3. Build DMG (15-20 min)**

```bash
make -f Makefile.dmg dmg
```

**Steps:**
```
📦 Building... (2-3 min)
✍️  Signing...
🔍 Verifying...
📦 Zipping...
☁️  Notarizing... (5-15 min) ← Apple's servers
📎 Stapling...
💿 Creating DMG...

🎉 DMG READY: build-dmg/NeuroForgeApp.dmg
```

---

## ✅ **VERIFY**

```bash
# Test DMG
open build-dmg/NeuroForgeApp.dmg

# Drag to Applications
# Launch from Applications
# Should work with NO security warnings ✅
```

---

## 🚀 **DISTRIBUTE**

```bash
# Upload to GitHub Release
gh release create v0.9.2-dmg \
  build-dmg/NeuroForgeApp.dmg \
  --title "NeuroForge v0.9.2" \
  --notes "Signed & notarized macOS installer"
```

**Users:**
1. Download DMG
2. Double-click
3. Drag to Applications
4. Launch
5. Done! 🎉

---

## 🛠️ **QUICK COMMANDS**

```bash
# Full build
make -f Makefile.dmg dmg

# Fast build (skip notarize for testing)
make -f Makefile.dmg build sign package

# Clean and rebuild
make -f Makefile.dmg clean dmg

# Open build folder
make -f Makefile.dmg open

# Help
make -f Makefile.dmg help
```

---

## ⚡ **THAT'S IT!**

**Setup:** 5 min
**Build:** 15-20 min
**Result:** Professional DMG installer

**Next:** See `DMG_SETUP_GUIDE.md` for detailed troubleshooting.
