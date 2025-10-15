# 🤖 Assistant Broker

**Local macOS HTTP API for AI-driven app control**

A secure, lightweight Swift/Vapor service that lets your AI assistant safely control macOS applications, run whitelisted commands, and manage files—all through a simple HTTP API.

---

## 🎯 What It Does

- ✅ **Open/Quit Apps** - Launch and close applications by bundle ID
- ✅ **Run Commands** - Execute whitelisted shell commands
- ✅ **File I/O** - Read/write files in allowed directories (Desktop, Documents)
- ✅ **Auto-Start** - LaunchAgent keeps it running at login
- ✅ **Secure by Default** - Whitelisted commands and path restrictions

---

## 🚀 Quick Start

### 1. Build the Broker

```bash
cd ~/Documents/GitHub/assistant-broker
make build
```

### 2. Run Locally (Development)

```bash
make run
# Broker starts on http://127.0.0.1:8080
```

### 3. Install as LaunchAgent (Auto-Start)

```bash
make install-agent
# Now runs automatically at login
```

### 4. Test It

```bash
make test
# Opens and closes TextEdit to verify
```

---

## 📡 API Reference

### Base URL

```
http://127.0.0.1:8080
```

### Endpoints

#### Health Check
```bash
GET /v1/health
```

**Response:**
```json
{"status": "ok"}
```

---

#### Open App
```bash
POST /v1/open_app
Content-Type: application/json

{"bundle_id": "com.apple.TextEdit"}
```

**Response:**
```json
{"ok": "true"}
```

**Common Bundle IDs:**
- `com.apple.TextEdit`
- `com.apple.calculator`
- `com.apple.Safari`
- `com.apple.finder`
- Find more: `osascript -e 'id of app "AppName"'`

---

#### Quit App
```bash
POST /v1/quit_app
Content-Type: application/json

{"bundle_id": "com.apple.TextEdit", "force": false}
```

**Parameters:**
- `bundle_id` (required): App bundle identifier
- `force` (optional): Force quit if `true`

**Response:**
```json
{"ok": "true"}
```

---

#### Run Command
```bash
POST /v1/run
Content-Type: application/json

{"cmd": "open", "args": ["/path/to/file.txt"]}
```

**Allowed Commands:**
- `open` - Open files/directories
- `osascript` - Run AppleScript
- `xcrun` - Xcode tools
- `xcodebuild` - Build Xcode projects

**Response:**
```json
{"ok": "true", "out": "command output"}
```

---

#### Write File
```bash
POST /v1/write_file
Content-Type: application/json

{
  "path": "/Users/christianmerrill/Desktop/hello.txt",
  "content": "Hello, World!"
}
```

**Allowed Directories:**
- `~/Desktop`
- `~/Documents`

**Response:**
```json
{"ok": "true"}
```

---

#### Read File
```bash
POST /v1/read_file
Content-Type: application/json

{"path": "/Users/christianmerrill/Desktop/hello.txt"}
```

**Response:**
```json
{"ok": "true", "content": "Hello, World!"}
```

---

## 🔒 Security

### Command Whitelist

Only these commands are allowed:
- `open`
- `osascript`
- `xcrun`
- `xcodebuild`

To add more, edit `ALLOWED_CMDS` in `Sources/AssistantBroker/main.swift`.

### Path Restrictions

File operations limited to:
- `~/Desktop`
- `~/Documents`

To add more, edit `ALLOWED_DIRS` in the source.

### Best Practices

1. **Never expose to the network** - Keep it on `127.0.0.1`
2. **Review commands** before adding to whitelist
3. **Monitor logs** at `~/Library/Logs/AssistantBroker.*.log`
4. **Grant minimal permissions** - Only Automation/Accessibility if needed

---

## 🛠️ Management

### Check Status

```bash
# If running as LaunchAgent
launchctl list | grep assistant-broker

# Should show PID if running
```

### View Logs

```bash
tail -f ~/Library/Logs/AssistantBroker.out.log
tail -f ~/Library/Logs/AssistantBroker.err.log
```

### Stop/Start

```bash
# Stop
launchctl stop com.neuroforge.assistant-broker

# Start
launchctl start com.neuroforge.assistant-broker

# Uninstall completely
make uninstall-agent
```

---

## 🧪 Examples

### From Shell

```bash
# Health check
curl -s http://127.0.0.1:8080/v1/health

# Open TextEdit
curl -X POST http://127.0.0.1:8080/v1/open_app \
  -H 'Content-Type: application/json' \
  -d '{"bundle_id":"com.apple.TextEdit"}'

# Write file to Desktop
curl -X POST http://127.0.0.1:8080/v1/write_file \
  -H 'Content-Type: application/json' \
  -d '{"path":"/Users/christianmerrill/Desktop/test.txt","content":"Hello!"}'

# Reveal file in Finder
curl -X POST http://127.0.0.1:8080/v1/run \
  -H 'Content-Type: application/json' \
  -d '{"cmd":"open","args":["-R","/Users/christianmerrill/Desktop/test.txt"]}'
```

### From Python

```python
import requests

BASE_URL = "http://127.0.0.1:8080"

# Open Calculator
resp = requests.post(
    f"{BASE_URL}/v1/open_app",
    json={"bundle_id": "com.apple.calculator"}
)
print(resp.json())  # {'ok': 'true'}
```

### From JavaScript

```javascript
const BASE_URL = "http://127.0.0.1:8080";

// Quit Safari
const resp = await fetch(`${BASE_URL}/v1/quit_app`, {
  method: "POST",
  headers: {"Content-Type": "application/json"},
  body: JSON.stringify({bundle_id: "com.apple.Safari"})
});
const data = await resp.json();
console.log(data);  // {ok: 'true'}
```

---

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Use different port
PORT=8099 make run
```

### LaunchAgent Not Starting

```bash
# Check logs
cat ~/Library/Logs/AssistantBroker.err.log

# Verify binary exists
ls -la ~/Documents/GitHub/assistant-broker/.build/release/assistant-broker

# Reload agent
launchctl unload ~/Library/LaunchAgents/com.neuroforge.assistant-broker.plist
launchctl load ~/Library/LaunchAgents/com.neuroforge.assistant-broker.plist
```

### Permission Denied

Grant permissions in **System Settings → Privacy & Security**:
- ✅ Automation
- ✅ Accessibility (if controlling other apps)

---

## 📊 Integration with Build Pipeline

Use the broker to:
1. **Reveal builds**: `POST /v1/run` with `open -R /path/to/App.app`
2. **Open DMGs**: `POST /v1/run` with `open /path/to/App.dmg`
3. **Launch apps**: Test newly built apps automatically

Example in build script:
```bash
DMG_PATH="/path/to/MyApp.dmg"
curl -X POST http://127.0.0.1:8080/v1/run \
  -H 'Content-Type: application/json' \
  -d "{\"cmd\":\"open\",\"args\":[\"$DMG_PATH\"]}"
```

---

## 🔄 Updates

### Rebuild After Code Changes

```bash
make build
make install-agent  # Restarts with new binary
```

---

## 📝 Files

```
assistant-broker/
├── Package.swift              # Swift package definition
├── Sources/
│   └── AssistantBroker/
│       └── main.swift        # Broker implementation
├── scripts/
│   └── com.neuroforge.assistant-broker.plist  # LaunchAgent config
├── Makefile                  # Build/install commands
└── README.md                 # This file
```

---

## 🎓 Next Steps

1. **Try it**: `make build && make run`
2. **Test it**: `make test`
3. **Install it**: `make install-agent`
4. **Integrate it**: Wire into your AI assistant

---

**Built with:** Swift 6.0 + Vapor 4.92  
**Platform:** macOS 13+  
**License:** MIT

