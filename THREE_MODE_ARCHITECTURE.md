# 🎯 Three-Mode Architecture — Flexibility + Security

**Choose your deployment mode based on your needs.**

---

## 🏗️ Three Deployment Modes

### **Mode 1: Offline (Default)** 🔒

**Best for:** Daily use, maximum privacy, no internet needed

```bash
docker-compose -f docker-compose.full-stack.yml up -d \
  weaviate ollama rag-gateway smart-chat openai-compat
make offline-ui
```

**Characteristics:**

- ✅ 100% local operation
- ✅ No external network calls
- ✅ All data on host volumes
- ✅ Works without internet connection
- ❌ Cannot fetch new research papers

**Use when:** Normal operation, sensitive data, no internet available

---

### **Mode 2: Controlled Egress** 🔓

**Best for:** Research paper ingestion, controlled internet access

```bash
make online  # Enable egress proxy + SearXNG
make papers-search Q="your research query"
make papers-ingest
make offline-mode  # Back to offline
```

**Characteristics:**

- ✅ Allowlist-only internet access
- ✅ Research sources only (arxiv, doi, acm, ieee, etc.)
- ✅ Full audit trail
- ✅ Rate limiting enforced
- ✅ Can be toggled on/off
- ❌ Blocks cloud LLMs (openai.com, anthropic.com, etc.)

**Use when:** Ingesting new research papers, updating knowledge base

---

### **Mode 3: Air-Gapped** 🔐

**Best for:** Classified environments, compliance requirements

```bash
docker network create --internal rag_core_nw
docker-compose -f docker-compose.airgapped.yml up -d
```

**Characteristics:**

- ✅ Internal-only Docker network
- ✅ iptables egress blocking
- ✅ DNS blocked to public domains
- ✅ Provable isolation
- ✅ Compliance-ready (HIPAA, SOC2, FedRAMP)
- ❌ Cannot fetch new papers
- ❌ Requires NET_ADMIN capability

**Use when:** Classified data, regulatory compliance, maximum security

---

## 📊 Feature Comparison

| Feature                  | Offline | Controlled Egress | Air-Gapped |
| ------------------------ | ------- | ----------------- | ---------- |
| **Local RAG**            | ✅      | ✅                | ✅         |
| **3 AI models**          | ✅      | ✅                | ✅         |
| **Local UI**             | ✅      | ✅                | ✅         |
| **PWA (iPhone)**         | ✅      | ✅                | ✅         |
| **Streaming**            | ✅      | ✅                | ✅         |
| **Metrics**              | ✅      | ✅                | ✅         |
| **Internet access**      | ❌      | ✅ Allowlist      | ❌         |
| **Paper ingestion**      | ❌      | ✅                | ❌         |
| **Network isolation**    | ❌      | ❌                | ✅         |
| **iptables blocking**    | ❌      | ❌                | ✅         |
| **Compliance certified** | ❌      | ⚠️                | ✅         |
| **Complexity**           | Low     | Medium            | High       |

---

## 🎯 Decision Matrix

### When to Use Each Mode

**Offline Mode:**

```
✅ Daily knowledge base queries
✅ Chat with existing corpus
✅ No internet available
✅ Maximum privacy needed
❌ Need to add new research papers
```

**Controlled Egress:**

```
✅ Weekly research paper updates
✅ Expand knowledge base
✅ Access to academic sources needed
✅ Want audit trail
❌ Compliance forbids any internet
```

**Air-Gapped:**

```
✅ Classified/sensitive data
✅ HIPAA/SOC2/FedRAMP compliance
✅ Zero-trust requirements
✅ Government/defense deployment
❌ Need research paper updates
❌ Can tolerate complexity
```

---

## 🔄 Switching Between Modes

### Offline ↔ Controlled Egress

```bash
# Enable internet (research only)
make online

# Use it
make papers-search Q="query"
make papers-ingest

# Back to offline
make offline-mode
```

**Toggle time:** <10 seconds  
**Data persistence:** ✅ (volumes preserved)

### Offline → Air-Gapped

```bash
# One-time: Create isolated network
docker network create --internal rag_core_nw

# Switch to air-gapped
docker-compose -f docker-compose.full-stack.yml down
docker-compose -f docker-compose.airgapped.yml up -d
```

**Requires:** Network recreation  
**Data migration:** ✅ (same volumes)

### Air-Gapped → Controlled Egress

**Not recommended** — defeats purpose of air-gap

---

## 📋 Quick Commands

### Offline Mode

```bash
make offline          # Validate offline operation
make offline-ui       # Start local UI
```

### Controlled Egress

```bash
make online           # Enable egress proxy
make papers-search Q="query"
make papers-ingest    # Full pipeline
make offline-mode     # Back to offline
```

### Air-Gapped

```bash
make offline          # Validate (includes air-gap checks)
```

---

## 🔒 Security Posture by Mode

### Offline Mode

- **Data exfiltration risk:** Minimal
- **Attack surface:** Localhost only
- **Compliance:** Good for general use
- **Audit requirement:** Low

### Controlled Egress

- **Data exfiltration risk:** Low (allowlist enforced)
- **Attack surface:** Research domains only
- **Compliance:** Good for most enterprises
- **Audit requirement:** Medium (audit logs required)

### Air-Gapped

- **Data exfiltration risk:** None (provably isolated)
- **Attack surface:** Zero external
- **Compliance:** Meets strictest requirements
- **Audit requirement:** High (full audit trail)

---

## 📊 Performance Impact

| Mode              | Startup Time | RAG Query Latency | Paper Fetch | Complexity |
| ----------------- | ------------ | ----------------- | ----------- | ---------- |
| Offline           | 30s          | 250-600ms         | N/A         | Low        |
| Controlled Egress | 40s          | 250-600ms         | 2-5s/paper  | Medium     |
| Air-Gapped        | 35s          | 250-600ms         | N/A         | High       |

**Verdict:** Negligible performance difference, choose based on security needs

---

## 🎯 Recommended Approach

### For Most Users

```
Day-to-Day: Offline Mode
Weekly: Controlled Egress (paper updates)
Special Cases: Air-Gapped
```

**Workflow:**

```bash
# Monday - Friday: Offline
docker-compose -f docker-compose.full-stack.yml up -d
make offline-ui

# Saturday: Research update
make online
make papers-ingest
make offline-mode

# Sunday: Back to offline
# (Already offline from Saturday)
```

---

## 🎉 Success!

**You have complete flexibility:**

✅ **Offline by default** — Privacy-first  
✅ **Online when needed** — Controlled and audited  
✅ **Air-gapped option** — Maximum compliance  
✅ **PWA for iPhone** — Mobile access  
✅ **One-command toggle** — `make online` / `make offline-mode`

**No vendor lock-in. Your choice. Your control.** ✅

---

**Last Updated:** October 18, 2025  
**Default:** Offline Mode  
**Toggle:** `make online` / `make offline-mode`
