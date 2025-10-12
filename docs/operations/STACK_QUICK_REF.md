# Stack Quick Reference

## One-Liners

```bash
# Start everything (real mode)
make stack-up

# Have Athena run the tests and report back
make athena-tests

# Tear it all down
make stack-down
```

## Services

| Service | Port | Auth Token | Purpose |
|---------|------|------------|---------|
| UAT | 8181 | `supersecret` | Orchestration |
| Athena | 8090 | `supersecret` | Agents + Tools |
| Bridge | 8014 | (optional) | Adapter |

## Quick Health Check

```bash
# All services via bridge
curl -s http://127.0.0.1:8014/health | jq .

# Individual
curl -s -H "Authorization: Bearer supersecret" http://127.0.0.1:8181/health
curl -s -H "Authorization: Bearer supersecret" http://127.0.0.1:8090/health
```

## Athena Tools

```bash
# Run tests
curl -X POST http://127.0.0.1:8090/run_tests \
  -H "Authorization: Bearer supersecret" \
  -H "Content-Type: application/json" \
  -d '{"markers":"smoke"}'

# Execute command
curl -X POST http://127.0.0.1:8090/tool_call \
  -H "Authorization: Bearer supersecret" \
  -H "Content-Type: application/json" \
  -d '{"tool":"run_command","params":{"command":"ls -la"}}'

# Read file
curl -X POST http://127.0.0.1:8090/tool_call \
  -H "Authorization: Bearer supersecret" \
  -H "Content-Type: application/json" \
  -d '{"tool":"read_file","params":{"path":"README.md","max_lines":20}}'
```

## Log Locations

```bash
logs/uat_8181.log
logs/athena_8090.log
logs/bridge_8014.log
```

## PID Files

```bash
.stack/uat.pid
.stack/athena.pid
.stack/bridge.pid
```

## Troubleshooting

```bash
# Kill ports
lsof -ti:8014,8181,8090 | xargs kill -9

# View logs
tail -f logs/*.log

# Check PIDs
cat .stack/*.pid | xargs ps -p
```

## Environment Overrides

```bash
# Custom ports
UAT_PORT=9181 ATH_PORT=9090 BRIDGE_PORT=9014 make stack-up

# Different tokens
UAT_TOKEN=mytoken ATH_TOKEN=mytoken make stack-up
```

## Complete Flow

```bash
# 1. Start stack
make stack-up

# 2. Check status
make stack-status

# 3. Run tests via Athena
make athena-tests

# 4. Launch app (optional, new terminal)
API_BASE=http://127.0.0.1:8014 QA_MODE=1 swift run

# 5. Stop stack
make stack-down
```

---

**Full docs:** [STACK_MANAGEMENT_GUIDE.md](./STACK_MANAGEMENT_GUIDE.md)
