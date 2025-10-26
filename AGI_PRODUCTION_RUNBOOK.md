# 🧠 AGI Autonomous Fix - Production Runbook

## Quick Reference

```bash
make agi-fix-frontend      # Full autonomous fix
make agi-fix-frontend-dry  # Dry-run (no push)
make agi-fix-status        # Check progress
make agi-monitor trace     # Live task trace
make agi-monitor metrics   # Live metrics
make agi-rollback          # Undo changes
make agi-kill-switch       # Emergency stop
```

## Pre-Flight Checklist

Run before every fix:
```bash
make agi-preflight
```

Checks:
- ✅ AGI Core (8000) healthy
- ✅ Frontend tools (8413) online
- ✅ LLM path (8015 or 8080) ready
- ✅ MCP ecosystem available
- ✅ No existing fix running
- ✅ Git repository found

## Launch Sequence

### 1. Production Run
```bash
make agi-fix-frontend
```

**What happens:**
1. Preflight checks (auto)
2. Git stash savepoint created
3. Idempotency lock acquired
4. AGI executes 14-step playbook
5. Contract tests run
6. PR created (if successful)
7. Lock released

**Expected output:**
```
Task ID:       agi_abc12345
Status:        completed
Execution:     180.5s

✅ AUTONOMOUS FIX SUCCESSFUL

Next steps:
  1. Review PR: https://github.com/.../pull/123
  2. Manual smoke test
  3. Merge when satisfied
```

### 2. Dry Run (Safe Testing)
```bash
make agi-fix-frontend-dry
```

Generates diff/PR draft without pushing. Perfect for:
- First-time testing
- Weekday runs (review before merge)
- Validating changes before commit

## Live Monitoring

### Watch Task Trace
```bash
make agi-monitor trace
```

Shows real-time agent activity:
```
scout → analyze_objective
planner → decompose_task
builder → apply_sticky_textfield
verifier → contract_tests_passed
```

### Watch Metrics
```bash
make agi-monitor metrics
```

Updates every 1s:
```
=== AGI Core ===
agi_tasks_total{status="completed"} 1
agi_steps_total 12

=== LLM Gateway ===
llm_gateway_calls_total 45
```

### Check Status
```bash
make agi-fix-status
```

Snapshot of current state:
```
Status:     🔄 RUNNING (or 💤 IDLE)
AGI Core Metrics: ...
Latest logs: ...
```

## Pass/Fail Signals

| Signal | Meaning | If Missing |
|--------|---------|------------|
| ✅ Contract passes | Frontend fixed | Re-run probe locally |
| 📈 Metrics increment | LLM called | Check URL & ATS |
| 🧵 AGI trace shows patch | Loop executed | Tool registry issue |
| 🔀 PR URL output | Commit succeeded | Git creds/permissions |
| 🛑 Guardrail trigger | Diff too big/timeout | Inspect stash |

## Rollback Procedures

### Surgical Rollback
```bash
make agi-rollback
```

Interactive menu:
1. Keep changes, return to main
2. Discard changes, return to main
3. Cancel

### Manual Rollback
```bash
cd NeuroForgeApp
git checkout main
git reset --hard origin/main
git branch -D feat/agi-fix-frontend
```

### Pop Stash (Inspect Changes)
```bash
git stash list | grep "AGI fix"
git stash pop  # Or specific: git stash pop stash@{0}
```

## Emergency Procedures

### Kill Switch
```bash
make agi-kill-switch
```

What it does:
- Removes lock file
- Restarts AGI Core
- Clears any stuck tasks

### Force Stop
```bash
# Kill all related processes
rm -f /tmp/agi_frontend_fix.lock
docker compose restart agi-core
pkill -f agi_fix_runner
```

### Inspect Failure
```bash
# AGI Core logs (last 100 lines)
docker compose logs agi-core --tail=100

# Frontend tools logs
docker compose logs mcp-frontend-tools --tail=50

# Contract test output (if saved)
cat /tmp/frontend_contract.log
```

## Safety Features

### 1. Idempotency Lock
- Prevents parallel runs
- Location: `/tmp/agi_frontend_fix.lock`
- Auto-released on success
- Manual clear: `rm /tmp/agi_frontend_fix.lock`

### 2. Git Stash Savepoint
- Auto-created before changes
- Name: `AGI fix savepoint YYYYMMDD-HHMMSS`
- Pop with: `git stash pop`

### 3. Guardrails
- Max 2k LOC changes
- 14 step limit
- 15 min timeout
- Path allowlist (NeuroForgeApp only)

### 4. Dry-Run Mode
- Set: `AGI_DRY_RUN=1`
- Or: `make agi-fix-frontend-dry`
- Generates diff without pushing

### 5. Contract Tests
- Auto-runs after fix
- 3 consecutive send cycles
- Metrics verification
- Fail → PR marked "needs triage"

## Troubleshooting

### Preflight Fails

**AGI Core down:**
```bash
docker compose up -d agi-core
curl http://localhost:8000/health
```

**Frontend tools offline:**
```bash
docker compose up -d mcp-frontend-tools
curl http://localhost:8413/tool/xcode_build
```

**LLM path unavailable:**
```bash
docker compose up -d athena-api uai
curl http://localhost:8015/ready
```

### Task Fails

**Check logs:**
```bash
docker compose logs agi-core --tail=100 | grep -i error
```

**Common issues:**
- Tool registry mapping wrong → Check `agi_core/agi_service.py`
- Xcode build fails → Run manually: `xcodebuild -scheme NeuroForgeApp`
- Git push fails → Check credentials: `git push origin feat/agi-fix-frontend`

### Contract Tests Fail

**Run manually:**
```bash
bash tests/frontend_contract.sh
```

**Debug:**
```bash
# Check app launch
open ~/Library/Developer/Xcode/DerivedData/.../NeuroForgeApp.app

# Check metrics manually
curl http://localhost:8015/metrics | grep llm_gateway_calls_total
```

### PR Created But "Still Dumb"

**Update acceptance criteria:**

Edit `agi_frontend_fix_payload.json`:
```json
"acceptance": [
  "Responses use chat-tuned model with temperature ≤ 0.3",
  "System prompt enforces structure (bullets/tables)",
  "Contract re-runs match expected substrings",
  "Gateway metrics show model=qwen2.5-coder or better"
]
```

Then re-run: `make agi-fix-frontend`

## Prometheus Alerts

**High-priority:**
```promql
# Failed tasks
agi_tasks_total{status="failed"} > 0 for 10m

# Stuck execution
rate(agi_steps_total[5m]) == 0 AND agi_tasks_running > 0

# Probe failures
frontend_probe_fail_total > 0
```

**Info-level:**
```promql
# Gateway calls stagnant during task
rate(llm_gateway_calls_total[5m]) == 0 AND agi_tasks_running > 0

# Long execution
agi_task_duration_seconds > 600  # 10 min
```

## Next-Level Hardening

### 1. PR Checklist Bot
```yaml
# .github/workflows/agi-fix-validation.yml
on:
  pull_request:
    branches: [main]
jobs:
  validate:
    if: startsWith(github.head_ref, 'feat/agi-fix-')
    steps:
      - uses: actions/checkout@v3
      - run: bash tests/frontend_contract.sh
      - run: gh pr comment $PR_NUMBER --body "✅ Contract tests PASSED"
```

### 2. Nightly Self-Check
```cron
# crontab -e
0 3 * * * cd /path/to/repo && bash tests/frontend_contract.sh || mail -s "Frontend regressed" you@example.com
```

### 3. Kill Switch Environment Variable
```yaml
# docker-compose.yml
agi-core:
  environment:
    - FEATURE_AGI_AUTOFIX=${FEATURE_AGI_AUTOFIX:-1}
```

Set to 0 to globally disable.

## Cost/Performance

**Typical run:**
- Time: 5-10 minutes
- LLM calls: 30-50
- Steps: 8-12 (of 14 max)
- Tokens: ~20k total

**Resource usage:**
- CPU: Xcode build (90%), AGI minimal
- Memory: <500MB for AGI Core
- Network: Localhost only (no egress)

## Success Metrics

**Track over time:**
- Fix success rate: `agi_tasks_total{status="completed"} / agi_tasks_total`
- Avg execution time: `rate(agi_execution_time_sum) / rate(agi_execution_time_count)`
- Contract test pass rate: `frontend_probe_success / frontend_probe_total`

**Targets:**
- Success rate: >90%
- Execution time: <10 min p95
- Contract pass: 100%

---

**This is production-grade autonomous system healing. Treat it like any other critical automation: observe, measure, improve.** 🧠✨

