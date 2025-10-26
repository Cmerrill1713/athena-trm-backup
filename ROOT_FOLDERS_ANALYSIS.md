# 📂 Root Folders Analysis

**Total Root Folders:** 57+

## 🟢 ACTIVE & CRITICAL (Keep These)

### Core Applications
- `NeuroForgeApp/` - Your Swift macOS app (governance integration) ✅
- `ollama-source/` - Ollama fork (Athena LLM rebranding) ✅
- `athena/` - Core Athena service
- `agi_core/` - AGI service layer ✅

### Services & Infrastructure
- `services/` - Backend services (router, RAG, MCP, etc.) ✅
- `governance/` - Governance system (executive/judicial/legislative) ✅
- `monitoring/` - Prometheus/Grafana/OTEL ✅
- `backend/` - Backend API services
- `ui/` - Web UI files (athena-chat.html, etc.) ✅

### Configuration
- `config/` - System configs, dashboards ✅
- `docker-compose.yml` - Main stack definition ✅
- `Makefile*` - Build/deployment automation ✅
- `scripts/` - Operational scripts ✅

### Data & Knowledge
- `knowledge_base/` - RAG knowledge base ✅
- `seeds/` - Database seeds
- `db/` - Database files

---

## 🟡 REVIEW NEEDED (Decide Keep/Archive)

### UI Projects (Multiple)
- `athena-desktop-ui/` - Desktop UI variant
- `athena-macapp-ui/` - Mac app UI variant
- `athena-custom-ui/` - Custom UI variant
- `athena-voice-control/` - Voice control UI
- `SwiftUI_MCP_Modernization/` - SwiftUI modernization work

**Question:** Are these separate from NeuroForgeApp? Should they be consolidated?

### AI Projects
- `AI-Projects/` - Contains universal-ai-tools
- `pydantic-ai/` - Pydantic AI experiments
- `TinyRecursiveModels/` - TRM experiments
- `fastvlm/` - FastVLM integration

**Question:** Active experiments or archivable?

### Utilities
- `A2A/` - Agent-to-agent communication?
- `ai_republic/` - AI republic governance?
- `assistant-broker/` - Assistant broker service
- `orchestrator/` - Orchestration layer
- `common/` - Common utilities

---

## 🔴 LIKELY OBSOLETE (Consider Archiving)

### Archive/Backup Folders
- `archive/` - Already archived content ✅
- `backups/` - Backup files
- `artifacts/` - Build artifacts
- `snapshots/` - Snapshots
- `state/` - Runtime state files
- `logs/` - Log files

### Old Integrations
- `searxng/` - Search integration (using?)
- `traefik/` - Traefik config (using?)
- `tempo/` - Tempo tracing (using?)
- `manifests/` - K8s manifests (using?)

### Example/Test Folders
- `examples/` - Example code
- `tests/` - Test suite (keep if active)
- `sandbox/` - Sandbox/experiments
- `indydevdan_transcripts/` - Transcripts (what is this?)

---

## 📊 Statistics by Category

| Category | Count | Status |
|----------|-------|--------|
| Active Core | 8 | ✅ Keep |
| UI Variants | 5 | 🟡 Review |
| Services | 10 | ✅ Keep |
| Archive/Logs | 6 | 🔴 Can archive |
| Config/Docs | 15+ | ✅ Keep |
| Experiments | 5 | 🟡 Review |
| Infrastructure | 8 | 🟡 Review |

---

## 🎯 Recommendations

### 1. **Consolidate UI Projects**
```bash
# If athena-desktop-ui, athena-macapp-ui are duplicates/old:
git mv athena-desktop-ui archive/ui-variants/
git mv athena-macapp-ui archive/ui-variants/
# Keep only NeuroForgeApp as the canonical Swift app
```

### 2. **Archive Build Artifacts**
```bash
# These shouldn't be in git:
echo "artifacts/" >> .gitignore
echo "snapshots/" >> .gitignore
echo "logs/" >> .gitignore
echo "state/" >> .gitignore
```

### 3. **Clarify AI Projects**
- Decide which AI experiments are active
- Archive completed experiments
- Document purpose of active ones

### 4. **Clean Up Duplicates**
- Multiple docker-compose files (keep main + specialized only)
- Multiple README files (consolidate)
- Multiple UI folders (pick canonical one)

---

## ❓ Questions to Answer

1. **NeuroForgeApp vs other UI folders** - Is NeuroForgeApp your primary UI now?
2. **AI-Projects/** - Is this actively used or can it be archived?
3. **TinyRecursiveModels/** - Active research or archivable?
4. **Multiple UI variants** - Which one(s) are actually deployed?
5. **Infrastructure** (traefik, tempo, searxng) - Currently used in your stack?

---

## 🚀 Quick Cleanup Commands

### Safe to remove from git (build artifacts):
```bash
cd /Users/christianmerrill/Documents/GitHub
# Add to .gitignore:
cat >> .gitignore << 'IGNORE'
artifacts/
snapshots/
logs/
state/
backups/
.pytest_cache/
.ruff_cache/
IGNORE

# Remove from tracking:
git rm -r --cached artifacts/ snapshots/ logs/ state/ 2>/dev/null
```

### Archive old UI variants (if not used):
```bash
mkdir -p archive/ui-variants
# Move old UI projects here if NeuroForgeApp is primary
```

Would you like me to:
1. **Audit specific folders** to determine if they're active?
2. **Create a cleanup script** to archive obsolete folders?
3. **Consolidate UI projects** into one canonical app?
4. **Update .gitignore** to exclude build artifacts?
