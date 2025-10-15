# Changelog - v0.9.2-dev (In Development)

**Branch:** v0.9.2-dev
**Started:** October 12, 2025
**Status:** Active Development
**Based on:** v0.9.1-green

---

## 🎯 Development Goals

### **Priority Features**
1. **Vision → RAG Context Drop-in** 🎨
   - Upload image via Swift UI
   - Extract text/objects with FastVLM
   - Auto-ingest to Weaviate
   - Use as context in chat

2. **Prompt Tooling Sidebar** 🛠️
   - Quick prompt templates library
   - Chat history browser
   - Golden prompts collection
   - One-click template apply

3. **LLM Router Inspector** 🔍
   - Runtime backend route toggle
   - Model selection override
   - Request/response inspector
   - Performance metrics display

4. **Fast Onboarding Wizard** 🚀
   - Step-by-step API setup
   - Service health checks
   - Test prompt validation
   - One-click configuration

5. **Golden Screenshot Diffing** 📸
   - Automatic PR UI regression checks
   - Visual diff viewer
   - Baseline management
   - CI/CD integration

---

## 🚧 In Progress

### **Features**
- [ ] Vision → RAG context drop-in
- [ ] Prompt tooling sidebar
- [ ] LLM router inspector
- [ ] Fast onboarding wizard
- [ ] Golden screenshot diffing

### **Improvements**
- [ ] Enhanced error messages
- [ ] Better loading states
- [ ] Keyboard shortcuts
- [ ] Multi-window support

### **Infrastructure**
- [ ] Additional UI tests for new features
- [ ] Performance benchmarks
- [ ] Memory usage monitoring
- [ ] Crash reporting

---

## 📝 Unreleased Changes

### **Added**
- Development branch v0.9.2-dev created
- Changelog template for tracking development
- Roadmap for v0.9.2 features

### **Changed**
- (None yet)

### **Fixed**
- (None yet)

### **Removed**
- (None yet)

---

## 🧪 Testing Strategy

### **New Test Requirements**
- All new features must include UI tests
- Golden screenshots for new UI components
- Error path testing for new functionality
- Integration tests for RAG/Vision features

### **Quality Gates**
- ✅ All existing tests must pass
- ✅ New features must have >85% test coverage
- ✅ No performance regressions (60s green run maintained)
- ✅ All services remain healthy (6/6)

---

## 🔄 Development Workflow

### **Feature Development**
```bash
# 1. Create feature branch from v0.9.2-dev
git checkout v0.9.2-dev
git pull origin v0.9.2-dev
git checkout -b feature/my-feature

# 2. Develop and test
make green
NeuroForgeApp/scripts/warmup_services.sh || true
make -C NeuroForgeApp xctest

# 3. Commit when green
git add -A
git commit -m "feat: add my feature"

# 4. Push and create PR to v0.9.2-dev
git push origin feature/my-feature
```

### **Merge to v0.9.2-dev**
```bash
# After PR approval
git checkout v0.9.2-dev
git merge --no-ff feature/my-feature
git push origin v0.9.2-dev
```

### **Promote to main (when stable)**
```bash
# After v0.9.2-dev is stable
git checkout main
git merge --no-ff v0.9.2-dev
git tag v0.9.2-green
git push origin main --tags
```

---

## 📊 Development Metrics

### **Current Status**
- **Branch Created**: October 12, 2025
- **Features Completed**: 0/5
- **Tests Added**: 0
- **Lines Changed**: TBD
- **Contributors**: 1

### **Quality Indicators**
- **Test Pass Rate**: 100% (baseline from v0.9.1-green)
- **Service Health**: 6/6 healthy
- **Build Time**: ~60s (maintained)
- **Test Flakiness**: 0% (target)

---

## 🎯 Feature Specifications

### **1. Vision → RAG Context Drop-in**

**User Story:**
> As a user, I want to upload an image to the chat, have it analyzed by FastVLM, and automatically ingested into RAG context, so I can ask questions about visual content.

**Technical Approach:**
- Add image picker to Swift UI (NSOpenPanel)
- Send image to FastVLM for analysis
- Parse FastVLM response (objects, text, descriptions)
- Auto-ingest to Weaviate with metadata
- Display visual thumbnail in chat
- Use image context in subsequent queries

**Acceptance Criteria:**
- [ ] User can select image via file picker
- [ ] Image displays as thumbnail in chat
- [ ] FastVLM analysis runs automatically
- [ ] Results ingested to Weaviate
- [ ] User can query about image content
- [ ] Error handling for failed analysis
- [ ] UI tests for image upload flow
- [ ] Golden screenshots for image display

---

### **2. Prompt Tooling Sidebar**

**User Story:**
> As a user, I want a sidebar with quick-access prompt templates and chat history, so I can reuse effective prompts and navigate past conversations.

**Technical Approach:**
- Add collapsible sidebar to Swift UI
- SQLite or JSON file for prompt storage
- Template variables ({{variable}}) support
- Category organization (coding, writing, etc.)
- Search/filter functionality
- Export/import templates

**Acceptance Criteria:**
- [ ] Sidebar toggles with keyboard shortcut
- [ ] Templates organized by category
- [ ] One-click template insertion
- [ ] Template variable substitution
- [ ] Search filters templates
- [ ] Import/export functionality
- [ ] UI tests for sidebar interactions
- [ ] Golden screenshots for sidebar states

---

### **3. LLM Router Inspector**

**User Story:**
> As a developer, I want to inspect and override LLM routing decisions at runtime, so I can test different models and debug routing issues.

**Technical Approach:**
- Debug panel in Swift UI (dev mode only)
- Display current route for each request
- Override dropdown for model selection
- Request/response JSON viewer
- Latency and token count display
- Route history log

**Acceptance Criteria:**
- [ ] Debug panel accessible via keyboard shortcut
- [ ] Current route displayed for each message
- [ ] User can override model selection
- [ ] Request/response details visible
- [ ] Performance metrics tracked
- [ ] Route history logged
- [ ] Only available in QA_MODE=1
- [ ] UI tests for inspector interactions

---

### **4. Fast Onboarding Wizard**

**User Story:**
> As a new user, I want a step-by-step setup wizard, so I can configure all services and verify they're working correctly.

**Technical Approach:**
- Multi-step wizard in Swift UI
- Service health check per step
- Auto-discovery of localhost services
- Test prompt execution
- Configuration file generation
- Skip option for advanced users

**Acceptance Criteria:**
- [ ] Wizard launches on first run
- [ ] Each step validates service health
- [ ] Clear error messages for failures
- [ ] Test prompt runs successfully
- [ ] Config written to disk
- [ ] Can skip wizard if desired
- [ ] UI tests for wizard flow
- [ ] Golden screenshots for each step

---

### **5. Golden Screenshot Diffing**

**User Story:**
> As a developer, I want automatic visual regression detection on PRs, so UI changes are caught before merge.

**Technical Approach:**
- Extend existing golden screenshot tests
- Pixel-diff comparison on CI
- Generate diff images for PRs
- Baseline management commands
- Approve/reject workflow
- GitHub Actions integration

**Acceptance Criteria:**
- [ ] CI runs visual diff on PRs
- [ ] Diff images attached as artifacts
- [ ] Clear pass/fail status
- [ ] Easy baseline update workflow
- [ ] Ignore acceptable differences (timestamps, etc.)
- [ ] Fast execution (<2min)
- [ ] Integration with existing xctest
- [ ] Documentation for workflow

---

## 🐛 Known Issues (Development)

### **Inherited from v0.9.1-green**
- RAG tests skip by default (intentional)
- macOS permissions required on first run
- Chat endpoint warmup shows warning on first run

### **New Issues**
- (Track new issues here as they arise)

---

## 📚 Documentation Updates Needed

- [ ] Add image upload guide
- [ ] Document prompt template format
- [ ] Inspector keyboard shortcuts
- [ ] Wizard troubleshooting guide
- [ ] Visual diff workflow

---

## 🔗 Related Links

- **Base Version**: v0.9.1-green
- **Branch**: v0.9.2-dev
- **Main Repo**: https://github.com/Cmerrill1713/athena-trm-backup
- **CI/CD**: `.github/workflows/ui-tests.yml`

---

## 📅 Development Timeline

### **Week 1** (Oct 12-18, 2025)
- [x] Branch created
- [ ] Vision → RAG context drop-in (prototype)
- [ ] Prompt tooling sidebar (basic UI)

### **Week 2** (Oct 19-25, 2025)
- [ ] LLM router inspector
- [ ] Fast onboarding wizard

### **Week 3** (Oct 26 - Nov 1, 2025)
- [ ] Golden screenshot diffing
- [ ] Polish and bug fixes

### **Week 4** (Nov 2-8, 2025)
- [ ] Final testing
- [ ] Documentation updates
- [ ] Promote to v0.9.2-green

---

## 🚀 Next Actions

1. **Choose First Feature** - Pick from priority list
2. **Create Feature Branch** - `feature/vision-rag-drop-in`
3. **Scaffold UI** - Basic Swift UI components
4. **Write Tests** - UI tests for new feature
5. **Implement** - Build the feature
6. **Validate Green** - Run full test suite
7. **Merge to v0.9.2-dev** - Create PR and merge

---

**Status**: Active Development 🚧
**Based on**: v0.9.1-green ✅
**Target**: v0.9.2-green 🎯
**ETA**: 4 weeks (~Nov 8, 2025)

---

*This changelog will be updated as features are completed. Each feature merge should update the "Unreleased Changes" section.*
