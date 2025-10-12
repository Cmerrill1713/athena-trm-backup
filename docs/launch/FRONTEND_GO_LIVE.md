# 🚀 Frontend Go-Live - 10-Minute Checklist

> **Complete end-to-end: Backend + Frontend + Voice**

---

## 0️⃣ **Prereqs (One-Time)**

```bash
cd /Users/christianmerrill/Documents/GitHub
python3 -m pip install -U slowapi anyio
```

Enables rate limiting (429 responses).

---

## 1️⃣ **Bring Up the Stack**

### Option A: Voice
```bash
athena "bring everything online"
athena "enable watchdog"
```

### Option B: Make
```bash
make stack-up
```

### Quick Health Check
```bash
curl -s http://127.0.0.1:8014/ready
curl -s http://127.0.0.1:8090/ready
curl -s http://127.0.0.1:8181/ready
make truth
```

**Expected:**
- All return `{"status": "ready"}`
- `make truth` shows 1 PID per port

---

## 2️⃣ **Observability (Optional)**

```bash
make otel-up  # OTLP collector for traces
```

**Skip if:** Don't need trace collection yet

---

## 3️⃣ **Frontend Wiring**

### Configuration

**API base:** `http://127.0.0.1:8014`  
**WebSocket:** `ws://127.0.0.1:8014/ws` (if used)  
**Auth header:** `Authorization: Bearer supersecret` (if required)  
**CORS:** Already enabled for localhost

### Framework Setup

**Next.js:**
```bash
cd <your-frontend>
echo 'NEXT_PUBLIC_API_BASE=http://127.0.0.1:8014' >> .env.local
npm run dev
```

**Vite:**
```bash
echo 'VITE_API_BASE=http://127.0.0.1:8014' >> .env
npm run dev
```

**React (CRA):**
```bash
echo 'REACT_APP_API_BASE=http://127.0.0.1:8014' >> .env
npm start
```

**Note:** Mic requires secure context (localhost OK, or use HTTPS/ngrok)

---

## 4️⃣ **Text Chat Smoke (UI)**

### In Your Frontend:

1. **Send prompt:** "hello"
2. **Verify streaming:** Tokens appear (if streaming enabled)
3. **Check Network tab:**
   - Look for `x-pid`, `x-build`, `x-mode` headers
   - Proves correct process answering
4. **Chaos test (optional):**
   ```bash
   pkill -f "uvicorn uat.api"
   # Watchdog recovers <60s
   # Chat resumes on retry
   ```

---

## 5️⃣ **Voice Path Smoke**

### In Frontend:
1. **Click mic** → Permission prompt → Allow
2. **Say "hello"** → Transcript appears
3. **TTS playback** → Hear response

### CLI Voice (Optional):
```bash
./athena_voice.sh

# Say:
"what's running"
"run smoke tests"
"ship it"  # Asks confirmation
```

---

## 6️⃣ **Guardrails Check**

### Test Rate Limiting
```bash
make guardrails-smoke
```

**Expected:**
```
 100 200
   5 429  ← Working!
```

**If no 429s:**
```bash
python3 -m pip install slowapi anyio
make stack-restart
make guardrails-smoke
```

---

## 7️⃣ **Proof Loop**

```bash
make tier4-proof
```

**Expected:** All green ✅

---

## 🔍 **Fast Triage (30-Second Fixes)**

| Symptom | Fix |
|---------|-----|
| Frontend 4xx | `export NEXT_PUBLIC_API_BASE=http://127.0.0.1:8014 && npm run dev` |
| CORS error | Bridge already allows localhost; check FE origin |
| 401 errors | `export UAT_TOKEN=supersecret ATH_TOKEN=supersecret && make stack-restart` |
| No 429s | `pip install slowapi anyio && make stack-restart` |
| Mic denied | Use `https://` or localhost (already secure context) |
| No traces | `make otel-up` or `export OTEL_DISABLED=1` |
| Weird state | `make truth` → `make nuke-ports && make stack-up` |

---

## ✅ **Go/No-Go Checklist**

### Text Chat
- [ ] Request/response works
- [ ] Streaming tokens appear
- [ ] Headers show correct PID/build
- [ ] Retry works after service kill

### Voice
- [ ] Mic permission granted
- [ ] ASR transcript appears
- [ ] TTS audio plays

### Guardrails
- [ ] Rate limit returns 429
- [ ] Graceful shutdown: `[Shutdown] Draining for 5s ...`
- [ ] Watchdog recovers within 60s

**All ✅ = Frontend ready!**

---

## 🗣️ **Voice One-Liners**

```
"bring everything online"
"run smoke tests"
"ghost check"
"ship it"
"rollback last deployment"
"snapshot traces"
"tail errors"
"open dashboards"
```

---

## 🎯 **Optional: Production Mode**

```bash
make prod-build
make prod-up

# Grafana: http://localhost:3001
```

---

## 🚀 **After Testing**

**Tell me:**
- **"Works"** - Frontend connected successfully
- **"Issue: X"** - Paste error/logs
- **"Tagged"** - You committed everything
- **"Tier 5"** - Build production delivery

---

**Status:** ✅ READY FOR FRONTEND  
**Guide:** This checklist  
**Next:** Start your FE and test!

🏆 **Voice-controlled autonomous infrastructure.**  
🎙️ **Your frontend can now talk to it.** 🚀

