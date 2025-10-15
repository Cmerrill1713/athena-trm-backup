# 🗣️ Athena Voice Control — Natural Language System Commands

## Conversational Interface to Your Production Infrastructure

**Talk to Athena. Control your entire stack.**

---

## Quick Start

### Single Command Mode
```bash
./athena_voice.sh "bring everything online"
./athena_voice.sh "run smoke tests"
./athena_voice.sh "ship it"
```

### Interactive Mode
```bash
./athena_voice.sh

You: bring everything online
🧠 Athena: Bringing all services online...
[Stack starts...]
✅ Done.

You: run smoke tests
🧠 Athena: Running smoke tests...
[Tests execute...]
✅ Done.

You: exit
🧠 Athena: Goodbye.
```

---

## Available Commands

### Stack Management
```
"bring everything online"  → make stack-up
"shut everything down"     → make stack-down
"restart everything"       → make stack-restart
"what's running"           → make truth
"kill the ghosts"          → make nuke-ports
```

### Autonomous Operations
```
"enable watchdog"          → make auto-heal-start
"watchdog status"          → make auto-heal-status
"start self healing"       → make auto-heal-start
```

### Testing & Validation
```
"run smoke tests"          → make athena-tests-smoke
"run all tests"            → make athena-tests
"production gate"          → make tier4-proof
"chaos test"               → make chaos-test
"security scan"            → make sec-check
```

### Deployment & GitOps
```
"ship it"                  → make athena-canary
"backtrack"                → make athena-cleanup + stack-restart
"deploy to production"     → make prod-up
"show deployment history"  → make athena-history
```

### Monitoring
```
"open the dashboard"       → open http://localhost:3001
"health check"             → curl health endpoint
"check the gate"           → make truth
```

---

## How It Works

### 1. Intent Mapping
Natural language phrases → System commands via `athena_voice_map.json`

**Example:**
```json
{
  "stack_up": {
    "phrases": ["bring everything online", "start the stack", "wake up"],
    "command": "make stack-up",
    "response": "Bringing all services online...",
    "requires_confirmation": false
  }
}
```

### 2. Safety Gates
High-risk actions require confirmation:
- Shutdown
- Rollback
- Chaos testing
- Production deployment

**Example:**
```
You: shut everything down
🧠 Athena: Shutting down all services...

⚠️  This action requires confirmation.
Command: make stack-down
Proceed? (yes/no): yes

Executing: make stack-down
✅ Done.
```

### 3. Command Execution
All commands run in workspace root with full context.

---

## Customization

### Add New Commands
Edit `athena_voice_map.json`:

```json
{
  "intents": {
    "your_intent": {
      "phrases": ["your phrase", "alternative phrase"],
      "command": "make your-command",
      "response": "Your response",
      "requires_confirmation": false
    }
  }
}
```

### Chain Multiple Commands
```json
{
  "full_restart": {
    "phrases": ["full reset", "nuclear option"],
    "command": "make nuke-ports && make stack-up && make auto-heal-start",
    "response": "Performing full system reset...",
    "requires_confirmation": true
  }
}
```

### Add Aliases
```bash
# In your .zshrc or .bashrc:
alias athena='cd /Users/christianmerrill/Documents/GitHub && ./athena-voice-control/athena_voice.sh'

# Now you can:
athena "bring everything online"
athena  # Interactive mode
```

---

## Examples

### Morning Startup
```bash
$ athena "bring everything online"
🧠 Athena: Bringing all services online...
Executing: make stack-up
[Services start...]
✅ Done.

$ athena "enable watchdog"
🧠 Athena: Watchdog enabled. System will self-heal on failures.
Executing: make auto-heal-start
✅ Done.
```

### Deploy a Feature
```bash
$ git commit -am "new feature"
$ git push
# Athena pre-push hook validates

$ athena "ship it"
🧠 Athena: Deploying canary... I'll monitor SLOs and auto-promote or rollback.

⚠️  This action requires confirmation.
Command: make athena-canary
Proceed? (yes/no): yes

[Canary deploys, monitors, decides...]
✅ Done.
```

### Emergency Recovery
```bash
$ athena "kill the ghosts"
🧠 Athena: Eliminating ghost processes...

⚠️  This action requires confirmation.
Proceed? (yes/no): yes

Executing: make nuke-ports
✅ Done.

$ athena "fresh start"
🧠 Athena: Restarting all services...
[Stack restarts...]
✅ Done.
```

### Check Status
```bash
$ athena "what's running"
🧠 Athena: Checking actual system state...

[Truth output shows all services...]
✅ Done.

$ athena "watchdog status"
🧠 Athena: Checking watchdog status...

Uptime: 3600s
Recovery attempts: 0 / 3
✅ Done.
```

---

## Safety Features

### Confirmation Required
High-risk actions prompt for confirmation:
- Shutdown
- Rollback
- Kill ghosts
- Restart
- Canary deploy
- Chaos test
- Production deploy

### Audit Trail
All commands logged with:
- Timestamp
- Intent
- Command executed
- User

**View:** `tail -f /tmp/athena_voice_audit.log`

### Graceful Degradation
If Athena service not available:
- Warning shown
- Command still executes
- No blocking

---

## Advanced Usage

### Batch Commands
```bash
# Morning routine script
athena "bring everything online"
athena "enable watchdog"
athena "run smoke tests"
```

### CI/CD Integration
```yaml
# .github/workflows/deploy.yml
- name: Deploy via Athena
  run: |
    cd athena-voice-control
    ./athena_voice.sh "deploy to production"
```

### SSH Remote Control
```bash
ssh production-server "cd /opt/stack && ./athena-voice-control/athena_voice.sh 'health check'"
```

---

## Troubleshooting

### "I didn't understand that command"
**Problem:** Phrase not in intent map  
**Fix:** Add to `athena_voice_map.json` or try similar phrase

### "Athena not running"
**Problem:** Services not started  
**Fix:** `make stack-up`

### Command fails
**Problem:** Underlying command issue  
**Fix:** Run the make command directly for details

---

## Integration with Full System

### With Pre-Push Hook
```bash
git push
# Athena pre-push hook validates automatically
# No voice command needed
```

### With Watchdog
```bash
athena "enable watchdog"
# Watchdog monitors, heals, notifies
# No further commands needed
```

### With Notifications
```bash
export NOTIFY_WEBHOOK='...'
athena "enable watchdog"
# Get Slack notifications on recoveries
```

---

## The Complete Flow

```
┌────────────────────────────────┐
│  You: "bring everything online"│
└────────────────────────────────┘
               ↓
┌────────────────────────────────┐
│  Athena Voice Control          │
│  • Parse intent                │
│  • Map to command              │
│  • Check if confirmation needed│
└────────────────────────────────┘
               ↓
┌────────────────────────────────┐
│  Execute: make stack-up        │
└────────────────────────────────┘
               ↓
┌────────────────────────────────┐
│  Services start                │
│  Watchdog monitors             │
│  Pre-push hook guards          │
│  Canary system ready           │
└────────────────────────────────┘
```

---

## Files

```
athena-voice-control/
  athena_voice.sh          - Main script
  athena_voice_map.json    - Intent mapping
  README.md                - This guide
```

---

## The Philosophy

**From:**
```bash
cd /path/to/workspace
source venv/bin/activate
export TOKENS
make stack-up
make auto-heal-start
# ... 10 more commands
```

**To:**
```bash
athena "bring everything online"
athena "enable watchdog"
```

**Natural language → Real commands → Autonomous execution**

---

## Status

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                                   ┃
┃  You talk. Athena executes.       ┃
┃                                   ┃
┃  No CLI gymnastics.               ┃
┃  No manual steps.                 ┃
┃  Just conversation.               ┃
┃                                   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

---

**Built:** 2025-10-12  
**Status:** VOICE CONTROL OPERATIONAL  
**Interface:** Natural Language  
**Backend:** 5-Tier Autonomous System  

**You code. You talk. Athena executes.** 🗣️🧠🚀

