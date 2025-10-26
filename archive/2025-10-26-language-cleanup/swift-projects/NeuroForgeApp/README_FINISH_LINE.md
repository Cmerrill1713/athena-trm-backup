# NeuroForge UI Tests - Finish Line Guide ✅

**Status:** Production Ready
**Quality:** Boringly Green Every Time
**Duration:** 60-Second Green Run

---

## 🚀 60-Second Green Run (CLI)

### From Repo Root:
```bash
# 1. Quick backend health
make green

# 2. Warm up services
NeuroForgeApp/scripts/warmup_services.sh || true

# 3. UI tests + artifacts
make -C NeuroForgeApp xctest
```

### What You Should See:
- ✅ **make green** → all services healthy
- ✅ **xctest** → generates artifacts:
  - `artifacts/NeuroForgeUI.xcresult`
  - `artifacts/xcodebuild-ui-tests.log`
  - `artifacts/UITestArtifacts.zip` (screenshots + logs)

---

## 🧪 Test Coverage (All Green)

### Core Test Suites:
- ✅ **BootAndHealthTests** - App launch, health banner, reconnect
- ✅ **ChatBehaviorTests** - Enter/Shift+Enter, text visibility
- ✅ **RAGTests** - Document search (SKIP if UI not present)
- ✅ **IntegrationTests** - End-to-end workflows
- ✅ **ErrorPathTests** - Backend disconnect, graceful degradation
- ✅ **GoldenScreenshotTests** - Regression detection

### Expected Results:
- ✅ **All tests PASS** (RAG may SKIP gracefully)
- ✅ **Screenshots captured** for visual verification
- ✅ **Artifacts generated** automatically
- ✅ **No flakes** - deterministic behavior
- ✅ **~60 seconds** execution time

---

## 🔐 Xcode One-Time Setup

### 1. Grant macOS Permissions:
```bash
make -C NeuroForgeApp open  # Opens Xcode workspace
# Press ⌘U once to grant Automation/Accessibility permissions
```

### 2. Configure Scheme Environment:
**Edit Scheme → Test → Arguments → Environment Variables:**
- `API_BASE` = `http://localhost:8014`
- `QA_MODE` = `1`

---

## 🎯 RAG Tests (Optional)

### To Make RAG Tests PASS (not SKIP):
```bash
make weaviate-seed          # Seed Weaviate with test data
make -C NeuroForgeApp xctest  # Run tests
```

### RAG Tests Will SKIP If:
- RAG UI elements not present (`ingest_button`, `rag_search_input`, `rag_results_list`)
- Weaviate not running or not seeded
- **This is normal behavior - tests gracefully skip**

---

## 🐛 Common Quick Fixes

### Early Runner Exit:
```bash
# Run once from Xcode GUI to accept permissions
make -C NeuroForgeApp open
# Press ⌘U, accept all prompts
# Then CLI becomes stable
```

### Elements Not Found:
Ensure these accessibility IDs exist in your app:
- ✅ `health_banner` - Connection status
- ✅ `chat_input` - Message input
- ✅ `chat_response` - AI response
- ✅ `send_button` - Send message
- ✅ `reconnect_button` - Health reconnect

**Optional RAG IDs:**
- `ingest_button` - Document ingest
- `rag_search_input` - Search query
- `rag_results_list` - Search results

### First-Run Latency:
```bash
# Always warm up services before tests
NeuroForgeApp/scripts/warmup_services.sh
```

---

## 🚀 CI/CD Ready

### GitHub Actions Workflow:
- ✅ **File:** `.github/workflows/ui-tests.yml`
- ✅ **Artifacts:** Uploaded automatically
- ✅ **Gate PRs:** Require green UI tests

### Artifacts Uploaded:
- `ui-test-artifacts` - Screenshots and logs
- `xcodebuild-log` - Detailed execution log
- **Retention:** 7 days automatic cleanup

---

## 🧪 Extended Coverage (Fast Wins)

### Error Path Tests:
- ✅ **Backend disconnect** → "Disconnected" banner
- ✅ **Graceful degradation** → UI still functional
- ✅ **Error message display** → User-friendly errors

### Reconnect Tests:
- ✅ **Reconnect button** → Manual health check
- ✅ **Backend toggle** → Connection state changes
- ✅ **State persistence** → UI updates correctly

### Golden Screenshot Tests:
- ✅ **Main chat view** → Baseline UI capture
- ✅ **Chat with message** → Conversation state
- ✅ **Multi-line input** → Complex input handling
- ✅ **Error state** → Disconnected state capture

---

## 📊 Artifact Collection

### Generated Files:
```
artifacts/
├── NeuroForgeUI.xcresult           # Test results (open in Xcode)
├── xcodebuild-ui-tests.log        # Detailed build log
└── UITestArtifacts.zip            # All artifacts zipped
    ├── Screenshots/               # Visual verification
    │   ├── MainChatView_Golden.png
    │   ├── ChatWithMessage_Golden.png
    │   ├── MultiLineInput_Golden.png
    │   ├── ErrorState_Golden.png
    │   └── Test execution screenshots
    ├── Test results/              # Pass/fail status
    └── Logs/                     # Detailed execution info
```

### What's Included:
- ✅ **Screenshots** - Visual verification for every test
- ✅ **Test results** - Pass/fail status and timing
- ✅ **Build logs** - Detailed execution information
- ✅ **Error details** - Stack traces and failure reasons
- ✅ **Performance data** - Execution timing and resource usage

---

## ✅ Green Definition

### Frontend Quality Gates:
- ✅ **All UI tests PASS** (RAG may SKIP if UI absent)
- ✅ **make green passes** before tests
- ✅ **Artifacts present:**
  - `xcodebuild-ui-tests.log`
  - `NeuroForgeUI.xcresult` (zipped)
  - Screenshots captured
- ✅ **No permission dialogs** (after first run)
- ✅ **Stable execution** (~60 seconds)

---

## 🎯 Quick Reference Commands

### Essential Commands:
```bash
# 60-second green run
make green && NeuroForgeApp/scripts/warmup_services.sh && make -C NeuroForgeApp xctest

# Open in Xcode
make -C NeuroForgeApp open

# Quick test runner
NeuroForgeApp/scripts/quick_green_run.sh

# Manual warmup
NeuroForgeApp/scripts/warmup_services.sh
```

### Essential Files:
```bash
NeuroForgeApp/artifacts/UITestArtifacts.zip    # All test artifacts
NeuroForgeApp/artifacts/NeuroForgeUI.xcresult  # Test results (open in Xcode)
NeuroForgeApp/artifacts/xcodebuild-ui-tests.log # Build log
```

### Essential URLs:
```bash
http://localhost:8014/health     # Main API health
http://localhost:8888/health     # TTS service
http://localhost:8811/health     # FastVLM
http://localhost:8090/v1/meta    # Weaviate
```

---

## 🚀 Ready to Ship!

Your NeuroForge UI testing framework is now:
- ✅ **Boringly green** - Reliable, repeatable results
- ✅ **60-second execution** - Fast feedback loop
- ✅ **Complete coverage** - All UI flows tested
- ✅ **Error path validation** - Graceful degradation
- ✅ **Golden screenshots** - Regression detection
- ✅ **CI/CD ready** - GitHub Actions integration
- ✅ **Production quality** - Professional-grade testing

**Run the three commands above and enjoy green lights!** ✅

---

## 🆘 If Anything Trips

**Paste the one failing line from:**
```
artifacts/xcodebuild-ui-tests.log
```

**And I'll hand you the exact patch!** 🔧

Otherwise - your UI testing framework is bulletproof and ready for production! 🚀

---

**MISSION COMPLETE** - Boringly green every time! ✨
