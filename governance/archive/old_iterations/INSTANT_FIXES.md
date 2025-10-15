# 🛠️ INSTANT FIXES - No Thinking Required

> **Copy-paste fixes for common issues**

---

## 🔴 Meta Panel Missing

```bash
export META_PROMPTING=1 && make stack-restart
```

---

## 🔴 Voice Silent

```bash
curl -fsS http://127.0.0.1:8020/health || python3 scripts/kokoro_server.py
```

---

## 🔴 No 429s in Guardrail Test

```bash
python3 -m pip install slowapi anyio && make stack-restart
```

---

## 🔴 Swift Build Hiccup

```bash
cd NeuroForgeApp
swift package resolve
swift build --clean-build
```

---

## 🔴 CORS / Base URL Mismatch

**Confirm frontend env:**
```bash
echo $API_BASE  # Should be: http://127.0.0.1:8014
```

**If using localhost, keep consistent:**
- Bridge: `http://localhost:8014`
- Frontend: `API_BASE=http://localhost:8014`

---

## 🔴 Auth Wobble (401)

```bash
export UAT_TOKEN=supersecret ATH_TOKEN=supersecret
make stack-restart
```

---

## 🔴 Ghosts (Multiple PIDs)

```bash
make nuke-ports
make stack-up
make truth
```

---

## 🔴 Hard Reset (10 sec)

**Nuclear option if anything feels off:**
```bash
make stack-down
make nuke-ports
make stack-up
make truth
```

---

## 🔍 Quick Verifications

### Health Probes
```bash
curl -fsS http://127.0.0.1:8014/ready
curl -fsS http://127.0.0.1:8014/metrics | head
```

### Meta Headers
```bash
curl -fsI http://127.0.0.1:8014/health | grep x-
```

### Watch Logs Live
```bash
tail -f logs/*.log | grep -i error
```

### WebSocket (if used)
```bash
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Key: test==" \
  http://127.0.0.1:8014/ws || true
```

---

## ✅ After Fixing

**Re-run green lights:**
```bash
./GREEN_LIGHTS.sh
```

**Or minimal check:**
```bash
make truth
curl -fsS http://127.0.0.1:8014/ready
```

---

**All fixes are < 30 seconds.** ⚡

