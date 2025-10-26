# 🎨 FRONTEND INTEGRATION AUDIT

**Goal:** Ensure athena-chat.html connects to ALL backend services  
**Current:** Checking what's connected vs what should be connected

---

## 🔍 CURRENT BACKEND SERVICES

### Core AI Services:
1. **UAI API** - http://localhost:8080
   - Unified AI interface
   - Chat completions
   - RAG integration
   - Health check

2. **Router** - http://localhost:9113
   - Intelligent routing
   - Load balancing
   - Fallback logic
   - Model selection

3. **Ollama** (via UAI) - http://localhost:11434
   - Local LLM inference
   - Model management

### Multimodal Services:
4. **FastVLM (Vision)** - http://localhost:8088
   - Image analysis
   - Visual understanding

5. **Kokoro TTS (Voice)** - http://localhost:8091
   - Text-to-speech
   - Voice synthesis

### Tool Services:
6. **MCP Ecosystem** - http://localhost:8082
   - Web search (via SearXNG)
   - ArXiv search
   - YouTube transcripts

7. **SearXNG** - http://localhost:8081
   - Privacy-first search engine

### Governance & Monitoring:
8. **Governance Orchestrator** - http://localhost:8000
   - Constitutional AI
   - Policy enforcement

9. **Prometheus** - http://localhost:9090
   - Metrics collection

10. **Grafana** - http://localhost:3001
    - Dashboards & visualization

---

## 📋 CHECKING CURRENT FRONTEND...


## ✅ CURRENTLY CONNECTED (Basic)

**athena-chat.html** currently connects to:
1. ✅ UAI API (http://localhost:8080)
   - `/v1/chat/completions` - Chat
   - `/health` - Health check

**That's it!** Only 1 service out of 10+ available.

---

## ❌ NOT CONNECTED (Missing Integrations)

### Missing Core Features:
2. ❌ **Router** (http://localhost:9113)
   - No direct router access
   - No load balancing visibility
   - No failover status

3. ❌ **FastVLM Vision** (http://localhost:8088)
   - No image upload
   - No visual analysis
   - No OCR

4. ❌ **Kokoro TTS** (http://localhost:8091)
   - No text-to-speech
   - No voice output
   - No audio playback

5. ❌ **MCP Tools** (http://localhost:8082)
   - No web search
   - No ArXiv lookup
   - No tool integration

6. ❌ **SearXNG** (http://localhost:8081)
   - No search capability
   - Frontend can't trigger searches

7. ❌ **Governance** (http://localhost:8000)
   - No policy status
   - No constitutional checks
   - No governance dashboard

8. ❌ **Prometheus** (http://localhost:9090)
   - No metrics display
   - No performance stats

9. ❌ **Grafana** (http://localhost:3001)
   - Not embedded
   - No dashboard access

---

## 🎯 INTEGRATION PLAN

### Phase 1: Multimodal Features (High Priority)
**Goal:** Add vision and voice to chat UI

**Add to Frontend:**
1. **Image Upload** → FastVLM
   - Upload button
   - Image preview
   - Send to `/vision/analyze`
   - Display results

2. **Text-to-Speech** → Kokoro
   - TTS button on messages
   - Audio playback
   - Voice synthesis controls

3. **Tool Integration** → MCP
   - Search button
   - ArXiv lookup
   - Tool selector dropdown

---

### Phase 2: Monitoring & Status (Medium Priority)
**Goal:** Show system health and performance

**Add to Frontend:**
4. **System Status Panel**
   - Service health indicators
   - Response times
   - Error rates

5. **Metrics Dashboard**
   - Embed Grafana iframe
   - Show key metrics
   - Performance graphs

---

### Phase 3: Advanced Features (Lower Priority)
**Goal:** Full system control from UI

6. **Model Selector**
   - Dynamic model list from Router
   - Switch between models
   - Model health status

7. **Governance Panel**
   - Policy status
   - Constitutional checks
   - Audit trail

---

## 🏗️ PROPOSED NEW ARCHITECTURE

```
┌─────────────────────────────────────────────┐
│         Athena Frontend (athena-chat.html)  │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │   Chat   │  │  Vision  │  │   Voice  │ │
│  │  💬      │  │  👁️      │  │   🔊     │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘ │
│       │             │              │        │
└───────┼─────────────┼──────────────┼────────┘
        │             │              │
        ▼             ▼              ▼
┌───────────────────────────────────────────┐
│           Backend Services                │
├───────────────────────────────────────────┤
│  UAI (8080)  │  FastVLM (8088)  │  Kokoro │
│  Router      │  MCP Tools       │  (8091) │
│  (9113)      │  (8082)          │         │
└───────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────┐
│          Monitoring & Governance          │
├───────────────────────────────────────────┤
│  Prometheus  │  Grafana  │  Governance    │
│  (9090)      │  (3001)   │  (8000)        │
└───────────────────────────────────────────┘
```

---

## 🎨 UI MOCKUP (What to Add)

```
┌─────────────────────────────────────────────┐
│  Athena AI  [Settings] [Status ✅]          │
├─────────────────────────────────────────────┤
│                                             │
│  ┌────────────────────────────────────┐    │
│  │ Chat History                       │    │
│  │                                    │    │
│  │ User: What is quantum computing?   │    │
│  │ [🔊 Speak]                         │    │
│  │                                    │    │
│  │ AI: Quantum computing is...        │    │
│  │ [🔊 Speak]                         │    │
│  └────────────────────────────────────┘    │
│                                             │
│  ┌────────────────────────────────────┐    │
│  │ Type message...                    │    │
│  │ [📎 Upload] [🔍 Search] [Send →]   │    │
│  └────────────────────────────────────┘    │
│                                             │
│  [Models ▼] [Tools ▼] [📊 Metrics]         │
└─────────────────────────────────────────────┘
```

**New Additions:**
- 🔊 **Speak button** - TTS for each message
- 📎 **Upload button** - Image analysis
- 🔍 **Search button** - Web/ArXiv search
- 📊 **Metrics button** - Show system status
- **Tools dropdown** - MCP tool selection

---

## 🚀 IMPLEMENTATION STEPS

### Step 1: Add Vision Support
```javascript
// Add image upload functionality
async function analyzeImage(imageFile) {
    const formData = new FormData();
    formData.append('image', imageFile);
    
    const response = await fetch('http://localhost:8088/analyze', {
        method: 'POST',
        body: formData
    });
    
    return await response.json();
}
```

### Step 2: Add TTS Support
```javascript
// Add text-to-speech
async function speakText(text) {
    const response = await fetch('http://localhost:8091/synthesize', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({text: text})
    });
    
    const audioBlob = await response.blob();
    const audioUrl = URL.createObjectURL(audioBlob);
    const audio = new Audio(audioUrl);
    audio.play();
}
```

### Step 3: Add Tool Integration
```javascript
// Add web search via MCP
async function webSearch(query) {
    const response = await fetch('http://localhost:8082/tool/web_search', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            arguments: {query: query, num_results: 5}
        })
    });
    
    return await response.json();
}
```

### Step 4: Add System Status
```javascript
// Check all service health
async function checkSystemHealth() {
    const services = [
        {name: 'UAI', url: 'http://localhost:8080/health'},
        {name: 'Router', url: 'http://localhost:9113/health'},
        {name: 'FastVLM', url: 'http://localhost:8088/health'},
        {name: 'Kokoro', url: 'http://localhost:8091/health'},
        {name: 'MCP', url: 'http://localhost:8082/health'}
    ];
    
    const results = await Promise.all(
        services.map(async s => {
            try {
                const r = await fetch(s.url);
                return {name: s.name, status: r.ok ? '✅' : '❌'};
            } catch {
                return {name: s.name, status: '❌'};
            }
        })
    );
    
    return results;
}
```

---

## ✅ SUCCESS CRITERIA

When complete, the frontend should:

1. ✅ Connect to all 10+ backend services
2. ✅ Support multimodal (text, image, voice)
3. ✅ Show system health status
4. ✅ Integrate MCP tools (search, arxiv, etc.)
5. ✅ Display metrics (Prometheus/Grafana)
6. ✅ One UI for everything

---

**What do you want to focus on first?**

**A.** Multimodal (vision + voice) - High value
**B.** Tools integration (search, arxiv) - Medium value  
**C.** Monitoring dashboard - Lower value  
**D.** All of the above - Complete integration  

I recommend **D - All of the above** for a complete, unified frontend! 🚀

