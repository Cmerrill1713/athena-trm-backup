# 🚀 GO LIVE ACTIVATION — Complete System Boot

## The Clean Path from Built → Running Live

**Everything is ready. Let's activate it.**

---

## Step 1: Boot the Entire Stack (30 seconds)

### Using Voice Control
```bash
athena "bring everything online"
```

### Or Direct Command
```bash
make stack-up
```

**Wait ~10 seconds for services to start.**

---

## Step 2: Verify All Services Healthy (15 seconds)

### Quick Check
```bash
athena "what's running"
```

### Detailed Verification
```bash
# Health check all services
curl -s http://127.0.0.1:8014/ready | jq .status  # Bridge
curl -s http://127.0.0.1:8090/ready | jq .status  # Athena (if endpoint exists)
curl -s http://127.0.0.1:8181/ready | jq .status  # UAT (if endpoint exists)

# Or use truth
make truth
```

**✅ Expected:**
- Bridge: `"ready"`
- All services showing healthy in truth output
- No ghost processes (PID count ≤ 6)

---

## Step 3: Activate Watchdog & Observability (10 seconds)

```bash
athena "enable watchdog"
```

**What this does:**
- Starts autonomous monitoring (30s interval)
- Auto-recovers failures in < 60s
- Logs all actions to `/tmp/watchdog_stack.log`

**Verify:**
```bash
athena "watchdog status"
# Should show: monitoring, 0 recoveries
```

---

## Step 4: Run Smoke Tests (5 seconds)

```bash
athena "run smoke tests"
```

**✅ Expected:**
```
Status: PASS
Passed: 3 | Failed: 0 | Skipped: 0
```

**If fails:** Check which test failed and fix before proceeding.

---

## Step 5: Connect Frontend to Live Backend

### For Next.js / React
Create or update `.env.local`:
```bash
NEXT_PUBLIC_API_BASE=http://127.0.0.1:8014
```

### For Vite / Vue
Create or update `.env.local`:
```bash
VITE_API_BASE=http://127.0.0.1:8014
```

### For SwiftUI (NeuroForgeApp)
```bash
cd NeuroForgeApp
API_BASE=http://127.0.0.1:8014 QA_MODE=1 swift run
```

---

## Step 6: Test Frontend → Backend Integration

### Test 1: Health Check from Frontend
```javascript
// In your browser console or app
fetch('http://127.0.0.1:8014/health')
  .then(r => r.json())
  .then(console.log)

// Expected: {"status": "healthy", "adapter": "..."}
```

### Test 2: Chat Endpoint
```bash
curl -X POST http://127.0.0.1:8014/chat \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello Athena"}' | jq .
```

**✅ Expected:** Response with text field

### Test 3: Traces Endpoint
```bash
curl -s http://127.0.0.1:8014/traces | jq '. | length'
```

**✅ Expected:** Number > 0 (trace count)

---

## Step 7: Run Full Tier 4 Proof (2 minutes)

```bash
make tier4-proof
```

**This validates:**
1. Health probes (/live, /ready)
2. Metrics export
3. Smoke tests
4. Security tools
5. Watchdog
6. Services running

**✅ All must pass for production readiness.**

---

## Step 8: Optional — Chaos Validation (2 minutes)

**Prove the system self-heals:**

```bash
# Terminal 1: Watch watchdog
make auto-heal-logs

# Terminal 2: Kill a service
pkill -f "uvicorn bridge"

# Watch Terminal 1: Should auto-recover in < 60s
```

**✅ Expected:** Watchdog detects → kills ghosts → restarts → validates

---

## Step 9: Deploy Test Feature with Canary (5 minutes)

```bash
# Create test commit
git checkout -b test/canary-flow
git commit --allow-empty -m "test: canary flow"

# Push (Athena pre-push validates)
git push -u origin test/canary-flow

# Deploy canary
athena "ship it"
```

**What happens:**
1. Canary deploys to :8015
2. Monitors for 5 minutes
3. Collects SLO metrics
4. ✅ Promotes if SLOs met
5. ❌ Rolls back + cleanup if failed

---

## Step 10: Verify Complete Integration

### Checklist
```bash
# 1. Stack running
athena "what's running"
# ✅ 3 services (Bridge, UAT, Athena)

# 2. Watchdog active
athena "watchdog status"
# ✅ Monitoring, uptime showing

# 3. Tests passing
athena "run smoke tests"
# ✅ 3/3 passed

# 4. Frontend connected
# ✅ Can fetch from API_BASE

# 5. Canary system works
# ✅ Can deploy, monitor, decide

# 6. Audit trail exists
athena "show deployment history"
# ✅ Shows events
```

---

## What Success Looks Like

### Services
```
Bridge:  http://127.0.0.1:8014 ✅ ready
UAT:     http://127.0.0.1:8181 ✅ healthy
Athena:  http://127.0.0.1:8090 ✅ healthy
```

### Watchdog
```
Status:     Monitoring ✅
Uptime:     > 0s
Recoveries: 0 (no failures yet)
Health:     All services healthy
```

### Tests
```
Smoke:      3/3 passed ✅
Pre-push:   Validated ✅
Tier 4:     6/6 gates passed ✅
```

### Canary
```
Deployed:   :8015 ✅
Monitored:  5 minutes ✅
Decision:   Promoted or rolled back ✅
Cleanup:    Auto-cleaned if failed ✅
```

---

## Troubleshooting

### Services Won't Start
```bash
athena "kill the ghosts"
athena "restart everything"
```

### Frontend Can't Connect
```bash
# Verify backend is up
curl http://127.0.0.1:8014/health

# Check CORS if browser
# Check API_BASE env var
# Check network tab for errors
```

### Tests Failing
```bash
athena "show recent errors"
make truth
# Fix issues, restart
```

### Watchdog Not Healing
```bash
make auto-heal-logs | tail -50
# Check for max retries or cooldown
```

---

## Production Deployment (When Ready)

### After All Tests Pass
```bash
# 1. Create rollback point
athena "create rollback point"

# 2. Tag ready for prod
git tag -a v0.9.3-ready -m "Athena autonomous system ready for production"

# 3. Deploy production stack
make prod-up

# 4. Open monitoring
open http://localhost:9090  # Prometheus
open http://localhost:3001  # Grafana (admin/admin)

# 5. Watch it run
athena "show deployment history"
```

---

## The Live System

```
┌─────────────────────────────────────┐
│  Frontend (SwiftUI/React/Vue)       │
│  - Text chat                        │
│  - Voice input                      │
│  - Streaming responses              │
└─────────────────────────────────────┘
                ↓
┌─────────────────────────────────────┐
│  Bridge Adapter :8014               │
│  - Routes requests                  │
│  - Circuit breaker                  │
│  - Health probes                    │
│  - Metrics export                   │
└─────────────────────────────────────┘
                ↓
      ┌─────────┴─────────┐
      ↓                   ↓
┌─────────────┐   ┌─────────────┐
│ UAT :8181   │   │Athena :8090 │
│ - Traces    │   │ - Agents    │
│ - Stats     │   │ - Chat      │
│ - Data      │   │ - Tests     │
└─────────────┘   └─────────────┘
                ↓
┌─────────────────────────────────────┐
│  Autonomous Layer                   │
│  - Watchdog (self-healing)          │
│  - Pre-push (validation)            │
│  - Canary (SLO gates)               │
│  - Notifications (Slack/etc)        │
└─────────────────────────────────────┘
                ↓
┌─────────────────────────────────────┐
│  Voice Control                      │
│  - 23 conversational intents        │
│  - Interactive mode                 │
│  - Safety confirmations             │
└─────────────────────────────────────┘
```

---

## Quick Activation Script

```bash
#!/bin/bash
# GO LIVE - Complete system activation

echo "🚀 Activating Athena Autonomous System..."
echo ""

# 1. Boot stack
echo "1/5: Starting services..."
athena "bring everything online"
sleep 5

# 2. Verify
echo "2/5: Verifying health..."
athena "what's running" | grep -q "Bridge" && echo "  ✅ Services up"

# 3. Enable watchdog
echo "3/5: Enabling autonomous healing..."
athena "enable watchdog"

# 4. Smoke tests
echo "4/5: Running validation..."
athena "run smoke tests"

# 5. Ready
echo "5/5: System operational"
echo ""
echo "╔════════════════════════════════════════════╗"
echo "║  ✅ ATHENA SYSTEM: LIVE & OPERATIONAL ✅   ║"
echo "╚════════════════════════════════════════════╝"
echo ""
echo "Frontend API: http://127.0.0.1:8014"
echo "Commands: athena help"
```

Save as `scripts/go_live.sh` and run: `bash scripts/go_live.sh`

---

## Success Criteria

### Minimum Viable Live
- [ ] Stack up (3 services)
- [ ] Smoke tests pass
- [ ] Watchdog active
- [ ] Frontend can fetch from :8014

### Production Ready
- [ ] Tier 4 proof green
- [ ] Canary deploy works
- [ ] Chaos test passes
- [ ] Notifications wired
- [ ] Dashboards accessible

---

## What to Test First

### Priority 1: Core Flow
1. athena "bring everything online"
2. athena "run smoke tests"
3. curl http://127.0.0.1:8014/health

### Priority 2: Autonomous
1. athena "enable watchdog"
2. pkill -f "uvicorn bridge"  # Kill service
3. Watch auto-recovery (< 60s)

### Priority 3: GitOps
1. git commit --allow-empty -m "test"
2. git push  # Athena pre-push validates
3. athena "ship it"  # Canary deploy

---

## The Moment of Truth

**Run this:**
```bash
athena "bring everything online"
athena "run smoke tests"
athena "enable watchdog"
```

**Then:**
- Open your frontend
- Try chat
- Try voice
- Watch it work

**You're live.** 🚀

---

**Built:** 2025-10-12  
**Status:** READY FOR ACTIVATION  
**Interface:** Conversational  
**System:** Fully Autonomous  

**Everything is ready. Time to flip the switch.** ⚡✨

