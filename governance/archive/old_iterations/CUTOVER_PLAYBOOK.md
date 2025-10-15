# Cutover Playbook - Real Mode

## Quick Commands

### Switch to Mock (Safe Mode)
```bash
make bridge-down
USE_MOCK=1 make bridge-up
```

### Switch to Real Mode
```bash
make bridge-down
USE_MOCK=0 UAT_BASE=http://127.0.0.1:8181 ATHENA_BASE=http://127.0.0.1:8090 make bridge-up
```

### Nuclear Option (Kill All Squatters)
```bash
lsof -ti:8014,8181,8090 | xargs -r kill -9
```

---

## Rollback (Half-Asleep Friendly)

If anything goes wrong, this is the panic button:

```bash
# Stop everything
make bridge-down

# Start in safe mock mode
USE_MOCK=1 make bridge-up

# Launch app (still shows traces, just mock data)
cd NeuroForgeApp
API_BASE=http://127.0.0.1:8014 swift run
```

**Result**: Users still see traces. You breathe. System stable.

---

## Verification After Cutover

```bash
# 1. Check mode
curl -s http://127.0.0.1:8014/ | jq '.mock_mode'
# Mock: true = safe mode, false = real mode

# 2. Check source
curl -s http://127.0.0.1:8014/traces | jq '.source'
# mock-mode = mock, uat-real = real UAT data

# 3. Check circuit breaker
curl -s http://127.0.0.1:8014/ | jq '.circuit_breaker'
# is_open: false = healthy, true = degraded
```

---

## Emergency Contacts

**Services**:
- UAT: `http://127.0.0.1:8181`
- Athena: `http://127.0.0.1:8090`
- Bridge: `http://127.0.0.1:8014`

**Logs**:
- UAT: `/tmp/uat_8181.log`
- Athena: `/tmp/athena_8090.log`
- Bridge: `/tmp/bridge_8014.log`

**Kill Switch**: `USE_MOCK=1`

---

## Common Issues

### 401 Errors
```bash
# Check tokens are set
echo $UAT_TOKEN
echo $ATH_TOKEN

# Restart with correct tokens
UAT_TOKEN=supersecret ATH_TOKEN=supersecret ./scripts/real_up.sh
```

### Port Conflicts
```bash
# Kill specific port squatter
kill -9 $(lsof -ti:8181)

# Or use the nuclear option
lsof -ti:8014,8181,8090 | xargs -r kill -9
```

### Circuit Breaker Open
```bash
# Check breaker state
curl -s http://127.0.0.1:8014/ | jq '.circuit_breaker'

# If open, either:
# 1. Fix backend and wait 30s for auto-recovery
# 2. Or flip to mock mode temporarily
```

---

## Pre-Cutover Checklist

- [ ] Verify all services healthy: `./scripts/real_up.sh`
- [ ] Smoke test passes: `make smoke`
- [ ] Real data flowing: Check source = "uat-real"
- [ ] Backup current state: `cp -r /tmp/*_{8181,8090,8014}.log backups/`
- [ ] Rollback plan understood
- [ ] Stakeholders notified

## Post-Cutover Checklist

- [ ] Services responding
- [ ] Real mode confirmed
- [ ] No errors in logs
- [ ] App connects successfully
- [ ] Circuit breaker closed
- [ ] Monitor for 15 minutes

---

**Last Updated**: 2025-10-12
**Owner**: Platform Team
**Escalation**: See RUNBOOKS/POSTMORTEM.md template
