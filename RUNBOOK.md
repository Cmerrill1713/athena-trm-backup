# 📘 Workspace Runbook

**Quick reference for common operations and troubleshooting**

---

## 🚨 Quick Fixes

### Broker Not Responding

```bash
# Check if running
lsof -i :8080

# View logs
tail -50 ~/Library/Logs/AssistantBroker.err.log

# Restart
launchctl stop com.neuroforge.assistant-broker
launchctl start com.neuroforge.assistant-broker
```

### Permission Denied Errors

1. Open **System Settings** → **Privacy & Security**
2. Find **Automation** → Add `assistant-broker`
3. Find **Accessibility** → Add `assistant-broker`
4. Restart broker

### Build Fails

```bash
# Clean and rebuild
cd ~/Documents/GitHub/assistant-broker
rm -rf .build
make build
```

### Tests Hang

```bash
# Kill stuck tests
pkill -9 -f xcodebuild
pkill -9 -f pytest

# Re-run with timeout
timeout 300 make test
```

---

## 🔧 Common Operations

### 1. Restart Broker

```bash
# Via launchctl
launchctl stop com.neuroforge.assistant-broker
launchctl start com.neuroforge.assistant-broker

# Or rebuild and reinstall
cd ~/Documents/GitHub/assistant-broker
make build
make install-agent
```

### 2. Rotate Token

```bash
cd ~/Documents/GitHub/assistant-broker

# Generate new token
NEW_TOKEN=$(make token)

# Update LaunchAgent
launchctl unload ~/Library/LaunchAgents/com.neuroforge.assistant-broker.plist
sed -i '' "s/<key>ASSISTANT_BROKER_TOKEN<\/key><string>.*<\/string>/<key>ASSISTANT_BROKER_TOKEN<\/key><string>$NEW_TOKEN<\/string>/" \
  ~/Library/LaunchAgents/com.neuroforge.assistant-broker.plist
launchctl load ~/Library/LaunchAgents/com.neuroforge.assistant-broker.plist

# Save token for your assistant
echo "$NEW_TOKEN" > ~/.assistant-broker-token
chmod 600 ~/.assistant-broker-token

echo "✅ Token rotated: $NEW_TOKEN"
```

### 3. Add Allowed Command

Edit `assistant-broker/Sources/AssistantBroker/main.swift`:

```swift
let ALLOWED_CMDS: Set<String> = ["open", "osascript", "xcrun", "xcodebuild", "YOUR_NEW_COMMAND"]
```

Then:
```bash
cd ~/Documents/GitHub/assistant-broker
make build
make install-agent  # Restarts with new binary
```

### 4. Add Allowed Directory

Edit `assistant-broker/Sources/AssistantBroker/main.swift`:

```swift
let ALLOWED_DIRS: [String] = [
    FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Desktop").path,
    FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Documents").path,
    FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("YOUR_NEW_DIR").path
]
```

Rebuild and install as above.

### 5. Full Build Pipeline (Manual)

```bash
cd ~/Documents/GitHub

# 1. Validate
./scripts/validate_gate.sh swift MyApp /path/to/project

# 2. Build
APP_PATH=$(./scripts/build_swift_app.sh MyApp /path/to/project)
echo "Built: $APP_PATH"

# 3. Package
DMG_PATH=$(./scripts/package_dmg.sh "$APP_PATH")
echo "Packaged: $DMG_PATH"

# 4. Reveal
TOKEN=$(cat ~/.assistant-broker-token)
curl -X POST http://127.0.0.1:8080/v1/run \
  -H 'Content-Type: application/json' \
  -H "X-Assistant-Token: $TOKEN" \
  -d "{\"cmd\":\"open\",\"args\":[\"$DMG_PATH\"]}"
```

### 6. Trigger Build from Chat Assistant

Your AI assistant should call:

```python
import requests

BROKER = "http://127.0.0.1:8080"
TOKEN = open("/Users/christianmerrill/.assistant-broker-token").read().strip()
HEADERS = {
    "Content-Type": "application/json",
    "X-Assistant-Token": TOKEN
}

# Build workflow
# 1. Validate
subprocess.run(["./scripts/validate_gate.sh", "swift", "MyApp", "/path"], check=True)

# 2. Build
result = subprocess.run(
    ["./scripts/build_swift_app.sh", "MyApp", "/path"],
    capture_output=True, text=True, check=True
)
app_path = result.stdout.strip().split('\n')[-1]

# 3. Package
result = subprocess.run(
    ["./scripts/package_dmg.sh", app_path],
    capture_output=True, text=True, check=True
)
dmg_path = result.stdout.strip().split('\n')[-1]

# 4. Reveal
requests.post(
    f"{BROKER}/v1/run",
    headers=HEADERS,
    json={"cmd": "open", "args": [dmg_path]}
)
```

---

## 🐛 Troubleshooting Guide

### "Bundle ID not found"

**Error:** `Bundle ID 'com.example.app' not found`

**Fix:**
```bash
# Find correct bundle ID
osascript -e 'id of app "AppName"'

# Use the exact output in your request
```

### "Command not allowed"

**Error:** `Command 'mycommand' not allowed. Allowed: open, osascript, xcrun, xcodebuild`

**Fix:** Add command to `ALLOWED_CMDS` (see above)

### "Path not allowed"

**Error:** `Path '/Users/you/Somewhere' not allowed. Allowed directories: ~/Desktop, ~/Documents`

**Fix:** Add directory to `ALLOWED_DIRS` (see above)

### "Unauthorized"

**Error:** `Missing or invalid X-Assistant-Token header`

**Fix:**
```bash
# Get token from LaunchAgent plist
grep -A1 "ASSISTANT_BROKER_TOKEN" ~/Library/LaunchAgents/com.neuroforge.assistant-broker.plist

# Or from saved file
cat ~/.assistant-broker-token

# Use in requests
curl -H "X-Assistant-Token: YOUR_TOKEN_HERE" ...
```

### Broker Won't Start

**Symptoms:** `launchctl list` doesn't show `com.neuroforge.assistant-broker`

**Diagnosis:**
```bash
# Check logs
cat ~/Library/Logs/AssistantBroker.err.log

# Try manual start
cd ~/Documents/GitHub/assistant-broker
ASSISTANT_BROKER_TOKEN=$(cat ~/.assistant-broker-token) .build/release/assistant-broker serve
```

**Common causes:**
- Binary doesn't exist → run `make build`
- Permission denied → check file permissions
- Port in use → kill process using port 8080

### Packaging Fails

**Error:** `Build failed: MyApp.app missing`

**Check:**
```bash
# Does project build in Xcode?
cd /path/to/project
xcodebuild -list  # Shows schemes

# Try manual build
xcodebuild -scheme MyApp -configuration Release

# Check for errors
```

### Tests Fail on CI

**Symptoms:** GitHub Actions fail but local tests pass

**Check:**
- macOS version mismatch (CI uses macos-14)
- Xcode version (CI uses 15.2)
- Missing dependencies
- Hardcoded paths

**Fix:** Run locally with same env:
```bash
# Match CI environment
xcode-select -p  # Should match CI
swift --version  # Should match CI

# Run tests
make validate
```

---

## 📊 Monitoring

### Check Broker Health

```bash
# Simple check
curl -s http://127.0.0.1:8080/v1/health

# With jq
curl -s http://127.0.0.1:8080/v1/health | jq .
```

### View Recent Logs

```bash
# Last 50 lines
tail -50 ~/Library/Logs/AssistantBroker.out.log

# Follow live
tail -f ~/Library/Logs/AssistantBroker.out.log

# Search for errors
grep -i error ~/Library/Logs/AssistantBroker.err.log
```

### Build Artifacts Location

```bash
# All builds organized by app and timestamp
ls -lh ~/Desktop/Builds/

# Latest build for an app
ls -lt ~/Desktop/Builds/MyApp/ | head -5
```

---

## 🔒 Security Checklist

- [ ] Token is random (32+ hex chars)
- [ ] Token not in version control
- [ ] Broker bound to `127.0.0.1` only
- [ ] Only required commands in `ALLOWED_CMDS`
- [ ] Only required dirs in `ALLOWED_DIRS`
- [ ] Logs reviewed monthly for unauthorized attempts
- [ ] LaunchAgent plist permissions: `chmod 644 ~/Library/LaunchAgents/com.neuroforge.assistant-broker.plist`

---

## 📋 Maintenance Schedule

### Weekly
- [ ] Check broker logs for errors
- [ ] Verify builds still work
- [ ] Test workspace_doctor.sh

### Monthly
- [ ] Update dependencies (`swift package update`)
- [ ] Review and clean old builds (`~/Desktop/Builds/`)
- [ ] Rotate broker token (optional)
- [ ] Review `ALLOWED_CMDS` and `ALLOWED_DIRS`

### Quarterly
- [ ] Update Vapor framework
- [ ] Review security audit logs
- [ ] Update documentation
- [ ] CI/CD health check

---

## 📞 Emergency Contacts

### Broker Down
1. Check logs (above)
2. Try manual start
3. If all fails: disable LaunchAgent, rebuild from scratch

### Security Incident
1. **Immediately:** Unload LaunchAgent
2. Rotate token
3. Review logs for unauthorized access
4. Tighten allowlists
5. Restart with new token

### Build Pipeline Broken
1. Test each script individually
2. Check for macOS/Xcode updates
3. Verify permissions
4. Review recent changes via git

---

## 🎓 Reference Links

- **Vapor Docs:** https://docs.vapor.codes/
- **Swift Package Manager:** https://www.swift.org/package-manager/
- **LaunchAgent Guide:** https://www.launchd.info/
- **macOS Permissions:** System Settings → Privacy & Security

---

**Last Updated:** October 11, 2025  
**Maintained By:** Christian Merrill  
**Version:** 2.0 (Hardened)

