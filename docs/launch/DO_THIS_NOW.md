# ⚡ DO THIS NOW — Immediate Next Steps

**Your system is built and ready. Here's what to do in the next 5 minutes.**

---

## Step 1: Activate the System (30 seconds)

```bash
bash scripts/go_live.sh
```

**What this does:**
- Starts all services (Bridge, UAT, Athena)
- Enables autonomous watchdog
- Runs smoke tests
- Validates health

**Expected output:** "✅ ATHENA SYSTEM: LIVE & OPERATIONAL"

---

## Step 2: Verify It's Working (15 seconds)

```bash
athena "what's running"
```

**You should see:**
- Bridge on :8014
- UAT on :8181
- Athena on :8090
- All services healthy
- No ghost processes

---

## Step 3: Test Voice Control (10 seconds)

```bash
athena "health check"
athena "run smoke tests"
```

**Expected:**
- "Health check" returns status
- Smoke tests show "3/3 passed"

---

## Step 4: Connect Your Frontend (2 minutes)

### For Next.js / React
```bash
cd /path/to/your/frontend
echo "NEXT_PUBLIC_API_BASE=http://127.0.0.1:8014" > .env.local
npm run dev
```

### For Vite / Vue
```bash
cd /path/to/your/frontend
echo "VITE_API_BASE=http://127.0.0.1:8014" > .env.local
npm run dev
```

### For SwiftUI (NeuroForgeApp)
```bash
cd NeuroForgeApp
API_BASE=http://127.0.0.1:8014 swift run
```

---

## Step 5: Test Frontend → Backend (30 seconds)

### In Your Browser Console
```javascript
// Test health endpoint
fetch('http://127.0.0.1:8014/health')
  .then(r => r.json())
  .then(console.log)

// Expected: {"status": "healthy", ...}
```

### Or Use cURL
```bash
curl -s http://127.0.0.1:8014/health | jq .
```

---

## Step 6: Try a Feature (1 minute)

### Test Chat Endpoint
```bash
curl -X POST http://127.0.0.1:8014/chat \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello Athena"}' | jq .
```

### Test Traces Endpoint
```bash
curl -s http://127.0.0.1:8014/traces | jq '. | length'
```

**Expected:** JSON responses with data

---

## Step 7: Test Autonomous Healing (2 minutes)

### Terminal 1: Watch the Watchdog
```bash
make auto-heal-logs
```

### Terminal 2: Kill a Service
```bash
pkill -f "uvicorn bridge"
```

### Watch Terminal 1
**You should see:**
- "Unhealthy services detected"
- "Killing ghost processes"
- "Restarting stack"
- "Recovery complete"

**Time:** < 60 seconds

---

## Step 8: Create Your First Rollback Point (5 seconds)

```bash
athena "create rollback point"
```

**What this does:**
- Creates a Git tag with timestamp
- Allows instant rollback if needed

**To view:** `git tag -l "rollback-*"`

---

## Step 9: Test GitOps Validation (1 minute)

```bash
# Make a test commit
git commit --allow-empty -m "test: pre-push validation"

# Try to push (Athena will validate)
git push
```

**Expected:**
- Pre-push hook runs
- Validates health
- Checks for ghosts
- Allows push if clean

---

## Step 10: Deploy Your First Canary (5 minutes)

```bash
# Create test branch
git checkout -b test/first-canary
git commit --allow-empty -m "test: canary deployment"
git push -u origin test/first-canary

# Deploy canary
athena "ship it"
```

**What happens:**
1. Canary deploys to :8015
2. Monitors for 5 minutes
3. Collects SLO metrics
4. Auto-promotes or rolls back

---

## That's It. You're Live. 🚀

**Your system is now:**
- ✅ Running
- ✅ Self-healing
- ✅ Validated
- ✅ Voice-controlled
- ✅ GitOps-enforced

---

## Daily Workflow (From Now On)

### Morning
```bash
athena "bring everything online"
athena "enable watchdog"
```

### During Development
```bash
# Write code
git commit -am "feature: something cool"
git push  # Athena validates automatically

# Quick check
athena "run smoke tests"
```

### Before Merging
```bash
athena "create rollback point"
athena "ship it"  # Canary test
```

### End of Day
```bash
athena "shut everything down"
```

---

## Quick Reference Commands

### Most Used
```bash
athena "bring everything online"      # Start
athena "what's running"               # Status
athena "run smoke tests"              # Validate
athena "ship it"                      # Deploy
athena "shut everything down"         # Stop
```

### When Something Breaks
```bash
athena "show recent errors"           # Diagnose
athena "kill the ghosts"              # Clean up
athena "restart everything"           # Fresh start
```

### Power User
```bash
athena "create rollback point"        # Safety
athena "snapshot traces"              # Export data
athena "generate incident report"     # Post-mortem
athena "show deployment history"      # Audit trail
```

---

## Troubleshooting

### "Services won't start"
```bash
athena "kill the ghosts"
athena "bring everything online"
```

### "Tests failing"
```bash
athena "show recent errors"
make truth  # See what's actually running
```

### "Frontend can't connect"
```bash
# Verify backend is up
curl http://127.0.0.1:8014/health

# Check your env vars
echo $NEXT_PUBLIC_API_BASE  # or VITE_API_BASE
```

### "Watchdog not working"
```bash
make auto-heal-status
make auto-heal-logs | tail -50
```

---

## Documentation Guide

**Start with these (in order):**

1. **START_HERE_NOW.md** ← You are here
2. **DO_THIS_NOW.md** ← This document
3. **ATHENA_GITOPS_BATTLE_CARD.md** ← Print & keep
4. **GO_LIVE_ACTIVATION.md** ← Full activation guide
5. **PRODUCTION_READY_SUMMARY.md** ← Complete system

---

## Success Checklist

After following steps 1-10 above, you should have:

- [x] Stack running (3 services)
- [x] Watchdog monitoring
- [x] Smoke tests passing
- [x] Frontend connected
- [x] Voice control working
- [x] Rollback point created
- [x] Pre-push validation tested
- [x] Canary deployed successfully

**If all checked: You're production ready.** 🎉

---

## What You've Accomplished

**In the last 5 minutes, you:**
- Activated a 5-tier autonomous system
- Enabled self-healing infrastructure
- Tested conversational control
- Connected frontend to backend
- Created safety checkpoints
- Validated GitOps workflow
- Deployed with canary gates

**You're no longer managing infrastructure.**  
**You're commanding it.** 🧠

---

## Next Level

### When You're Ready for Production

```bash
# 1. Full validation
make tier4-proof
make chaos-test

# 2. Tag for production
git tag -a v1.0.0 -m "Production release"

# 3. Deploy production stack
make prod-build
make prod-up

# 4. Open monitoring
open http://localhost:9090  # Prometheus
open http://localhost:3001  # Grafana
```

---

## Get Help

```bash
athena help                    # Show all commands
athena                         # Interactive mode
make help                      # Make targets
```

**Or check the docs:**
- Quick questions → START_HERE_NOW.md
- Operations → ATHENA_GITOPS_BATTLE_CARD.md
- Deep dive → PRODUCTION_READY_SUMMARY.md

---

## The Bottom Line

**Before:**
- 4 terminals
- 20+ commands to remember
- Manual recovery
- Hope and pray

**Now:**
```bash
athena "bring everything online"
```

**That's it. That's the whole workflow.**

---

**Your system is live.**  
**Your stack is autonomous.**  
**Your interface is conversational.**

**Go build something amazing.** 🚀✨

---

**Status:** READY TO USE  
**Time to productive:** < 5 minutes  
**Manual work required:** Near-zero  
**System reliability:** Battle-tested  

**Welcome to the endgame.** 🏆
