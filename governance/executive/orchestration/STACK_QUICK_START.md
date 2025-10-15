# Stack Quick Start Guide 🚀

## One-Command Operations

### Start Everything
```bash
make stack-up
```
Starts: UAT (8181) + Athena (8090) + Bridge (8014)

### Run Tests via Athena
```bash
make athena-tests-smoke    # Fast (3 tests, ~0.2s)
make athena-tests-backends # Backend integration
make athena-tests          # Full suite
```

### Validate Stack
```bash
make stack-validate
```
Runs health checks + smoke + backend tests automatically.

### Stop Everything
```bash
make stack-down
```

## Quick Verification

```bash
# Check if everything is up
curl -s http://127.0.0.1:8014/health | jq .status
curl -s http://127.0.0.1:8181/health | jq .status
curl -s http://127.0.0.1:8090/health | jq .status
```

Expected: `"ok"` or `"healthy"` for all three.

## Manual Test Run (Direct to Athena)

```bash
curl -X POST http://127.0.0.1:8090/run_tests \
  -H "Authorization: Bearer supersecret" \
  -H "Content-Type: application/json" \
  -d '{
    "markers": "smoke",
    "maxfail": 10,
    "env": {
      "BRIDGE_BASE": "http://127.0.0.1:8014"
    }
  }' | jq '.summary'
```

## Service Logs

```bash
tail -f /tmp/uat_8181.log
tail -f /tmp/athena_8090.log
tail -f /tmp/bridge_8014.log
```

## Emergency Reset

```bash
make stack-down
lsof -ti:8181,8090,8014 | xargs kill -9
make stack-up
```

## Daily Workflow

```bash
# Morning
make stack-up

# During development
make athena-tests-smoke  # Quick check after changes

# Before commit
make athena-tests        # Full validation

# End of day
make stack-down
```

## CI/CD Integration

```yaml
# .github/workflows/integration.yml
- name: Start Stack
  run: make stack-up

- name: Validate
  run: make stack-validate

- name: Stop Stack
  run: make stack-down
```

## Ports

| Service | Port | Purpose |
|---------|------|---------|
| UAT | 8181 | Universal AI Tools service |
| Athena | 8090 | AI agent + orchestration |
| Bridge | 8014 | NeuroForge adapter |

## Status Check

```bash
make stack-status
```

Shows:
- Process IDs
- Port assignments
- Health status

## Full Command Reference

```bash
make stack-up              # Start full stack
make stack-down            # Stop full stack
make stack-restart         # Restart all
make stack-status          # Show status
make stack-validate        # Run validation suite
make athena-tests          # Full test suite
make athena-tests-smoke    # Quick smoke tests
make athena-tests-backends # Backend tests only
make athena-tests-all      # All tests + full JSON
```

## Success Indicators

✅ All services respond to `/health`
✅ Smoke tests pass (3/3)
✅ Backend tests pass (no 401s)
✅ Bridge shows `"mock_mode": false`

## Troubleshooting

**Port in use:**
```bash
lsof -ti:8181 | xargs kill -9  # Replace 8181 with your port
```

**Service won't start:**
```bash
tail -f /tmp/athena_8090.log  # Check logs
```

**Tests fail with 401:**
```bash
# Verify tokens are set
echo $UAT_TOKEN
echo $ATH_TOKEN
```

---

**Quick Reference:** Save this file to your desktop or bookmark it!
