# 🔓 Controlled Egress Mode — Selective Internet Access

**Offline by default, online when needed — with audit trail and allowlists.**

---

## 🎯 Philosophy

**Three modes for different needs:**

1. **Offline (Default)** — Zero internet, 100% local
2. **Controlled Egress** — Allowlist-only via proxy
3. **Air-Gapped** — Network isolation + iptables blocking

---

## 🚀 Quick Start

### Enable Online Mode

```bash
# Turn on controlled egress
make online
```

**This starts:**

- Egress proxy (Squid) with allowlist
- SearXNG (meta-search for research papers)

**Allowlisted domains:**

- arxiv.org, doi.org, crossref.org
- acm.org, ieee.org, semanticscholar.org
- pubmed.gov, nature.com, springer.com
- - 6 more research sources

### Use It

```bash
# Search for papers
make papers-search Q="retrieval augmented generation"

# Review and queue results
make papers-queue-latest

# Fetch PDFs (via proxy)
make papers-fetch

# Embed to Weaviate
make papers-embed

# Validate quality
make papers-eval
```

### Disable Online Mode

```bash
# Back to offline
make offline-mode
```

---

## 🏗️ Architecture

### Offline Mode (Default)

```
UI → Adapter → RAG/Chat → Weaviate/Ollama
(No external access)
```

### Online Mode (When Enabled)

```
UI → Adapter → RAG/Chat → Weaviate/Ollama
                  ↓
            Egress Proxy (Allowlist)
                  ↓
        SearXNG → Research Sites Only
          (arxiv, doi, acm, ieee, etc.)
```

**Key differences:**

- Egress proxy enforces allowlist (no arbitrary internet)
- All outbound goes through single auditable gateway
- SearXNG aggregates multiple research sources
- Can be toggled on/off with Make command

---

## 📚 Research Paper Ingestion Pipeline

### Step-by-Step

**1. Enable online mode:**

```bash
make online
```

**2. Search for papers:**

```bash
make papers-search Q="vector embeddings deep learning"
```

**3. Review and queue:**

```bash
# Review results
cat artifacts/search_*.json | jq '.results[] | {title, url, score}'

# Add to queue (min score 0.6)
make papers-queue-latest MIN_SCORE=0.6
```

**4. Fetch PDFs:**

```bash
# Download top 10 papers
make papers-fetch LIMIT=10 THROTTLE=3.0
```

**5. Embed to Weaviate:**

```bash
make papers-embed CLASS=DocsV2
```

**6. Validate quality:**

```bash
# Run RAG evaluation to ensure quality didn't regress
make papers-eval
```

**7. Disable online mode:**

```bash
make offline-mode
```

### One-Command Pipeline

```bash
make papers-ingest
# Interactive: prompts for query, then runs full pipeline
```

---

## 🔒 Security & Audit

### Allowlist Enforcement

**Egress proxy** (`egress/acl.conf`):

```squid
acl research_sources dstdomain .arxiv.org .doi.org .crossref.org ...
acl numeric_IPs dstdom_regex ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$

http_access deny numeric_IPs  # No direct IP access
http_access allow research_sources
http_access deny all           # Deny everything else
```

**Blocked:**

- ❌ openai.com, anthropic.com, google.com
- ❌ Direct IP addresses
- ❌ Non-research domains

**Allowed:**

- ✅ arxiv.org (preprints)
- ✅ doi.org (DOI resolution)
- ✅ acm.org, ieee.org (papers)
- ✅ semanticscholar.org (meta-search)

### Audit Trail

```bash
# View all egress requests
docker logs egress-proxy | grep "TCP_MISS"

# Export audit log
docker exec egress-proxy cat /var/log/squid/access.log \
  > audit/egress-$(date +%Y%m%d).log
```

### Rate Limiting

**Squid:** Configured in ACL  
**SearXNG:** 600 req/hour max (see `searxng/limiter.toml`)  
**Fetcher:** 2-second throttle between downloads

---

## 📱 iPhone Client Options

### Option 1: PWA (Fastest)

**Your HTML UI is now a PWA!**

**On iPhone:**

1. Open Safari: `https://your-domain/athena-chat.html`
2. Tap Share → "Add to Home Screen"
3. Icon appears on home screen
4. Launch like native app!

**Features:**

- ✅ Installable (home screen icon)
- ✅ Offline cache (service worker)
- ✅ Full-screen mode
- ✅ No App Store needed
- ✅ Works with your adapter over HTTPS

**Setup:**

```bash
# Serve over HTTPS (required for PWA)
# Already configured in nginx.conf

# Files added:
# - ui/manifest.json (PWA manifest)
# - ui/sw.js (service worker)
# - ui/athena-chat.html (PWA meta tags)
```

### Option 2: SwiftUI App (Best UX)

**Use Exyte/Chat or custom SwiftUI:**

```swift
// ContentView.swift
import SwiftUI

struct ContentView: View {
    @StateObject var viewModel = ChatViewModel()

    var body: some View {
        ChatView(messages: $viewModel.messages) { message in
            Task {
                await viewModel.send(message)
            }
        }
    }
}

class ChatViewModel: ObservableObject {
    @Published var messages: [Message] = []
    private let apiBase = "https://your-domain/v1"

    func send(_ text: String) async {
        // Add user message
        messages.append(Message(role: .user, content: text))

        // Call adapter
        let response = try? await fetch(
            url: "\(apiBase)/chat/completions",
            method: "POST",
            body: [
                "model": "athena-rag",
                "messages": messages.map { ["role": $0.role, "content": $0.content] },
                "stream": false
            ]
        )

        if let reply = response?["choices"][0]["message"]["content"] as? String {
            messages.append(Message(role: .assistant, content: reply))
        }
    }
}
```

**Auth:** Use Keychain for API key storage

---

## 🔧 Configuration

### Enable Proxy for Specific Services

**In .env:**

```env
# Online mode (set when running 'make online')
HTTP_PROXY=http://localhost:3128
HTTPS_PROXY=http://localhost:3128
NO_PROXY=localhost,127.0.0.1,weaviate,ollama
```

### Customize Allowlist

**Edit `egress/acl.conf`:**

```squid
# Add your trusted domains
acl research_sources dstdomain .yourdomain.com
```

---

## 📊 Queue Management

### View Status

```bash
make papers-status
```

**Output:**

```
status      count
----------  -----
queued      25
fetched     18
embedded    15
error       2
```

### Clean Errors

```bash
make papers-clean-errors
```

---

## 🎯 Use Cases

### Use Case 1: Weekly Research Update

```bash
# Monday morning: fetch latest papers
make online
make papers-search Q="recent advances RAG 2025"
make papers-queue-latest
make papers-fetch LIMIT=20
make papers-embed
make papers-eval
make offline-mode
```

### Use Case 2: On-Demand Topic Dive

```bash
# Deep dive into a topic
make online
make papers-search Q="graph neural networks retrieval"
make papers-ingest  # Interactive pipeline
```

### Use Case 3: Mobile Access

```bash
# Configure HTTPS in nginx.conf
# Access from iPhone Safari
# Add to home screen (PWA)
# Use like native app!
```

---

## 🔒 Compliance Benefits

### Controlled vs Unrestricted

| Feature                   | Unrestricted Internet | Controlled Egress |
| ------------------------- | --------------------- | ----------------- |
| Access to research papers | ✅                    | ✅                |
| Access to social media    | ✅                    | ❌                |
| Access to cloud LLMs      | ✅                    | ❌                |
| Direct IP access          | ✅                    | ❌                |
| Audit trail               | ❌                    | ✅                |
| Allowlist enforcement     | ❌                    | ✅                |
| Compliance-ready          | ❌                    | ✅                |

### Audit Reports

```bash
# Generate weekly audit
docker exec egress-proxy cat /var/log/squid/access.log | \
  awk '{print $7}' | sort | uniq -c | sort -rn \
  > audit/weekly-egress-$(date +%Y%m%d).txt
```

---

## 🎉 Success!

**You now have three deployment modes:**

**1. Offline (Default)**

```bash
# Pure local, zero internet
docker-compose -f docker-compose.full-stack.yml up -d
```

**2. Controlled Egress**

```bash
# Research sources only, audited
make online
```

**3. Air-Gapped**

```bash
# Maximum isolation, provable
docker-compose -f docker-compose.airgapped.yml up -d
```

**Plus mobile access via PWA!**

---

**Read more:**

- `Makefile.papers` — Paper ingestion targets
- `LOCAL_UI_OPTIONS.md` — PWA setup guide
- `PRODUCTION_RUNBOOK.md` — Operations

---

**Last Updated:** October 18, 2025  
**Default Mode:** Offline  
**Online Mode:** Opt-in with `make online`
