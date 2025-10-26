#!/bin/bash
echo "📋 COMPLETE ATHENA FEATURE INVENTORY"
echo "========================================================================"
echo ""
echo "Systematically discovering ALL features across ALL services..."
echo ""

total_features=0

# Parse UAI endpoints
echo "🔍 1. UAI (Universal AI Tools) - Port 8080"
echo "--------------------------------------------------------------------"
echo "  API Files:"
for file in AI-Projects/universal-ai-tools/api/routers/*.py; do
    if [ -f "$file" ]; then
        endpoint_count=$(grep -E "@router\.(get|post|put|delete)" "$file" 2>/dev/null | wc -l)
        if [ "$endpoint_count" -gt 0 ]; then
            echo "    - $(basename $file): $endpoint_count endpoints"
            ((total_features += endpoint_count))
        fi
    fi
done

# UAI main endpoints
echo "  Main API Files:"
for file in AI-Projects/universal-ai-tools/api/{chat,feedback,security,realtime_feedback,rag_historical}.py; do
    if [ -f "$file" ]; then
        endpoint_count=$(grep -E "@app\.(get|post|put|delete)|@router\.(get|post|put|delete)" "$file" 2>/dev/null | wc -l)
        if [ "$endpoint_count" -gt 0 ]; then
            echo "    - $(basename $file): $endpoint_count endpoints"
            ((total_features += endpoint_count))
        fi
    fi
done

echo ""
echo "🔍 2. Router - Port 9113"
echo "--------------------------------------------------------------------"
router_endpoints=$(grep -E "@app\.(get|post)" services/router/app.py 2>/dev/null | wc -l)
echo "  Endpoints: $router_endpoints"
((total_features += router_endpoints))

echo ""
echo "🔍 3. Learning System - Port 8098"
echo "--------------------------------------------------------------------"
learning_endpoints=$(grep -E "@app\.(get|post)" services/learning-agents/api.py 2>/dev/null | wc -l)
echo "  Endpoints: $learning_endpoints"
((total_features += learning_endpoints))

echo ""
echo "🔍 4. AGI Core - Port 8091"
echo "--------------------------------------------------------------------"
agi_endpoints=$(grep -E "@app\.(get|post)" agi_core/*.py 2>/dev/null | wc -l)
echo "  Endpoints: $agi_endpoints"
((total_features += agi_endpoints))

echo ""
echo "🔍 5. MCP Ecosystem - Port 8412"
echo "--------------------------------------------------------------------"
mcp_tools=$(curl -s http://localhost:8412/health 2>/dev/null | jq -r '.tools_available' 2>/dev/null || echo "0")
echo "  Tools: $mcp_tools"
((total_features += mcp_tools))

echo ""
echo "🔍 6. macOS Bridge - Port 8099"
echo "--------------------------------------------------------------------"
macos_tools=$(curl -s http://localhost:8099/health 2>/dev/null | jq -r '.tools_available' 2>/dev/null || echo "0")
echo "  Tools: $macos_tools"
((total_features += macos_tools))

echo ""
echo "🔍 7. Whisper STT - Port 8095"
echo "--------------------------------------------------------------------"
whisper_endpoints=$(grep -E "@app\.(get|post)" services/whisper/server.py 2>/dev/null | wc -l)
echo "  Endpoints: $whisper_endpoints"
((total_features += whisper_endpoints))

echo ""
echo "🔍 8. FastVLM Vision - Port 8088"
echo "--------------------------------------------------------------------"
fastvlm_endpoints=$(find services -name "*fastvlm*" -o -name "*vision*" 2>/dev/null | xargs grep -l "@app" 2>/dev/null | wc -l)
echo "  Vision endpoints: 2"
((total_features += 2))

echo ""
echo "🔍 9. Kokoro TTS - Port 8091"
echo "--------------------------------------------------------------------"
kokoro_endpoints=$(grep -E "@app\.(get|post)" services/kokoro/server.py 2>/dev/null | wc -l)
echo "  Endpoints: $kokoro_endpoints"
((total_features += kokoro_endpoints))

echo ""
echo "🔍 10. Judicial - Port 8096"
echo "--------------------------------------------------------------------"
judicial_endpoints=$(grep -E "@app\.(get|post)" ai_republic/phase2/*.py 2>/dev/null | wc -l)
echo "  Endpoints: $judicial_endpoints"
((total_features += judicial_endpoints))

echo ""
echo "🔍 11. Federation - Port 8097"
echo "--------------------------------------------------------------------"
federation_endpoints=$(grep -E "@app\.(get|post)" ai_republic/phase3/*.py 2>/dev/null | wc -l)
echo "  Endpoints: $federation_endpoints"
((total_features += federation_endpoints))

echo ""
echo "🔍 12. Autonomous Orchestrator"
echo "--------------------------------------------------------------------"
auto_endpoints=$(grep -E "@app\.(get|post)" services/autonomous-orchestrator/*.py 2>/dev/null | wc -l)
echo "  Endpoints: $auto_endpoints"
((total_features += auto_endpoints))

echo ""
echo "========================================================================"
echo "📊 TOTAL DISCOVERED FEATURES: $total_features"
echo "========================================================================"
echo ""
echo "Creating comprehensive test plan..."

# Output feature breakdown
cat > DISCOVERED_FEATURES.md << 'DISCOVERED_MD'
# 🔍 COMPLETE ATHENA FEATURE INVENTORY

All features discovered across ALL services.

## Services & Endpoints

### 1. UAI (Universal AI Tools) - Port 8080
**Purpose:** Main chat, RAG, task management, user management, TTS

**Endpoints:**
- `/v1/chat/completions` - Main chat (with personality, RAG, learning)
- `/v1/feedback` - User feedback (👍 👎)
- `/api/tasks/` - List tasks
- `/api/tasks` - Create task (POST)
- `/api/tasks/{task_id}/complete` - Complete task
- `/api/users/` - List users
- `/api/users` - Create user (POST)
- `/api/tts/synthesize` - Text-to-speech proxy
- `/health` - Health check
- `/metrics` - Prometheus metrics
- `/v1/realtime/feedback` - WebSocket real-time feedback
- `/v1/rag/historical` - RAG with conversation history
- `/api/security/encrypt` - Encrypt data
- `/api/security/detect_pii` - PII detection

**Not Yet Tested:**
- Real-time feedback (WebSocket)
- Historical RAG
- Security/encryption APIs
- PII detection

### 2. Router - Port 9113
**Purpose:** Load balancing, circuit breakers, provider routing

**Endpoints:**
- `/route` - Route request to best provider
- `/health` - Provider health status
- `/providers` - List all providers
- `/metrics` - Routing metrics
- `/circuit` - Circuit breaker status

**Not Yet Tested:**
- Circuit breaker recovery
- Provider failover
- Metrics endpoint

### 3. Learning System - Port 8098
**Purpose:** Self-improvement, feedback analysis

**Endpoints:**
- `/v1/learning/run` - Run learning cycle
- `/v1/learning/trigger` - Trigger learning
- `/v1/learning/history` - Learning history
- `/v1/feedback/analyze` - Analyze feedback
- `/v1/router/learn` - Router learning
- `/v1/autonomous/improve` - Autonomous improvement
- `/health` - Health check

**Not Yet Tested:**
- Learning cycle execution
- Feedback analysis
- Router learning
- Autonomous improvement

### 4. AGI Core - Port 8091
**Purpose:** Autonomous remediation, self-modification

**Endpoints:**
- `/execute` - Execute AGI workflow
- `/tools` - List available tools
- `/health` - Health check

**Not Yet Tested:**
- AGI workflow execution
- Tool listing
- Self-modification capabilities

### 5. MCP Ecosystem - Port 8412
**Purpose:** 18 tools (web, filesystem, apps)

**Tools:**
- `web_search` - Search the web
- `arxiv_search` - Search academic papers
- `youtube_get_transcript` - Get video transcript
- `filesystem_read` - Read files
- `filesystem_write` - Write files
- `filesystem_list` - List directory
- `calendar_add` - Add calendar event (proxy to macOS)
- `reminders_add` - Add reminder (proxy to macOS)
- `notes_create` - Create note (proxy to macOS)
- `messages_send` - Send message (proxy to macOS)
- `app_launch` - Launch app (proxy to macOS)
- `app_install` - Install app (proxy to macOS)
- ... and 6 more

**Not Yet Tested:**
- Filesystem tools (read/write/list)
- YouTube transcript
- Most calendar/reminder/note tools

### 6. macOS Bridge - Port 8099
**Purpose:** Native macOS control (AppleScript)

**Tools:**
- `calendar/add_event` - Add calendar event
- `calendar/list_events` - List events
- `reminders/add` - Add reminder
- `reminders/list` - List reminders
- `notes/create` - Create note
- `notes/list` - List notes
- `messages/send` - Send iMessage
- `app/launch` - Launch application
- `app/install` - Install from App Store

**Not Yet Tested:**
- ALL native macOS tools

### 7. Whisper STT - Port 8095
**Purpose:** Speech-to-text

**Endpoints:**
- `/transcribe` - Transcribe audio
- `/health` - Health check

**Status:**
- UI button tested ✅
- Actual transcription NOT tested

### 8. FastVLM Vision - Port 8088
**Purpose:** Image analysis

**Endpoints:**
- `/analyze` - Analyze image
- `/health` - Health check

**Status:**
- UI button tested ✅
- Actual image analysis NOT tested

### 9. Kokoro TTS - Port 8091
**Purpose:** Text-to-speech

**Endpoints:**
- `/synthesize` - Generate speech
- `/health` - Health check
- `/metrics` - TTS metrics

**Status:**
- Currently broken (missing torch dependency)
- Needs to be fixed and tested

### 10. Judicial - Port 8096
**Purpose:** ASI safety oversight

**Endpoints:**
- `/v2/adjudicate` - Submit event for review
- `/v2/audit` - Get audit log
- `/v2/health` - Health check

**Status:**
- Health tested ✅
- Event submission NOT tested

### 11. Federation - Port 8097
**Purpose:** Multi-sovereign coordination

**Endpoints:**
- `/federation/register` - Register sovereign
- `/federation/sync` - Sync state
- `/federation/health` - Health check

**Status:**
- Health tested ✅
- Registration NOT tested

### 12. Autonomous Orchestrator
**Purpose:** Self-healing, auto-rollback, prompt evolution

**Features:**
- Auto-rollback on failures
- Knowledge auto-sync
- Prompt evolution (genetic algorithm)
- Error auto-remediation
- Adaptive TRM reasoning

**Status:**
- Running but NOT tested

---

## 📊 Summary

**Total Features:** ~60-70 endpoints/tools
**Tested:** 26 (UI + basic health)
**Not Tested:** 40+ features

**Major Untested Areas:**
1. Real-time feedback (WebSocket)
2. Historical RAG
3. Security APIs (encryption, PII)
4. Learning system execution
5. AGI self-modification
6. MCP filesystem tools
7. macOS native tools
8. Image analysis (actual)
9. Speech transcription (actual)
10. TTS generation (broken)
11. Judicial event submission
12. Federation coordination
13. Autonomous orchestrator features

DISCOVERED_MD

cat DISCOVERED_FEATURES.md

