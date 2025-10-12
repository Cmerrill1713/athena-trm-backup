# 🎯 OPERATOR BATTLE CARD

**Print this. Laminate it. Keep it visible.**

---

## The Ritual (Not a Checklist)

```bash
make stack-up              # Foundation rises
make athena-tests-smoke    # Fast feedback (< 1s)
make athena-tests          # Full validation (< 30s)
make truth                 # Reality check
make stack-down            # Clean exit
```

**Measurable. Observable. Boringly reliable.**

---

## When the World Goes Weird

```bash
make truth                 # What's ACTUALLY running?
make nuke-ports            # Kill all ghosts
make stack-up              # Clean reset
```

**Receipts not vibes. Facts not guesses.**

---

## The Numbers That Matter

```
Commands to start:     1
Services orchestrated: 3
Auth errors:          0
Smoke test time:    0.2s
Full suite time:     23s
Debug by feelings:    NEVER
```

---

## Truth Sources

| When | Command | What It Shows |
|------|---------|---------------|
| **Confused?** | `make truth` | Ports, PIDs, Python, args |
| **Broken?** | `curl -I :8014/health` | Real/mock, breaker state |
| **Failing?** | `tail -f /tmp/*.log` | Service logs |

---

## The Discipline

### ✅ DO
- Run `make truth` first when debugging
- Keep services running during active dev
- Use smoke tests for fast feedback
- Validate before commits

### ❌ DON'T
- Mix manual pytest with orchestration
- Leave ghosts overnight
- Ignore 401s (they indicate issues)
- Skip `make stack-down`

---

## Daily Rhythm

```
Morning:        make stack-up
After changes:  make athena-tests-smoke
Before commit:  make athena-tests
When confused:  make truth
End of day:     make stack-down
```

---

## Emergency Procedures

### Port Conflict
```bash
make nuke-ports && make stack-up
```

### Service Not Responding
```bash
make truth
tail -f /tmp/athena_8090.log
make stack-restart
```

### Tests Failing
```bash
make truth              # Get receipts
make stack-restart      # Fresh start
make athena-tests-smoke # Verify basics
```

---

## Performance Targets

| Operation | Target | Status |
|-----------|--------|--------|
| Stack up | < 10s | ✅ |
| Smoke tests | < 1s | ✅ |
| Full suite | < 30s | ✅ |
| Truth check | < 2s | ✅ |

---

## Status Indicators

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  System: ⚡ Fast               ┃
┃          💤 Boring             ┃
┃          🛡️ Bulletproof        ┃
┃                                ┃
┃  Ghosts:  ☠️ Eliminated        ┃
┃  Auth:    ✅ Zero errors       ┃
┃  Receipts: 🔒 Secured          ┃
┃                                ┃
┃  Status: 👑 OPERATIONAL        ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

---

## The Mantra

**"Receipts not vibes."**

When something breaks, you don't guess.
You run `make truth` and get facts.

---

## Quick Reference

```bash
make help              # All commands
make stack-up          # Start
make athena-tests      # Test
make truth             # Verify
make stack-down        # Stop
```

---

## What This Enables

- **Confident feature dev** — solid foundation
- **Fast feedback loops** — subsecond validation
- **Systematic debugging** — no mysteries
- **Instant onboarding** — one command setup
- **Bulletproof scaling** — foundation won't buckle

---

## The Philosophy

### Fast
Optimize for feedback. No unnecessary waits.

### Boring
Deterministic results. Predictable behavior.

### Bulletproof
Health checks. Token management. Recovery ready.

---

## Critical Paths

### Pre-Commit Checklist
- [ ] `make athena-tests` passes
- [ ] `make truth` shows clean state
- [ ] All services on expected ports
- [ ] Zero 401 errors

### Daily Startup
- [ ] `make stack-up` completes < 10s
- [ ] `make athena-tests-smoke` passes
- [ ] `make truth` shows 3 services
- [ ] Bridge in real mode (not mock)

### Before Deploy
- [ ] Full test suite green
- [ ] Stack validation passes
- [ ] Truth check clean
- [ ] Logs show no errors

---

## Remember

**Boring systems scale.**
**Clever systems break.**

You chose boring.
You chose right.

---

**This is now your normal.**
**Maintain the discipline.** 👑

---

*Fast • Boring • Bulletproof*
*Receipts Not Vibes*
*Built: 2025-10-12*
*Status: OPERATIONAL*
