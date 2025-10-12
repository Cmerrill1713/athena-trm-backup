# 🤖 Self-Healing Stack - Autopilot Mode

> **From manual recovery to self-healing orchestration**

---

## 🎯 Evolution: Manual → Autopilot

### Current State (Deterministic but Manual)
```bash
you → make truth → make nuke-ports → make stack-up → make athena-tests
```

### Next State (Self-Healing Autopilot)
```bash
watchdog → detect → nuke → restart → test → log → notify
```

**You get to sleep while your stack punches ghosts in the face.** 😎

---

## 🤖 What the Watchdog Does

### Every 30 seconds:
1. ✅ Checks Bridge health (`:8014/health`)
2. ✅ Checks Athena health (`:8090/health`)
3. ✅ Checks UAT health (`:8181/health`)
4. ✅ Counts PIDs on ports (detects ghosts)

### If unhealthy:
1. 🔍 **Detect** - Identifies the problem
2. 💥 **Nuke** - Kills all ghosts (`make nuke-ports`)
3. 🚀 **Restart** - Starts stack (`make stack-up`)
4. ✅ **Verify** - Checks health
5. 🧪 **Test** - Runs smoke tests
6. 📝 **Log** - Records incident
7. 📢 **Notify** - Alerts you (optional)

---

## 🚀 Quick Start

### Start watchdog (foreground, see output)
```bash
bash scripts/stack_watchdog.sh
```

### Start watchdog (background)
```bash
make watchdog-start
```

### Check status
```bash
make watchdog-status
```

### View logs
```bash
make watchdog-logs
# or
tail -f /tmp/stack_watchdog.log
```

### Stop watchdog
```bash
make watchdog-stop
```

---

## 🔧 Installation (Auto-Start on Boot)

### macOS (LaunchAgent)
```bash
# Install
make watchdog-install

# Check status
launchctl list | grep watchdog

# View logs
tail -f /tmp/stack_watchdog.log

# Uninstall
make watchdog-uninstall
```

### Linux (systemd)
Create `/etc/systemd/system/stack-watchdog.service`:
```ini
[Unit]
Description=Stack Watchdog - Self-Healing Orchestration
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/workspace
ExecStart=/bin/bash /path/to/workspace/scripts/stack_watchdog.sh
Restart=always
RestartSec=10

Environment="WORKSPACE_ROOT=/path/to/workspace"
Environment="CHECK_INTERVAL=30"
Environment="MAX_RESTARTS_PER_HOUR=5"

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable stack-watchdog
sudo systemctl start stack-watchdog

# Check status
sudo systemctl status stack-watchdog

# View logs
sudo journalctl -u stack-watchdog -f
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# Basic settings
export CHECK_INTERVAL=30              # Check every 30 seconds
export MAX_RESTARTS_PER_HOUR=5        # Limit to 5 restarts/hour
export BACKOFF_SECONDS=60             # Wait 60s if limit exceeded

# Service endpoints
export BRIDGE_URL=http://127.0.0.1:8014
export ATHENA_URL=http://127.0.0.1:8090
export UAT_URL=http://127.0.0.1:8181
export ATH_TOKEN=supersecret
export UAT_TOKEN=supersecret

# Logging
export LOGFILE=/tmp/stack_watchdog.log
export INCIDENT_LOG=/tmp/stack_incidents.log

# Slack notifications (optional)
export NOTIFY_SLACK=1
export SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Telegram notifications (optional)
export NOTIFY_TELEGRAM=1
export TELEGRAM_BOT_TOKEN=your-bot-token
export TELEGRAM_CHAT_ID=your-chat-id
```

### Using .env file
```bash
# Create .env.watchdog
cat > .env.watchdog << 'EOF'
CHECK_INTERVAL=30
MAX_RESTARTS_PER_HOUR=5
NOTIFY_SLACK=1
SLACK_WEBHOOK=https://hooks.slack.com/...
EOF

# Load and run
source .env.watchdog
bash scripts/stack_watchdog.sh
```

---

## 📊 Features

### ✅ Health Detection
- HTTP health checks for all services
- Ghost process detection (multiple PIDs)
- Response status validation
- Automatic failure classification

### ✅ Self-Healing
- Automatic ghost killing
- Clean stack restart
- Post-recovery verification
- Smoke test validation

### ✅ Safety Features
- **Restart limiting** - Max 5 restarts/hour (prevents loops)
- **Exponential backoff** - 60s wait if limit hit
- **Incident logging** - All events tracked
- **State management** - Restart counts tracked

### ✅ Notifications
- Slack webhooks
- Telegram bot
- Incident logging
- Timestamped events

### ✅ Observability
- Real-time logs (`/tmp/stack_watchdog.log`)
- Incident history (`/tmp/stack_incidents.log`)
- Restart count tracking
- Per-issue root cause logging

---

## 📝 Log Output Examples

### Healthy Check
```
[2025-10-12 14:30:00] [INFO] ✅ Stack healthy (PIDs: 3)
```

### Incident Detection
```
[2025-10-12 14:31:00] [INCIDENT] ❌ Stack unhealthy: Ghost processes detected (6 PIDs, expected 3)
[2025-10-12 14:31:00] [HEAL] Initiating self-heal sequence...
[2025-10-12 14:31:00] [HEAL] Step 1/4: Killing ghosts (nuke-ports)...
[2025-10-12 14:31:02] [HEAL] Step 2/4: Starting stack...
[2025-10-12 14:31:05] [HEAL] Stack started successfully
[2025-10-12 14:31:08] [HEAL] Step 3/4: Verifying health...
[2025-10-12 14:31:08] [HEAL] Health check passed
[2025-10-12 14:31:08] [HEAL] Step 4/4: Running smoke tests...
[2025-10-12 14:31:23] [HEAL] Smoke tests passed
[2025-10-12 14:31:23] [HEAL] ✅ Self-heal complete. Restart count: 1/hour
```

### Restart Limit Hit
```
[2025-10-12 15:00:00] [ERROR] Restart limit exceeded (5 restarts in last hour). Entering backoff.
[2025-10-12 15:00:00] [ERROR] Cannot self-heal: restart limit exceeded. Manual intervention required.
```

---

## 🔔 Setting Up Notifications

### Slack

1. Create incoming webhook in Slack:
   - Go to: https://api.slack.com/messaging/webhooks
   - Create webhook for your channel
   - Copy webhook URL

2. Configure watchdog:
```bash
export NOTIFY_SLACK=1
export SLACK_WEBHOOK=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX
```

3. Test:
```bash
curl -X POST $SLACK_WEBHOOK \
  -H "Content-Type: application/json" \
  -d '{"text":"🤖 Stack Watchdog: Test notification"}'
```

### Telegram

1. Create bot:
   - Talk to @BotFather on Telegram
   - Use `/newbot` command
   - Copy bot token

2. Get chat ID:
```bash
# Send message to your bot first, then:
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
# Look for "chat":{"id": 123456789}
```

3. Configure watchdog:
```bash
export NOTIFY_TELEGRAM=1
export TELEGRAM_BOT_TOKEN=110201543:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw
export TELEGRAM_CHAT_ID=123456789
```

4. Test:
```bash
curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d "chat_id=${TELEGRAM_CHAT_ID}" \
  -d "text=🤖 Stack Watchdog: Test notification"
```

---

## 🎯 Usage Patterns

### Development (Manual)
```bash
# You monitor and control
make truth
make stack-up
# ... work ...
make stack-down
```

### Staging (Semi-Auto)
```bash
# Watchdog in foreground (visible)
bash scripts/stack_watchdog.sh
# Or background:
make watchdog-start
```

### Production (Fully Auto)
```bash
# Install as service
make watchdog-install  # macOS
# or
sudo systemctl enable stack-watchdog  # Linux

# Monitor
make watchdog-status
make watchdog-logs
make watchdog-incidents
```

---

## 🚨 Common Scenarios

### Scenario 1: Ghost Processes at 3 AM

**Without Watchdog:**
- Ghosts accumulate
- Services slow down
- You wake up to alerts
- Manually run `make nuke-ports && make stack-up`

**With Watchdog:**
- Watchdog detects ghosts at 3:00:15 AM
- Auto-heals in 8 seconds
- Logs incident
- Sends you notification (optional)
- You sleep through it 😴

### Scenario 2: Service Crash

**Without Watchdog:**
- Service down
- Tests fail
- You investigate
- Manually restart

**With Watchdog:**
- Service crash detected
- Stack restarted automatically
- Smoke tests validate
- Incident logged
- Back online in 15 seconds

### Scenario 3: Restart Loop (Safety)

**With Watchdog:**
- Issue causes crash
- Watchdog restarts (1/5)
- Crashes again
- Watchdog restarts (2/5)
- ... happens 5 times
- Watchdog hits limit
- Enters backoff, alerts you
- You investigate actual root cause

---

## 📊 Monitoring Watchdog

### Check Status
```bash
make watchdog-status
```

Output:
```
📊 Watchdog Status:
  Status: ✅ Running
  PID: 12345
  Restarts: 2/hour
  Last incident: [2025-10-12 14:31:00] [HEAL] Self-heal complete
```

### View Recent Activity
```bash
# Last 20 log lines
tail -20 /tmp/stack_watchdog.log

# Last 10 incidents
tail -10 /tmp/stack_incidents.log

# Follow live
make watchdog-logs
```

### Check Restart Rate
```bash
cat /tmp/stack_watchdog_restarts
# Output: 2 (number of restarts in last hour)
```

---

## 🎓 Best Practices

### 1. Start with Manual Mode
```bash
# Run in foreground first to see behavior
bash scripts/stack_watchdog.sh
```

### 2. Monitor for a Day
```bash
# Let it run, watch for false positives
make watchdog-logs
```

### 3. Tune Check Interval
```bash
# Adjust based on your needs
export CHECK_INTERVAL=60  # Less aggressive
export CHECK_INTERVAL=15  # More responsive
```

### 4. Set Restart Limits
```bash
# Prevent restart loops
export MAX_RESTARTS_PER_HOUR=5  # Default
export MAX_RESTARTS_PER_HOUR=3  # More conservative
```

### 5. Enable Notifications
```bash
# Get alerts for incidents
export NOTIFY_SLACK=1
export SLACK_WEBHOOK=...
```

### 6. Review Incidents Weekly
```bash
# Learn from patterns
make watchdog-incidents
```

---

## 🔧 Troubleshooting

### Watchdog won't start
```bash
# Check script syntax
bash -n scripts/stack_watchdog.sh

# Check permissions
ls -la scripts/stack_watchdog.sh
chmod +x scripts/stack_watchdog.sh
```

### Watchdog starts but doesn't heal
```bash
# Check logs for errors
tail -50 /tmp/stack_watchdog.log

# Verify make commands work manually
make nuke-ports
make stack-up
```

### Notifications not working
```bash
# Test Slack manually
curl -X POST $SLACK_WEBHOOK \
  -H "Content-Type: application/json" \
  -d '{"text":"test"}'

# Check environment vars are set
env | grep SLACK
env | grep TELEGRAM
```

### Too many restarts
```bash
# Check incident log for root cause
cat /tmp/stack_incidents.log

# Increase limits if intentional
export MAX_RESTARTS_PER_HOUR=10
```

---

## 🎉 Benefits

### Before (Manual)
- 🕐 You check health manually
- 👤 You kill ghosts manually
- 🔄 You restart manually
- 😴 Downtime while you sleep
- 📈 Slow incident response

### After (Self-Healing)
- ⏱️ Health checked every 30s
- 🤖 Ghosts killed automatically
- 🔄 Stack restarted automatically
- 😴 You sleep through incidents
- ⚡ 8-second incident response

**Mean Time To Recovery: 3 AM → 8 seconds** 🚀

---

## 📋 Summary

**You've upgraded from:**
- Manual monitoring → Automated detection
- Manual recovery → Self-healing
- Reactive → Proactive
- Hope → Receipts

**The loop:**
```bash
watchdog → detect → nuke → restart → test → log → notify → sleep
```

**Fast. Boring. Bulletproof. Self-healing.**

---

## 🚀 Quick Commands

```bash
# Start
make watchdog-start

# Status
make watchdog-status

# Logs
make watchdog-logs

# Incidents
make watchdog-incidents

# Stop
make watchdog-stop

# Install (auto-start)
make watchdog-install
```

---

**Status:** ✅ SELF-HEALING ENABLED
**Your new superpower:** Sleep through outages 😴

🤖 **Autopilot engaged!**
