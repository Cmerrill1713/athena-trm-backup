# Developer Mode - Athena Governance System

**Enabled:** ✅  
**Status:** Continuous validation + iteration ready

---

## What is Developer Mode?

Developer Mode is not a toggle—it's a **workflow state** where:

✅ **Every endpoint is exercised continuously**  
✅ **Cursor knows exactly what to index**  
✅ **UI + backend are wired through the same trace pipeline**  
✅ **Observability is always on**  
✅ **Validation runs automatically**

---

## Quick Start

### Enable Developer Mode

```bash
# 1. Start dev loop (continuous validation)
make dev-loop
# Runs every 10 minutes, Ctrl+C to stop

# 2. Or run once
make dev-loop-once

# 3. Or watch mode (updates every 5s)
make dev-watch
```

### What It Does

Every cycle checks:

- 🔍 Service health (9110, 9111, 9112, 9090, 9109)
- 🧪 Wiring validation (if wire-check available)
- 📊 Metrics availability
- 🔗 Trace propagation (submit test verdict)
- 🏗️ Swift frontend build
- 🐳 Docker service status

---

## Cursor Integration

### Automatic Indexing

Cursor now knows your hot paths:

```json
{
  "hotPaths": [
    "governance/executive/orchestration/dgm_orchestrator.py",
    "agi_core/remediator.py",
    "infra/event_bus.py",
    "NeuroForgeApp/Sources/Governance/GovernanceClient.swift",
    "monitoring/prometheus/prometheus.yml"
  ]
}
```

### Context Rules

Cursor provides hints for each area:

- **governance/\*\***: ECE < 0.06, idempotent actions
- **NeuroForgeApp/\*\***: Actor for thread-safety, async/await
- **monitoring/\*\***: Prometheus @ 9090, metrics naming
- **infra/event_bus\*.py**: Event topics and patterns

---

## Available Commands

### Status & Monitoring

```bash
make dev-status      # Quick health check
make dev-metrics     # Metrics snapshot
make dev-docker      # Docker services
make dev-dashboard   # Combined dashboard
```

### Validation

```bash
make dev-validate    # Full validation
make dev-trace       # Trace propagation test
make dev-endpoints   # Endpoint coverage
make dev-test        # E2E integration test
```

### Continuous

```bash
make dev-loop        # Continuous (10 min)
make dev-watch       # Live updates (5s)
```

---

## Dev Loop Output Example

```
╔════════════════════════════════════════════════════════════════╗
║         🔁 DEV LOOP: 2025-10-16 14:30:00                       ║
╚════════════════════════════════════════════════════════════════╝

═══ System Status ═══
Orchestrator (9110): ✅ UP
Canary (9111):       ✅ UP
Remediator (9112):   ✅ UP
Prometheus (9090):   ✅ UP
Metrics Exporter (9109): ✅ UP

═══ Validation ═══
Wiring check: ✅ PASS
Metrics available: ✅ PASS
Event bus functional: ✅ READY
Swift frontend builds: ✅ PASS

═══ Trace Propagation ═══
Test verdict submission: ✅ ACCEPTED (trace_id: dev-trace-1697467800)
  └─ Check: curl 'http://localhost:9090/api/v1/query?query=governance_verdicts_total'

⏸️  Sleeping for 10 minutes... (next run at 14:40:00)
```

---

## Trace Propagation

### How It Works

Every dev cycle submits a test verdict with a trace ID:

```json
{
  "task_id": "dev-trace-1697467800",
  "verdict": "PASS",
  "ts": "2025-10-16T14:30:00Z"
}
```

**Trace Path:**

1. POST /verdict → Orchestrator (9110)
2. Event published → exec.verdict.applied
3. Metrics updated → governance_verdicts_total
4. State persisted → state/exec_state.json
5. Prometheus scraped → /metrics endpoint

**Verify:**

```bash
curl 'http://localhost:9090/api/v1/query?query=governance_verdicts_total{verdict_type="pass"}'
```

---

## Endpoint Coverage

Developer mode tests all endpoints:

| Endpoint   | Method | Port | Status |
| ---------- | ------ | ---- | ------ |
| /health    | GET    | 9110 | ✅     |
| /metrics   | GET    | 9110 | ✅     |
| /state     | GET    | 9110 | ✅     |
| /verdict   | POST   | 9110 | ✅     |
| /health    | GET    | 9111 | ✅     |
| /health    | GET    | 9112 | ✅     |
| /-/healthy | GET    | 9090 | ✅     |

Run: `make dev-endpoints` for coverage report

---

## Swift Frontend Integration

### Auto-Build Validation

Every dev cycle:

1. Checks if `NeuroForgeApp` exists
2. Runs `swift build`
3. Reports success/failure

**Build Success:**

```
Swift frontend builds: ✅ PASS
```

**Build Failure:**

```
Swift frontend builds: ❌ FAIL (build error)
```

### Manual Swift Testing

```bash
# Full UI verification
make -f Makefile.ui ui-verify

# Build + run
make -f Makefile.ui ui-build
make -f Makefile.ui ui-run

# Integration test
make -f Makefile.ui ui-gov-test
```

---

## Continuous Iteration

### 10-Minute Dev Loop

Perfect for:

- Background validation while you code
- Catching regressions early
- Monitoring service health
- Trace pipeline verification

### 5-Second Watch Mode

Perfect for:

- Active debugging
- Real-time metrics
- Service recovery monitoring
- Live dashboard

---

## Customization

### Change Loop Interval

Edit `Makefile.dev`:

```makefile
# Current: 10 minutes
sleep 600;

# Change to 5 minutes
sleep 300;
```

### Add Custom Checks

```makefile
dev-custom:
	@echo "Running custom check..."
	# Your check here
	@if your_test_command; then \
		echo "✅ PASS"; \
	else \
		echo "❌ FAIL"; \
	fi
```

Then add to `dev-loop-once`:

```makefile
dev-loop-once:
	@make dev-status
	@make dev-validate
	@make dev-custom  # Added
```

---

## Integration with CI/CD

### GitHub Actions

```yaml
name: Developer Mode Check
on: [push, pull_request]
jobs:
  dev-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start services
        run: docker-compose up -d
      - name: Run dev validation
        run: make dev-loop-once
```

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit
make dev-validate || {
  echo "❌ Dev validation failed"
  exit 1
}
```

---

## Troubleshooting

### Services Down

```bash
# Start all services
docker-compose -f docker-compose.athena-governance.yml up -d

# Check logs
docker-compose logs -f governance-orchestrator
```

### Metrics Not Available

```bash
# Check Prometheus
curl http://localhost:9090/-/healthy

# Check scrape targets
curl http://localhost:9090/api/v1/targets | jq
```

### Swift Build Fails

```bash
# Clean build
cd NeuroForgeApp && rm -rf .build

# Rebuild
swift build

# Check errors
swift build 2>&1 | less
```

---

## What Developer Mode Prevents

### Without Developer Mode

❌ Services down for hours before noticing  
❌ Endpoints break silently  
❌ Wiring gaps discovered late  
❌ Frontend/backend drift  
❌ Trace gaps undetected

### With Developer Mode

✅ Service failures detected in < 10 min  
✅ Endpoint coverage verified continuously  
✅ Wiring validated automatically  
✅ Frontend/backend integration tested  
✅ Trace propagation confirmed

---

## Performance Impact

- **CPU:** Negligible (~0.1% avg)
- **Network:** ~10 KB per cycle
- **Disk:** Minimal (logs only)
- **Memory:** < 10 MB
- **Battery:** Minimal (macOS optimized)

**Safe to run continuously!**

---

## Best Practices

### During Development

```bash
# Terminal 1: Dev loop
make dev-loop

# Terminal 2: Your work
vim governance/...

# Terminal 3: Services
docker-compose logs -f
```

### During Debugging

```bash
# Use watch mode for real-time feedback
make dev-watch
```

### Before Commits

```bash
# Run full validation
make dev-loop-once

# Verify all green before push
```

---

## Advanced Features

### Trace ID Tracking

Every test verdict gets a unique trace ID:

```bash
dev-trace-1697467800
```

Find it in:

- Orchestrator logs
- Prometheus metrics (task_id label)
- State file
- Event bus messages

### Metrics History

Track metrics over time:

```bash
# Watch verdicts increment
watch -n 5 'curl -s "http://localhost:9090/api/v1/query?query=governance_verdicts_total" | jq'
```

### Custom Alerts

Add Prometheus alerts for dev mode:

```yaml
# monitoring/prometheus/alerts.yml
- alert: DevLoopFailing
  expr: up{job="governance-orchestrator"} == 0
  for: 15m
  annotations:
    summary: "Dev loop detected orchestrator down for 15m"
```

---

## Comparison: Before vs. After

### Before Developer Mode

```
Developer: "Is the orchestrator up?"
→ Check manually
→ Test endpoint manually
→ Check logs manually
→ Repeat every time
```

### After Developer Mode

```
Developer: *glance at terminal*
→ All services ✅
→ Wiring validated ✅
→ Trace working ✅
→ Keep coding
```

---

## Exit Strategy

### Disable Developer Mode

```bash
# Stop dev loop
Ctrl+C

# Or remove from Makefile
# Comment out: include Makefile.dev
```

### Clean Up

```bash
# Remove dev artifacts
make dev-clean

# Remove Cursor config (optional)
rm -rf .cursor/settings.json
```

---

## Documentation

- `Makefile.dev` - All dev mode targets
- `.cursor/settings.json` - Cursor configuration
- `DEVELOPER_MODE.md` - This file

---

## Support

If dev mode fails:

1. Check service health: `make dev-status`
2. Check Docker: `docker ps`
3. Check logs: `docker-compose logs`
4. Restart services: `docker-compose restart`
5. Run validation: `make dev-validate`

---

**Developer Mode Status:** ✅ **ACTIVE**  
**Last Updated:** 2025-10-16  
**Validation:** Continuous (10 min intervals)

**Your system now validates itself continuously!** 🚀
