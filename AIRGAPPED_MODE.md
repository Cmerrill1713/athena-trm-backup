# 🔒 Air-Gapped Mode — Maximum Network Isolation

**Provably offline RAG system with internal-only Docker network and egress blocking.**

---

## 🎯 What Is Air-Gapped Mode?

**Standard Offline Mode:**

- Services can't pull from internet (no Docker Hub access)
- Local volumes only
- No external API calls in code

**Air-Gapped Mode (This):**

- ✅ **Internal Docker network** — Core services isolated
- ✅ **Egress blocking** — Adapter uses iptables to block outbound
- ✅ **Provable isolation** — Validation tests external connectivity
- ✅ **DNS blocked** — No name resolution to public domains
- ✅ **No model pulls** — `OLLAMA_OFFLINE=1`

---

## 🚀 Quick Start

### Step 1: Create Internal Network

```bash
# One-time setup: Create isolated internal network
docker network create --internal rag_core_nw
```

### Step 2: Deploy Air-Gapped Stack

```bash
cd /Users/christianmerrill/Documents/GitHub

# Restore corpus (if not done)
cp -r /Volumes/Untitled/docker-data/volumes/weaviate_data/* \
  volumes/weaviate_data/

# Start air-gapped stack
docker-compose -f docker-compose.airgapped.yml up -d

# Wait for health
sleep 30
```

### Step 3: Validate Air-Gap

```bash
# Run offline validation (includes air-gap checks)
make offline
```

**Expected:**

```
🔒 Air-Gap Validation (Provable No Internet)

1. DNS to public domains blocked... ✅
2. Adapter cannot reach public internet... ✅
3. No connections to external IPs... ✅

✅ OFFLINE VALIDATION PASSED
```

### Step 4: Use Local UI

```bash
# Serve UI
cd ui && python3 -m http.server 8080

# Open browser
open http://localhost:8080/athena-chat.html
```

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────┐
│  Host Network (Your Computer)            │
│                                           │
│  ┌────────────────────────────────────┐  │
│  │  Edge Network (bridge)             │  │
│  │                                     │  │
│  │  ┌──────────────────┐              │  │
│  │  │ OpenAI Adapter   │ Port 3000 ← UI  │
│  │  │ (iptables egress │              │  │
│  │  │  blocking)       │              │  │
│  │  └────────┬─────────┘              │  │
│  └───────────┼─────────────────────────┘  │
│              │                            │
│  ┌───────────┼─────────────────────────┐  │
│  │           ↓                         │  │
│  │  Internal Network (rag_core)       │  │
│  │  🔒 No Egress — Internal Only      │  │
│  │                                     │  │
│  │  ┌──────────┐  ┌───────────┐      │  │
│  │  │ Weaviate │  │  Ollama   │      │  │
│  │  └──────────┘  └───────────┘      │  │
│  │                                     │  │
│  │  ┌──────────┐  ┌───────────┐      │  │
│  │  │   RAG    │  │   Smart   │      │  │
│  │  │ Gateway  │  │   Chat    │      │  │
│  │  └──────────┘  └───────────┘      │  │
│  └─────────────────────────────────────┘  │
└──────────────────────────────────────────┘

❌ PUBLIC INTERNET (Blocked)
```

---

## 🔒 Isolation Mechanisms

### 1. Internal Docker Network

**Created with:**

```bash
docker network create --internal rag_core_nw
```

**Effect:**

- Core services (Weaviate, Ollama, RAG Gateway, Smart Chat) **cannot** reach internet
- No egress routing configured
- Network is isolated at Docker daemon level

### 2. Adapter Egress Blocking (iptables)

**Applied in:** `services/openai-compat/entrypoint.sh`

```bash
# Default: DROP all outbound
iptables -P OUTPUT DROP

# Allow: Local subnets only
iptables -A OUTPUT -d 127.0.0.0/8   -j ACCEPT  # localhost
iptables -A OUTPUT -d 172.16.0.0/12 -j ACCEPT  # Docker
iptables -A OUTPUT -d 10.0.0.0/8    -j ACCEPT  # Private
iptables -A OUTPUT -d 192.168.0.0/16 -j ACCEPT # Private
```

**Requires:** `NET_ADMIN` capability (added in compose)

### 3. Model Pull Prevention

```env
OLLAMA_OFFLINE=1  # Prevents Ollama from pulling models
```

### 4. Weaviate Client-Side Embeddings

```env
DEFAULT_VECTORIZER_MODULE=none  # No server-side vectorizer (no HF pulls)
```

---

## ✅ Validation Tests

### Automated (make offline)

```bash
make offline
```

**Tests:**

1. Weaviate data present
2. Services start successfully
3. Adapter health check
4. Models endpoint working
5. Non-streaming completion
6. Streaming (SSE)
7. **DNS to public domains blocked**
8. **Adapter cannot reach 1.1.1.1**
9. **No established connections to external IPs**

### Manual (Network Tab)

1. Open http://localhost:8080/athena-chat.html
2. Open DevTools → Network tab
3. Send a chat message
4. **Verify:** Only see `localhost:3000` requests
5. **No calls to:** openai.com, anthropic.com, googleapis.com, huggingface.co

### Advanced (Fetch Monitor)

Paste in DevTools console:

```javascript
// Monitor all fetch calls
(function () {
  const originalFetch = window.fetch;
  window.fetch = function (...args) {
    console.log("🔍 FETCH:", args[0]);
    if (!args[0].startsWith("http://localhost:")) {
      console.error("❌ EXTERNAL CALL BLOCKED:", args[0]);
      throw new Error("External calls not allowed in air-gapped mode");
    }
    return originalFetch.apply(this, args);
  };
})();

// Now try chatting — any external call will throw error
```

---

## 🎯 Comparison: Standard vs Air-Gapped

| Feature                    | Standard Offline | Air-Gapped Mode |
| -------------------------- | ---------------- | --------------- |
| Local volumes              | ✅               | ✅              |
| No cloud APIs in code      | ✅               | ✅              |
| Internal Docker network    | ❌               | ✅              |
| Egress blocking (iptables) | ❌               | ✅              |
| DNS blocking               | ❌               | ✅              |
| Provable isolation         | ❌               | ✅              |
| NET_ADMIN required         | ❌               | ✅              |

**Use Air-Gapped Mode for:**

- Classified/sensitive environments
- HIPAA/SOC2 compliance
- Zero-trust requirements
- Government/defense
- Paranoid mode 🔒

---

## 🔧 Configuration

### Enable Air-Gapped Mode

```bash
# Use air-gapped compose file
docker-compose -f docker-compose.airgapped.yml up -d
```

### Disable Air-Gapped Mode

```bash
# Use standard compose file (still offline, but no iptables)
docker-compose -f docker-compose.full-stack.yml up -d \
  weaviate ollama rag-gateway smart-chat openai-compat
```

---

## 🧪 Test Egress Blocking

### From Inside Adapter Container

```bash
# Should FAIL (egress blocked)
docker exec openai-compat curl -sS --max-time 2 http://google.com
docker exec openai-compat wget -q --timeout=2 http://1.1.1.1 -O-

# Should SUCCEED (local backend)
docker exec openai-compat curl -sS http://rag-gateway:8090/health
docker exec openai-compat curl -sS http://smart-chat:8088/health
```

### From Inside Core Services

```bash
# Should FAIL (internal network has no egress)
docker exec rag-gateway curl -sS --max-time 2 http://google.com
docker exec smart-chat curl -sS --max-time 2 http://1.1.1.1
```

---

## 🛠️ Troubleshooting

### "Permission denied" for iptables

**Cause:** Container lacks `NET_ADMIN` capability

**Fix:** Already added in `docker-compose.airgapped.yml`:

```yaml
cap_add:
  - NET_ADMIN
```

### Services can't reach each other

**Cause:** Wrong network configuration

**Fix:** Ensure adapter is on BOTH networks:

```yaml
networks:
  - rag_core # Internal (backend access)
  - edge # External (UI access)
```

### DNS resolution fails for Docker services

**Cause:** Internal network blocks Docker DNS

**Fix:** Allow Docker DNS in iptables (already in entrypoint.sh):

```bash
iptables -A OUTPUT -p udp --dport 53 -d 127.0.0.11 -j ACCEPT
```

---

## 📊 Compliance Benefits

### Zero-Trust Architecture

✅ **Network segmentation** — Core services isolated  
✅ **Egress deny-by-default** — Explicit allowlist only  
✅ **Principle of least privilege** — Adapter is only bridge  
✅ **Defense in depth** — Code + network + container isolation

### Audit Trail

```bash
# Prove no internet access
make offline > audit-proof-$(date +%Y%m%d).txt

# Store as compliance evidence
```

### Compliance Frameworks

| Framework      | Requirement          | Implementation       |
| -------------- | -------------------- | -------------------- |
| **SOC 2**      | Data isolation       | ✅ Internal network  |
| **HIPAA**      | No data egress       | ✅ Egress blocking   |
| **ISO 27001**  | Network segmentation | ✅ Separate networks |
| **FedRAMP**    | Air-gapped option    | ✅ Full isolation    |
| **Zero Trust** | Deny by default      | ✅ iptables DROP     |

---

## 🎯 When to Use Air-Gapped Mode

### ✅ Use Air-Gapped Mode If:

- Handling classified/sensitive data
- Compliance requires provable isolation (HIPAA, SOC 2)
- Zero-trust security posture
- Government/defense deployment
- Maximum paranoia required 🔒

### ❌ Standard Offline Mode Is Fine If:

- Personal use
- Internal company knowledge base
- General development
- Testing and prototyping

**Both modes are 100% local and offline — air-gapped just adds provable network isolation.**

---

## 🎉 Success!

**You now have the option of:**

**Standard Offline:**

```bash
docker-compose -f docker-compose.full-stack.yml up -d \
  weaviate ollama rag-gateway smart-chat openai-compat
```

**Air-Gapped (Maximum Isolation):**

```bash
docker network create --internal rag_core_nw
docker-compose -f docker-compose.airgapped.yml up -d
```

**Both are 100% offline. Air-gapped adds network-level isolation and egress blocking.**

---

**Validate with:** `make offline`  
**Use:** http://localhost:8080/athena-chat.html  
**Monitor:** http://localhost:3000/metrics

**Your data never leaves your infrastructure.** 🔒✅

---

**Last Updated:** October 18, 2025  
**Security Level:** Maximum (Air-Gapped)  
**Status:** ✅ Compliance-Ready
