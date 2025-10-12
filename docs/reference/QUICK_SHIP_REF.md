# 🚀 Quick Ship Reference Card

**One-page guide for day-to-day operations**

---

## 🎯 Daily Operations

### Start Everything
```bash
./scripts/real_up.sh
# or
make real-up
```

### Stop Everything
```bash
./scripts/real_down.sh
# or
make real-down
```

### Quick Health Check
```bash
./scripts/acceptance_test.sh
# or
make smoke
```

---

## 🔍 Status Checks

### Service Health
```bash
curl http://127.0.0.1:8014/health  # Bridge
curl http://127.0.0.1:8181/health  # UAT
curl http://127.0.0.1:8090/health  # Athena
```

### Observability Headers
```bash
curl -I http://127.0.0.1:8014/health | grep "X-Mode\|X-Breaker"
# X-Mode: real (or mock)
# X-Breaker: closed (or open/half-open)
```

### Trace Count
```bash
curl -s http://127.0.0.1:8014/traces | jq 'length'
# Expected: 170+
```

---

## 🧪 Testing

### Quick Smoke
```bash
make smoke
```

### Contract Tests
```bash
cd AI-Projects/universal-ai-tools
pytest tests/test_contract.py -v
```

### Integration Tests (fast)
```bash
pytest tests/test_integration.py -v -m "not slow"
```

### Full Suite
```bash
pytest tests/ -v
```

---

## 🚨 Emergency Procedures

### Rollback to Mock (30 seconds)
```bash
make bridge-down
USE_MOCK=1 make bridge-up
./scripts/acceptance_test.sh
```

### Kill Port Squatters
```bash
lsof -ti:8014,8181,8090 | xargs -r kill -9
```

### Nuclear Restart
```bash
make real-down
sleep 2
lsof -ti:8014,8181,8090 | xargs -r kill -9
./scripts/real_up.sh
```

---

## 📊 Monitoring

### Logs
```bash
# Bridge
tail -f /tmp/bridge_8014.log

# UAT
tail -f /tmp/uat_8181.log

# Athena
tail -f /tmp/athena_8090.log

# All together
tail -f /tmp/{bridge_8014,uat_8181,athena_8090}.log
```

### Error Scan
```bash
grep -i error /tmp/bridge_8014.log | tail -n 20
```

### Latency Check
```bash
for i in {1..10}; do
  curl -w "%{time_total}\n" -o /dev/null -s http://127.0.0.1:8014/traces
done
```

---

## 🔧 Troubleshooting

### 401 Errors
```bash
# Check tokens
echo $UAT_TOKEN $ATH_TOKEN

# Re-export and restart
export UAT_TOKEN=<token>
export ATH_TOKEN=<token>
make bridge-down
make bridge-up
```

### Stuck in Mock Mode
```bash
# Kill old processes
make bridge-down
lsof -ti:8014 | xargs -r kill -9

# Start fresh
USE_MOCK=0 make bridge-up

# Verify
curl -I http://127.0.0.1:8014/health | grep X-Mode
```

### Breaker Won't Close
```bash
# Check backend health
curl http://127.0.0.1:8181/health
curl http://127.0.0.1:8090/health

# If healthy, restart bridge
make bridge-down
make bridge-up
```

### Port Conflicts
```bash
# Find squatter
lsof -iTCP:8014 -sTCP:LISTEN  # or 8181, 8090

# Kill by PID
kill -9 <PID>

# Or nuclear
lsof -ti:8014 | xargs -r kill -9
```

---

## 🎮 Environment Modes

### Development (Mock)
```bash
ENV=dev USE_MOCK=1 make bridge-up
```

### Staging (Real)
```bash
ENV=staging USE_MOCK=0 \
UAT_BASE=http://127.0.0.1:8181 \
ATHENA_BASE=http://127.0.0.1:8090 \
make bridge-up
```

### Production
```bash
ENV=prod USE_MOCK=0 \
UAT_BASE=https://uat.yourdomain:8181 \
ATHENA_BASE=https://athena.yourdomain:8090 \
UAT_TOKEN=<prod-secret> \
ATH_TOKEN=<prod-secret> \
make bridge-up
```

---

## 📈 Performance Checks

### p95 Latency
```bash
for i in {1..100}; do
  curl -w "%{time_total}\n" -o /dev/null -s http://127.0.0.1:8014/traces
done | sort -n | awk 'NR==95 {print "p95: "$1"s"}'
```

### Load Test (5 minutes)
```bash
hey -z 5m -q 3.33 -c 10 http://127.0.0.1:8014/traces
```

---

## 🔐 Security

### Token Rotation
```bash
# Generate new token
NEW_TOKEN=$(openssl rand -base64 32)

# Update env
export UAT_TOKEN=$NEW_TOKEN

# Restart
make bridge-down
make bridge-up

# Verify
./scripts/acceptance_test.sh
```

### Check for Leaked Secrets
```bash
grep -rE '(Bearer|token|secret|password).{0,50}' /tmp/*.log | grep -v '***'
# Should be empty or only show redacted
```

---

## 🎯 One-Liners

```bash
# Full health check
curl -s http://127.0.0.1:8014/health && echo "✅ Bridge OK" || echo "❌ Bridge DOWN"

# Trace validation
curl -s http://127.0.0.1:8014/traces | jq 'if length >= 170 then "✅ Traces OK" else "❌ Missing traces" end'

# Auth test
curl -s http://127.0.0.1:8014/traces | jq -e '.[0]' && echo "✅ Auth OK" || echo "❌ Auth FAIL"

# Breaker status
curl -sI http://127.0.0.1:8014/health | grep -i x-breaker | awk '{print $2}'

# Mode check
curl -sI http://127.0.0.1:8014/health | grep -i x-mode | awk '{print $2}'
```

---

## 📋 Checklists

### Morning Startup
- [ ] Run `./scripts/real_up.sh`
- [ ] Wait 5 seconds
- [ ] Run `./scripts/acceptance_test.sh`
- [ ] Check `X-Mode: real` and `X-Breaker: closed`
- [ ] Launch app: `API_BASE=http://127.0.0.1:8014 swift run`

### Pre-Deploy
- [ ] All tests pass: `pytest tests/ -v`
- [ ] Acceptance green: `./scripts/acceptance_test.sh`
- [ ] Rollback drill: < 30 seconds
- [ ] Tag: `git tag -a bridge-X.Y.Z`
- [ ] Push: `git push --tags`

### Post-Incident
- [ ] Identify root cause
- [ ] Document in `RUNBOOKS/POSTMORTEM.md`
- [ ] Add test to prevent recurrence
- [ ] Update this card if new procedure discovered

---

## 🆘 Who to Call

| Issue | Action | Contact |
|-------|--------|---------|
| Services won't start | Check port conflicts | Platform Team |
| 401 errors | Token rotation | Security Team |
| High latency | Check backend health | Ops Team |
| Data integrity | Verify backups | Data Team |
| CI failures | Check logs | DevOps Team |

---

## 📚 Documentation

- **Full Guide**: `GO_LIVE_GUIDE.md`
- **Integration Tests**: `INTEGRATION_TESTS_COMPLETE.md`
- **Real Mode Setup**: `REAL_MODE_COMPLETE.md`
- **Runbooks**: `RUNBOOKS/*.md`
- **Ship Log**: `SHIPLOG.md`

---

## 🎓 Quick Wins

**Fastest debug**: Check observability headers
```bash
curl -I http://127.0.0.1:8014/health
```

**Fastest rollback**: Flip to mock
```bash
USE_MOCK=1 make bridge-up
```

**Fastest validation**: Acceptance test
```bash
./scripts/acceptance_test.sh
```

---

**Last Updated**: 2025-10-12
**Version**: bridge-1.0.0
**Owner**: Platform Team

🚀 **Keep calm and ship it.**
