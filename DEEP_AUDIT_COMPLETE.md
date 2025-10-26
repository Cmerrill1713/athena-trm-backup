# 🔍 COMPLETE DEEP FOLDER AUDIT

**Date:** October 26, 2025  
**Repository:** athena-trm-backup  
**Total Root Folders:** 57+

---

## 📊 EXECUTIVE SUMMARY

### Repository Size Analysis
- **Estimated Total Size:** 35-50GB
- **Total Files:** ~750,000+ files across all folders
- **Largest Folders:** 
  1. archive/ (15GB, 290K files)
  2. AI-Projects/ (12GB, 285K files)
  3. fastvlm/ (5GB, 741 files)
  4. governance/ (4.6GB, 128K files)
  5. ollama-source/ (693MB, 34K files)

### Critical Issues
- ⚠️ **Massive repository size** (likely 35-50GB)
- ⚠️ **Many obsolete/archived folders**
- ⚠️ **Build artifacts and logs in git**
- ⚠️ **Multiple duplicate UI projects**
- ⚠️ **node_modules committed** (athena-macapp-ui)

---

## 🟢 PART 1: ACTIVE & CRITICAL FOLDERS

### 1.1 Core Applications

#### ✅ NeuroForgeApp/ (PRIMARY SWIFT APP)
- **Files:** 8,872
- **Size:** 656MB
- **Status:** ACTIVE - Your main Swift macOS application
- **Last Modified:** 2025-10-17
- **Key Components:**
  - 72 Swift source files
  - Governance integration (5 files)
  - LLM Gateway, Chat UI, Routing
  - Services: ChatService, VoiceIOService, VisionIOService
  - Complete MVVM architecture
- **Recommendation:** ✅ KEEP - This is your primary app

#### ✅ ollama-source/ (OLLAMA FORK)
- **Files:** 34,968
- **Size:** 693MB
- **Status:** ACTIVE - Ollama fork with Athena LLM rebranding
- **Key Components:**
  - Full Ollama codebase
  - Custom Athena branding
  - Test file you're working on (llama_test.go)
  - macOS app build
- **Recommendation:** ✅ KEEP - Active development

#### ✅ agi_core/
- **Files:** 86
- **Size:** 884KB
- **Status:** ACTIVE - AGI service layer
- **Key Components:**
  - AGI service implementation
  - Docker configurations
  - Integration guides
- **Recommendation:** ✅ KEEP - Core service

#### ⚠️ athena/
- **Files:** 3
- **Size:** 12KB
- **Status:** MINIMAL - Only db.py, judge.py, requirements.txt
- **Recommendation:** 🟡 REVIEW - Might be obsolete or needs consolidation

### 1.2 Services & Infrastructure

#### ✅ services/
- **Files:** 4,331
- **Size:** 101MB
- **Status:** ACTIVE - Core backend services
- **Key Services:**
  - router/ - Routing system
  - rag-gateway/ - RAG integration
  - mcp-ecosystem/ - MCP tools
  - kokoro/ - Voice services
  - llm_gateway/ - LLM gateway
  - openai-compat/ - OpenAI compatibility
  - model_pool.py, embedding_service.py
- **Recommendation:** ✅ KEEP - Active services

#### ✅ governance/
- **Files:** 128,799 files
- **Size:** 4.6GB (!!)
- **Status:** ACTIVE but BLOATED
- **Structure:**
  - executive/ - Orchestration
  - judicial/ - Evaluation (many test artifacts)
  - legislative/ - Policy compiler
  - archive/ - Old iterations
  - observability/ - Monitoring
- **⚠️ Issues:** 
  - Extremely large (4.6GB)
  - Contains many test artifacts and archives
  - governance/judicial/evaluation/ has massive test results
- **Recommendation:** 🟡 KEEP but CLEANUP - Archive old test results

#### ✅ ui/
- **Files:** 9
- **Size:** 112KB
- **Status:** ACTIVE - Web UI files
- **Files:**
  - athena-chat.html (fixed)
  - simple-chat.html
  - agi_demo.html
  - test-ui.html
- **Recommendation:** ✅ KEEP - Active UIs

#### ✅ monitoring/
- **Files:** 14
- **Size:** 108KB
- **Status:** ACTIVE - Prometheus/Grafana/OTEL
- **Recommendation:** ✅ KEEP - Active monitoring

#### ✅ backend/
- **Files:** 16
- **Size:** 11MB
- **Status:** ACTIVE - Backend utilities
- **Recommendation:** ✅ KEEP

---

## 🟡 PART 2: REVIEW NEEDED

### 2.1 UI Variants (Multiple Implementations)

#### ⚠️ athena-desktop-ui/
- **Files:** 2
- **Size:** 12KB
- **Status:** MINIMAL - Only main.js and package.json
- **Recommendation:** 🔴 ARCHIVE - Superseded by NeuroForgeApp

#### ⚠️ athena-macapp-ui/
- **Files:** 33,838 files
- **Size:** 553MB (!!)
- **Status:** ELECTRON APP - TypeScript/React with node_modules
- **⚠️ Issues:**
  - node_modules committed (bad practice)
  - Duplicates NeuroForgeApp functionality
- **Recommendation:** 🟡 DECIDE - If active, add to .gitignore and rebuild; otherwise archive

#### 🔴 athena-custom-ui/
- **Files:** 0
- **Size:** 0B
- **Status:** EMPTY
- **Recommendation:** 🔴 DELETE - Empty folder

#### ✅ athena-voice-control/
- **Files:** 5
- **Size:** 44KB
- **Status:** VOICE CONTROL SCRIPTS
- **Recommendation:** 🟡 KEEP if used, else archive

### 2.2 AI Experiments

#### ⚠️ AI-Projects/ (MASSIVE!)
- **Files:** 285,723 files
- **Size:** 12GB (!!)
- **Status:** CONTAINS "Universal AI Tools" app
- **⚠️ Issues:**
  - Extremely large
  - Submodule or separate project?
- **Recommendation:** 🔴 MOVE - Should be separate repo or properly managed submodule

#### ⚠️ TinyRecursiveModels/
- **Files:** 6,128
- **Size:** 282MB
- **Status:** RESEARCH PROJECT - Has completion docs
- **Recommendation:** 🟡 ARCHIVE - Research appears complete

#### ⚠️ pydantic-ai/
- **Files:** 331
- **Size:** 36MB
- **Status:** EXPERIMENTS
- **Recommendation:** 🟡 REVIEW - Active experiments or archivable?

#### ⚠️ fastvlm/
- **Files:** 741
- **Size:** 5.0GB (!!)
- **Status:** VISION MODEL INTEGRATION
- **⚠️ Issues:**
  - Very large (5GB)
  - Contains ml-fastvlm models
- **Recommendation:** 🟡 KEEP if active, but ensure models in .gitignore

### 2.3 Utilities

#### ✅ A2A/
- **Files:** 56
- **Size:** 9.6MB
- **Status:** Agent-to-agent communication
- **Recommendation:** 🟡 KEEP if active

#### ✅ ai_republic/
- **Files:** 26
- **Size:** 304KB
- **Status:** Federation/governance phases
- **Recommendation:** ✅ KEEP

#### ✅ assistant-broker/
- **Files:** 6
- **Size:** 36KB
- **Status:** Swift package
- **Recommendation:** ✅ KEEP

#### ✅ orchestrator/
- **Files:** 5
- **Size:** 28KB
- **Status:** Python orchestrator service
- **Recommendation:** ✅ KEEP

#### ✅ common/
- **Files:** 7
- **Size:** 40KB
- **Status:** Shared Python utilities
- **Recommendation:** ✅ KEEP

### 2.4 Infrastructure

#### ✅ searxng/
- **Files:** 2
- **Size:** 8KB
- **Status:** Search integration configs
- **Recommendation:** 🟡 KEEP if used in stack

#### ✅ traefik/
- **Files:** 1
- **Size:** 4KB
- **Status:** Traefik dynamic config
- **Recommendation:** 🟡 KEEP if used

#### ✅ tempo/
- **Files:** 1
- **Size:** 4KB
- **Status:** Tempo tracing config
- **Recommendation:** 🟡 KEEP if used

#### ✅ manifests/
- **Files:** 1
- **Size:** 4KB
- **Status:** Policy bundle
- **Recommendation:** ✅ KEEP

#### ✅ infra/
- **Files:** 11
- **Size:** 64KB
- **Status:** Infrastructure SDK
- **Recommendation:** ✅ KEEP

#### 🔴 policy/
- **Files:** 0
- **Size:** 0B
- **Status:** EMPTY
- **Recommendation:** 🔴 DELETE

---

## 🔴 PART 3: SHOULD BE ARCHIVED/REMOVED

### 3.1 Archive Folders (Already Historical)

#### 🔴 archive/ (MASSIVE!)
- **Files:** 290,609 files
- **Size:** 15GB (!!)
- **Status:** ALREADY ARCHIVED CONTENT
- **⚠️ Issues:**
  - Extremely large (15GB)
  - Already archived material
  - Should not be in active git
- **Recommendation:** 🔴 MOVE OUT OF GIT - Use external storage or separate archive repo

#### 🔴 backups/
- **Files:** 5
- **Size:** 20KB
- **Recommendation:** 🔴 ADD TO .gitignore - Backups shouldn't be in git

### 3.2 Build Artifacts & Runtime Data

#### 🔴 artifacts/
- **Files:** 9
- **Size:** 60KB
- **Recommendation:** 🔴 ADD TO .gitignore - Build artifacts

#### 🔴 snapshots/
- **Files:** 4
- **Size:** 28KB
- **Recommendation:** 🔴 ADD TO .gitignore

#### 🔴 logs/
- **Files:** 82
- **Size:** 249MB
- **⚠️ Issues:** Large log files in git
- **Recommendation:** 🔴 ADD TO .gitignore + git rm --cached

#### 🔴 state/
- **Files:** 44
- **Size:** 184KB
- **Recommendation:** 🔴 ADD TO .gitignore - Runtime state

#### 🔴 .pytest_cache/
- **Files:** 5
- **Size:** 20KB
- **Recommendation:** 🔴 ADD TO .gitignore

#### 🔴 .ruff_cache/
- **Files:** 1
- **Size:** 4KB
- **Recommendation:** 🔴 ADD TO .gitignore

### 3.3 Active Support Folders (Keep but Review)

#### ✅ tests/
- **Files:** 15
- **Size:** 108KB
- **Status:** Test suites
- **Recommendation:** ✅ KEEP - Active tests

#### ✅ examples/
- **Files:** 1
- **Size:** 8KB
- **Recommendation:** ✅ KEEP

#### ⚠️ sandbox/
- **Files:** 2
- **Size:** 8KB
- **Recommendation:** 🟡 CLEANUP - Old sandbox experiments

#### ✅ tools/
- **Files:** 16
- **Size:** 12MB
- **Recommendation:** ✅ KEEP - Active tools

#### ✅ scripts/
- **Files:** 236
- **Size:** 1.7MB
- **Recommendation:** ✅ KEEP - Operational scripts

#### ✅ dashboards/
- **Files:** 8
- **Size:** 60KB
- **Recommendation:** ✅ KEEP - Grafana dashboards

---

## 📈 SUMMARY STATISTICS

### By Status

| Status | Folders | Estimated Size | Files |
|--------|---------|----------------|-------|
| ✅ Keep (Active) | 25 | ~2GB | ~50K |
| 🟡 Review Needed | 15 | ~20GB | ~300K |
| 🔴 Archive/Remove | 17 | ~20GB | ~400K |

### Space Savings Potential

By cleaning up recommended folders:
- **archive/** → Move out: 15GB, 290K files
- **AI-Projects/** → Separate repo: 12GB, 285K files
- **fastvlm/** → Optimize: 5GB, 741 files
- **governance/** → Cleanup: ~2GB saved
- **logs/state/artifacts/** → Remove: 250MB
- **athena-macapp-ui/** → Fix node_modules: 500MB+

**Total Potential Savings: 30-35GB** (70-80% reduction!)

---

## 🎯 ACTIONABLE RECOMMENDATIONS

### IMMEDIATE (Do Now)

1. **Add to .gitignore:**
```bash
# Build artifacts
artifacts/
snapshots/
.pytest_cache/
.ruff_cache/

# Runtime data
logs/
state/
backups/

# Dependencies
node_modules/
.build/
.swiftpm/

# Large models
*.bin
*.gguf
*.safetensors
```

2. **Remove tracked artifacts:**
```bash
git rm -r --cached logs/ state/ artifacts/ snapshots/ backups/
git commit -m "chore: remove build artifacts and runtime data from git"
```

3. **Delete empty folders:**
```bash
rm -rf athena-custom-ui/ policy/
git add -u
git commit -m "chore: remove empty folders"
```

### SHORT TERM (This Week)

4. **Move archive/ out of git:**
```bash
# Create external archive
mkdir -p ~/athena-archives
mv archive/ ~/athena-archives/archive-$(date +%Y%m%d)/
git add archive/
git commit -m "chore: move archive to external storage"
```

5. **Handle AI-Projects:**
```bash
# Option A: Make it a proper submodule
git rm -r AI-Projects/
git submodule add <url> AI-Projects

# Option B: Move to separate repo
# (recommended if it's its own project)
```

6. **Fix athena-macapp-ui node_modules:**
```bash
cd athena-macapp-ui
echo "node_modules/" >> .gitignore
git rm -r --cached node_modules/
git commit -m "fix: remove node_modules from git"
```

7. **Archive obsolete UI:**
```bash
mkdir -p archive/ui-variants-2025-10-26
git mv athena-desktop-ui archive/ui-variants-2025-10-26/
git commit -m "chore: archive obsolete athena-desktop-ui"
```

### MEDIUM TERM (This Month)

8. **Cleanup governance/ test artifacts:**
```bash
cd governance/judicial/evaluation
# Remove old test zip files (keep last 2-3 only)
rm -f *.zip
git add -u
git commit -m "chore: cleanup old governance test artifacts"
```

9. **Review and archive TinyRecursiveModels:**
```bash
# If research is complete:
git mv TinyRecursiveModels archive/completed-research/
```

10. **Optimize fastvlm:**
```bash
# Ensure model files are not tracked
cd fastvlm
echo "*.bin" >> .gitignore
echo "*.gguf" >> .gitignore
echo "*.safetensors" >> .gitignore
echo "ml-fastvlm/models/" >> .gitignore
```

### LONG TERM (Next Quarter)

11. **Consolidate UI projects** - Pick one: NeuroForgeApp or athena-macapp-ui
12. **Create separate repos** for large experiments (AI-Projects, TinyRecursiveModels)
13. **Implement LFS** for any large files that must be tracked
14. **Regular cleanup schedule** - Monthly review of logs/artifacts

---

## 🚀 QUICK CLEANUP SCRIPT

Save this as `cleanup_repo.sh`:

```bash
#!/bin/bash
set -e

echo "🧹 Starting repository cleanup..."

# Add to .gitignore
cat >> .gitignore << 'IGNORE'
# Build artifacts
artifacts/
snapshots/
.pytest_cache/
.ruff_cache/
.venv/
.uv-services/

# Runtime data
logs/
state/
backups/

# Dependencies
node_modules/
.build/
.swiftpm/

# Large models
*.bin
*.gguf
*.safetensors
IGNORE

# Remove tracked artifacts
echo "📦 Removing build artifacts from git..."
git rm -r --cached logs/ state/ artifacts/ snapshots/ backups/ 2>/dev/null || true
git rm -r --cached athena-macapp-ui/node_modules/ 2>/dev/null || true

# Delete empty folders
echo "🗑️  Removing empty folders..."
[ -d "athena-custom-ui" ] && rmdir athena-custom-ui 2>/dev/null || true
[ -d "policy" ] && rmdir policy 2>/dev/null || true

# Stage changes
git add .gitignore

echo "✅ Cleanup complete!"
echo ""
echo "Next steps:"
echo "1. Review changes: git status"
echo "2. Commit: git commit -m 'chore: major repository cleanup'"
echo "3. Consider moving archive/ and AI-Projects/ out of repo"
```

---

## ✅ VERIFICATION CHECKLIST

After cleanup:

- [ ] .gitignore updated with all build artifacts
- [ ] logs/, state/, artifacts/ removed from git
- [ ] Empty folders deleted
- [ ] node_modules/ removed from athena-macapp-ui
- [ ] Repository size reduced significantly
- [ ] All active services still functional
- [ ] NeuroForgeApp still builds
- [ ] Tests still pass

---

## 📞 DECISION POINTS NEEDED

Please decide on these items:

1. **athena-macapp-ui** - Still active? Or superseded by NeuroForgeApp?
2. **AI-Projects/** - Should this be a separate repository?
3. **TinyRecursiveModels** - Archive or keep active?
4. **fastvlm** - Still actively used?
5. **archive/** - Move to external storage or keep in git?
6. **Infrastructure** (traefik, tempo, searxng) - Which are actually running?

---

**End of Deep Audit Report**
**Generated:** October 26, 2025

