# 🚀 Real Mode - Quick Reference Card

## One-Command Operations

```bash
# Start everything (clean, handles conflicts)
./scripts/real_up.sh

# Stop everything
./scripts/real_down.sh

# Or use Make
make real-up
make real-down
```

## Services & Ports

| Service | Port | Auth | Endpoint |
|---------|------|------|----------|
| UAT     | 8181 | Bearer | `http://127.0.0.1:8181` |
| Athena  | 8090 | Bearer | `http://127.0.0.1:8090` |
| Bridge  | 8014 | None   | `http://127.0.0.1:8014` |

**Token**: `supersecret` (default)

## Quick Tests

```bash
# 1. Check real mode is active
curl -s http://127.0.0.1:8014/ | jq '.mock_mode'
# Should return: false

# 2. Get traces (170 items from UAT)
curl -s http://127.0.0.1:8014/traces | jq '.source, .count'
# Should return: "uat-real", 170

# 3. Test chat with routing
curl -s -X POST http://127.0.0.1:8014/chat \
  -H 'content-type: application/json' \
  -d '{"text":"review my code"}' | jq '.route'
# Should return: "code-agent"

# 4. Verify auth enforcement
curl -s http://127.0.0.1:8181/traces
# Should return: 401 Unauthorized
```

## Launch NeuroForge App

```bash
cd NeuroForgeApp
API_BASE=http://127.0.0.1:8014 QA_MODE=1 swift run
```

## Troubleshooting

```bash
# Check what's running
lsof -i:8181 -i:8090 -i:8014

# View logs
tail -f /tmp/uat_8181.log
tail -f /tmp/athena_8090.log
tail -f /tmp/bridge_8014.log

# Clean restart
./scripts/real_down.sh
sleep 2
./scripts/real_up.sh
```

## Port Conflicts?

```bash
# Use different UAT port
UAT_PORT=8282 ./scripts/real_up.sh

# Kill specific squatter
kill -9 $(lsof -ti:8080)
```

## Success Indicators

✅ `real_up.sh` output shows:
- "✅ UAT responding"
- "✅ Athena responding"
- "✅ Bridge in REAL mode"
- "✅ REAL MODE ACTIVE - ALL GREEN!"

✅ Bridge shows `mock_mode: false`
✅ Traces source is `"uat-real"`
✅ Auth returns 401 without token

## Files

- **Services**: `uat/api.py`, `athena/api.py`, `bridge.py`
- **Scripts**: `scripts/real_up.sh`, `scripts/real_down.sh`
- **Logs**: `/tmp/uat_8181.log`, `/tmp/athena_8090.log`, `/tmp/bridge_8014.log`
- **Docs**: `REAL_MODE_COMPLETE.md`, `REAL_MODE_STATUS.md`

---

**Status**: 🟢 Live | **Docs**: `REAL_MODE_COMPLETE.md`
