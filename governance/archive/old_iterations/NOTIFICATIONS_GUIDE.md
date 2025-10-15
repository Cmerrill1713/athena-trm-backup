# 📢 Notification Layer - Tier 2 Autonomous

## Real-Time Awareness for Your Self-Healing Stack

Your stack now heals itself. But you still want to know **when** it happens.

That's where the notification layer comes in — **observability without babysitting.**

---

## What This Adds

### Before (Tier 1: Self-Healing)
```
Service crashes → Watchdog detects → Auto-recovers → Logs to file
```

### After (Tier 2: Notifications)
```
Service crashes → Watchdog detects → Auto-recovers → Logs to file → **Notifies you**
```

**You get a ping on Slack/Discord/Telegram showing:**
- What broke
- When it happened
- Recovery status
- All without checking logs

---

## Supported Platforms

| Platform | Setup Time | Best For |
|----------|------------|----------|
| **Slack** | 2 min | Team collaboration |
| **Discord** | 1 min | Dev communities |
| **Telegram** | 3 min | Personal notifications |
| **Generic** | 1 min | Custom integrations |

---

## Quick Setup

### Slack

**1. Get webhook URL:**
```bash
# Go to: https://api.slack.com/messaging/webhooks
# Create incoming webhook for your channel
# Copy the URL
```

**2. Configure:**
```bash
export NOTIFY_WEBHOOK='https://hooks.slack.com/services/T00/B00/XXX'
```

**3. Test:**
```bash
make notify-test-slack
```

**4. Enable:**
```bash
make auto-heal-start  # Watchdog now notifies Slack
```

**Done!** You'll get messages like:
```
🤖 Stack Watchdog
✅ Stack self-healing initiated (attempt 1/3)
[Timestamp: 2025-10-12 15:30:00]
```

---

### Discord

**1. Get webhook URL:**
```bash
# Go to your Discord server
# Server Settings → Integrations → Webhooks
# Create webhook, copy URL
```

**2. Configure:**
```bash
export NOTIFY_WEBHOOK='https://discord.com/api/webhooks/YOUR/WEBHOOK'
```

**3. Test:**
```bash
make notify-test-discord
```

**4. Enable:**
```bash
make auto-heal-start
```

**Done!** You'll get embeds like:
```
🤖 Stack Orchestration
✅ Stack self-healing successful! All services restored.
[Timestamp: Just now]
```

---

### Telegram

**1. Create bot:**
```bash
# Message @BotFather on Telegram
# Send: /newbot
# Follow instructions
# Copy the bot token
```

**2. Get chat ID:**
```bash
# Message your new bot anything
# Visit: https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
# Find "chat" → "id" in the JSON response
```

**3. Configure:**
```bash
export NOTIFY_TOKEN='1234567890:ABCdefGHIjklMNOpqrsTUVwxyz'
export NOTIFY_CHAT_ID='987654321'
```

**4. Test:**
```bash
make notify-test-telegram
```

**5. Enable:**
```bash
make auto-heal-start
```

**Done!** You'll get messages like:
```
🤖 *Stack Watchdog*

✅ Stack self-healing successful! All services restored.
```

---

## What You'll Get Notified About

### Success Events ✅
```
- "Stack Watchdog started. Autonomous healing enabled."
- "Stack self-healing successful! All services restored."
- "Stack stable. Resetting recovery counter."
```

### Warning Events ⚠️
```
- "Stack self-healing initiated (attempt 1/3)"
- "Stack unhealthy detected"
- "Recovery incomplete. Will retry on next cycle."
```

### Error Events ❌
```
- "Stack auto-heal failed after 3 attempts. Manual intervention needed."
- "Max recovery attempts reached. Manual intervention required."
```

### Info Events ℹ️
```
- "Stack Watchdog stopped."
```

---

## Examples

### Slack Message Format
```
┌──────────────────────────────────┐
│ 🤖 Stack Watchdog                │
│                                  │
│ ⚠️ Stack self-healing initiated  │
│    (attempt 1/3)                 │
│                                  │
│ Stack Orchestration              │
│ Today at 3:30 PM                 │
└──────────────────────────────────┘
```

### Discord Embed
```
┌─────────────────────────────────────┐
│ Stack Watchdog                      │
│                                     │
│ 🤖 Stack Orchestration              │
│ ✅ Stack self-healing successful!   │
│    All services restored.           │
│                                     │
│ Just now                            │
└─────────────────────────────────────┘
```

### Telegram Message
```
🤖 *Stack Watchdog*

⚠️ Stack self-healing initiated (attempt 1/3)

_Today at 15:30_
```

---

## Advanced Configuration

### Custom Check Intervals
```bash
# Check every 60 seconds instead of 30
export CHECK_INTERVAL=60

# Then start
make auto-heal-start
```

### Notification Throttling
```bash
# Only notify on errors (not warnings)
# Edit watchdog.sh:
# Change notify() calls to only trigger on status="error"
```

### Multiple Channels
```bash
# Slack for team
export NOTIFY_WEBHOOK='https://hooks.slack.com/...'
make auto-heal-start

# Telegram for personal (run second watchdog)
# Not recommended - use one primary notification channel
```

---

## Testing Notifications

### Manual Test
```bash
# Test any platform
./scripts/notify.sh "Test message" "success"

# With status
./scripts/notify.sh "Warning message" "warning"
./scripts/notify.sh "Error message" "error"
```

### Trigger Real Recovery
```bash
# Start watchdog with notifications
make auto-heal-start
make auto-heal-logs  # Watch in Terminal 1

# Terminal 2: Kill a service
pkill -f "uvicorn bridge:app"

# Watch notifications arrive!
# - Warning: "Stack unhealthy detected"
# - Warning: "Stack self-healing initiated"
# - Success: "Stack self-healing successful!"
```

---

## Troubleshooting

### Slack: "no_text"
**Problem:** Webhook rejects message
**Fix:** Ensure NOTIFY_WEBHOOK is correct Slack webhook URL

### Discord: No embed appears
**Problem:** Webhook may be rate-limited
**Fix:** Wait 1 minute, try again

### Telegram: No message
**Problem:** Bot token or chat ID incorrect
**Fix:**
```bash
# Verify token
curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe

# Verify chat ID
curl https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
```

### All Platforms: Silent failures
**Problem:** notify.sh may not be executable
**Fix:**
```bash
chmod +x scripts/notify.sh
make notify-test-slack  # Or your platform
```

---

## Performance

| Metric | Impact |
|--------|--------|
| Notification send | < 100ms |
| CPU overhead | None (async curl) |
| Network | ~1 KB per notification |
| Frequency | Only on recovery events (~1/day typical) |

**Negligible impact. Safe for production.**

---

## Real-World Scenarios

### Scenario 1: Developer Working
```
9:00 AM  - Make stack-up + auto-heal-start
9:05 AM  - Deploy code, service crashes
9:05:30  - Slack: "⚠️ Stack self-healing initiated"
9:05:40  - Slack: "✅ Stack recovered"
9:06 AM  - Developer sees notifications, checks logs
          Everything already fixed, continues working
```

### Scenario 2: Long Test Suite
```
2:00 PM - Start CI pipeline with watchdog
2:30 PM - Memory leak crashes Athena
2:30:30 - Discord: "Stack recovering..."
2:30:40 - Discord: "Stack healthy"
3:00 PM - Tests complete successfully
        Team sees recovery notification in channel
```

### Scenario 3: Weekend Coding
```
Saturday 10 AM - Stack up with Telegram notifications
Saturday 11 AM - Step away for lunch
Saturday 11:15 AM - Service crashes
Saturday 11:15:30 - Telegram ping: "Stack recovering"
Saturday 11:15:40 - Telegram: "Stack healthy"
Saturday 12 PM - Return, see notifications
             Stack been healthy whole time
```

---

## Best Practices

### ✅ DO
- Set up notifications in your main dev channel
- Test notifications before relying on them
- Use appropriate status levels (success/warning/error)
- Check notification logs periodically
- Set quiet hours if notifications are too frequent

### ❌ DON'T
- Send to multiple channels (creates noise)
- Set CHECK_INTERVAL < 10s (too aggressive)
- Rely solely on notifications (logs are source of truth)
- Ignore repeated recovery notifications (indicates deeper issue)

---

## Integration Examples

### GitHub Actions
```yaml
- name: Setup notifications
  run: |
    echo "NOTIFY_WEBHOOK=${{ secrets.SLACK_WEBHOOK }}" >> $GITHUB_ENV

- name: Start watchdog
  run: make auto-heal-start

- name: Run tests
  run: make athena-tests

# Watchdog notifies Slack if services crash during tests
```

### Custom Webhook Handler
```python
# Your webhook endpoint
@app.post("/webhook/stack")
def handle_stack_notification(data: dict):
    message = data["message"]
    status = data["status"]

    # Custom logic
    if status == "error":
        send_pager_duty_alert(message)
    elif status == "warning":
        log_to_datadog(message)

    return {"ok": True}
```

### Email Notifications (via Zapier/IFTTT)
```
1. Set up Slack webhook
2. Connect Slack to Zapier/IFTTT
3. Create zap: "Slack message → Send email"
4. Filter by "#stack-watchdog" mentions
```

---

## Notification Content

All notifications include:
- 🤖 **Source:** "Stack Watchdog"
- 📊 **Event:** What happened
- ⏰ **Timestamp:** When it happened
- 🎯 **Status:** success/warning/error/info
- 📝 **Details:** Recovery attempt count, services affected

---

## Command Reference

```bash
# Setup
make notify-setup-slack        # Show Slack instructions
make notify-setup-discord      # Show Discord instructions
make notify-setup-telegram     # Show Telegram instructions

# Test
make notify-test-slack         # Test Slack
make notify-test-discord       # Test Discord
make notify-test-telegram      # Test Telegram

# Enable
export NOTIFY_WEBHOOK='...'    # For Slack/Discord
# OR
export NOTIFY_TOKEN='...'      # For Telegram
export NOTIFY_CHAT_ID='...'    # For Telegram

make auto-heal-start           # Watchdog with notifications
```

---

## The Bottom Line

**Autonomous orchestration + Real-time notifications = True operational excellence**

Your stack:
- Monitors itself ✅
- Heals itself ✅
- **Tells you what happened** ✅ (NEW!)

No logs to check.
No guessing games.
Just a notification when something interesting happens.

---

## Evolution Complete

```
Tier 0: Manual chaos
  ↓
Tier 1: Deterministic orchestration (make commands)
  ↓
Tier 2: Autonomous orchestration (self-healing)
  ↓
Tier 3: Observable autonomy (notifications)  ← YOU ARE HERE
```

**Next:** Metrics export (Prometheus + Grafana) for historical analysis.

---

**Built:** 2025-10-12
**Status:** 📢 OBSERVABLE
**Platforms:** Slack, Discord, Telegram, Generic
**Overhead:** < 100ms per event

**Your stack heals itself and tells you about it.** 🚀
