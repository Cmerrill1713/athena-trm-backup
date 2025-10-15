# v0.9.2-dev Development Notes

**Branch**: v0.9.2-dev
**Based on**: v0.9.1-green
**Status**: Active Development
**Started**: October 12, 2025

---

## 🎯 Development Focus

### **Priority Features**
1. **Vision → RAG Quick Path** 📸
   - Upload image from Swift UI
   - Auto-analyze with FastVLM
   - Auto-persist to Weaviate
   - Surface in RAG search context

2. **Provider Inspector Toggle** 🔍
   - QA overlay for runtime routing
   - Override model selection
   - View request/response details
   - Toggle FastVLM/Ollama/TRM providers

3. **Prompt Tooling Sidebar** 🛠️
   - Quick-access template library
   - Category organization
   - One-click template insertion
   - Template variable substitution

4. **Golden Screenshot Diff in CI** 📊
   - Automatic visual regression detection
   - PR-based diff reports
   - Baseline management
   - Fail on threshold exceeded

---

## 🚀 Quick Start (Development Loop)

### **Essential Commands**
```bash
# 60-second green confidence loop
make green
NeuroForgeApp/scripts/warmup_services.sh || true
make -C NeuroForgeApp xctest

# Open test results
open NeuroForgeApp/artifacts/NeuroForgeUI.xcresult

# Full validation
make validate-green && make e2e-sweep
```

### **Feature Development Workflow**
```bash
# 1. Create feature branch
git checkout v0.9.2-dev
git pull origin v0.9.2-dev
git checkout -b feature/my-feature

# 2. Develop with continuous validation
# ... make changes ...
make green && make -C NeuroForgeApp xctest

# 3. Commit when green
git add -A
git commit -m "feat: add my feature"

# 4. Push and create PR to v0.9.2-dev
git push origin feature/my-feature
# Create PR on GitHub: feature/my-feature → v0.9.2-dev
```

---

## 🧪 Quality Gates (Mandatory)

### **Before Every Commit**
- ✅ `make green` passes (all services healthy)
- ✅ `make -C NeuroForgeApp xctest` passes (all UI tests)
- ✅ No new linter errors
- ✅ Code formatted (pre-commit hooks)

### **Before Every PR**
- ✅ All quality gates above
- ✅ New features have UI tests
- ✅ Golden screenshots updated if UI changed
- ✅ Documentation updated
- ✅ CHANGELOG.md updated

### **Performance Targets**
- 60-second green run maintained ✅
- No memory leaks
- Smooth UI (no janky animations)
- Fast startup (<2s to first render)

---

## 📁 Key Files & Locations

### **Swift UI Application**
```
NeuroForgeApp/
├── Sources/
│   ├── Config/APIBase.swift           # Backend routing
│   ├── Network/                       # API client
│   ├── Features/                      # UI components
│   │   ├── ChatView.swift             # Main chat interface
│   │   ├── KeyCatchingTextView.swift  # Input handling
│   │   └── (new features here)
│   └── Diagnostics/HealthBanner.swift # Service health
├── UITests/                           # All UI tests
└── scripts/                           # Automation
```

### **Configuration**
```
config/
├── routing_policy.json                # Model routing rules
└── vision_providers.json              # Vision provider config
```

### **Documentation**
```
NeuroForgeApp/
├── README_FINISH_LINE.md              # Complete guide
├── UI_TESTING_GUIDE.md                # Testing guide
└── PERMISSIONS_SETUP.md               # macOS setup

Root/
├── CHANGELOG.md                       # Version history
├── DEV_NOTES.md                       # This file
└── VERSION                            # Current version
```

---

## 🔧 Development Tips

### **Adding New UI Features**
1. Create SwiftUI view in `Sources/Features/`
2. Add accessibility identifiers for testing
3. Create corresponding test in `UITests/`
4. Add golden screenshots if UI component
5. Update health banner if affects services

### **Adding New Tests**
```swift
// UITests/MyFeatureTests.swift
import XCTest

final class MyFeatureTests: XCTestCase {
    func testMyFeature() {
        let app = UITestHelpers.launchApp()
        XCTAssertTrue(UITestHelpers.waitForAppReady(app))

        // Test implementation
        let element = app.buttons["my_feature_button"]
        element.waitTap()

        // Verify behavior
        XCTAssertTrue(/* assertion */)
    }
}
```

### **Debugging Test Failures**
```bash
# 1. Check the logs
tail -100 NeuroForgeApp/artifacts/xcodebuild-ui-tests.log

# 2. Open results in Xcode
open NeuroForgeApp/artifacts/NeuroForgeUI.xcresult

# 3. Run specific test
xcodebuild -project NeuroForgeApp/NeuroForgeApp.xcodeproj \
  -scheme NeuroForgeApp \
  -destination 'platform=macOS' \
  -only-testing:NeuroForgeAppUITests/MyFeatureTests/testMyFeature \
  test

# 4. Check service health
make green
```

---

## 🚧 Current Work

### **Active Features**
- [ ] Vision → RAG quick path (planning)
- [ ] Provider inspector toggle (not started)
- [ ] Prompt tooling sidebar (not started)

### **Known Issues**
- (None yet - track issues here as they arise)

### **Tech Debt**
- (Track technical debt here)

---

## 📊 Development Metrics

### **Progress Tracker**
- **Features Completed**: 0/4
- **Tests Added**: 0
- **Test Coverage**: 100% (maintained from v0.9.1-green)
- **Service Health**: 6/6 healthy
- **Build Time**: ~60s (maintained)

### **Weekly Goals**
- **Week 1**: Vision → RAG prototype
- **Week 2**: Provider inspector + prompt sidebar
- **Week 3**: Golden screenshot diffing
- **Week 4**: Polish + merge to main

---

## 🔗 Useful Links

### **Documentation**
- [UI Testing Guide](NeuroForgeApp/UI_TESTING_GUIDE.md)
- [Post-Ship Guide](NeuroForgeApp/POST_SHIP_COMPLETE.md)
- [Changelog](CHANGELOG.md)

### **External**
- [GitHub Repo](https://github.com/Cmerrill1713/athena-trm-backup)
- [CI/CD Workflows](.github/workflows/)
- [Latest Release](https://github.com/Cmerrill1713/athena-trm-backup/releases/tag/v0.9.1-green)

---

## 🆘 Emergency Procedures

### **Rollback to Stable**
```bash
# If v0.9.2-dev becomes unstable
git checkout main  # or v0.9.1-green

# Verify it's green
make green && make -C NeuroForgeApp xctest
```

### **Reset Feature Branch**
```bash
# If feature branch is broken
git checkout v0.9.2-dev
git branch -D feature/my-feature
git checkout -b feature/my-feature
```

### **Clean Build**
```bash
# If Xcode build is acting weird
cd NeuroForgeApp
rm -rf .build DerivedData artifacts/*.xcresult
xcodegen generate
make xctest
```

---

## 📝 Notes

### **Design Decisions**
- (Document major design decisions here)

### **Architecture Changes**
- (Track architectural changes here)

### **Performance Optimizations**
- (Track performance work here)

---

**Last Updated**: October 12, 2025
**Status**: Active Development 🚧
**Next Milestone**: Vision → RAG Quick Path Prototype
