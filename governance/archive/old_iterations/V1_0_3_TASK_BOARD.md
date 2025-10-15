# 🎯 v1.0.3 Task Board

**Target Ship**: November 1, 2025  
**Branch**: `feature/v1.0.3-morph-cleanup`  
**Status**: 📋 **PLANNING**

---

## 🎯 Goals

1. **Restore iOS Compatibility** - Make app work on iOS again
2. **Pay Down Lint Debt** - Reduce warnings from 1,673 to <500
3. **Enable Photoreal Avatar** - Activate cinematic morph (rights-pending)
4. **Cross-Platform Excellence** - Clean separation of iOS/macOS code

---

## 📊 Sprint Overview

### Sprint 1: Platform Fixes (Week 1)
**Goal**: iOS compatibility restored, lint debt <1000

### Sprint 2: Quality & Testing (Week 2)
**Goal**: Lint debt <500, comprehensive tests

### Sprint 3: Avatar Activation (Week 3)
**Goal**: Photoreal ready, morph tested

### Sprint 4: Polish & Ship (Week 4)
**Goal**: Final QA, documentation, release

---

## 🔨 Sprint 1: Platform Fixes

### 1.1 iOS Code Restoration
**Priority**: P0 (Blocker)  
**Estimate**: 3 days

**Tasks**:
- [ ] Unquarantine iOS files from `archive/ios-code/`
- [ ] Replace `UIDevice` with platform-appropriate equivalents:
  ```swift
  #if os(iOS)
  import UIKit
  let device = UIDevice.current
  #elseif os(macOS)
  import AppKit
  let device = ProcessInfo.processInfo.hostName
  #endif
  ```
- [ ] Add platform guards to all iOS-specific code
- [ ] Test on iOS simulator
- [ ] Test on macOS

**Files to Fix**:
- `AuthInterceptor.swift` (UIDevice → platform guards)
- `AvatarSettingsView.swift` (iOS-only modifiers)
- `MobileMetricsService.swift` (platform-specific metrics)
- `FrontsideBridge.swift` (AppDelegate integration)

**Acceptance Criteria**:
- ✅ App builds on both iOS and macOS
- ✅ No UIDevice errors
- ✅ Platform-specific features work correctly
- ✅ Tests pass on both platforms

---

### 1.2 ObservableObject Conformance
**Priority**: P0 (Blocker)  
**Estimate**: 1 day

**Tasks**:
- [ ] Make `PromptEngineerService` conform to `ObservableObject`
- [ ] Add `@Published` properties where needed
- [ ] Update view bindings
- [ ] Test state updates

**Code**:
```swift
final class PromptEngineerService: ObservableObject {
    @Published var status: ServiceStatus?
    @Published var isProcessing: Bool = false
    // ...
}
```

**Acceptance Criteria**:
- ✅ Service conforms to `ObservableObject`
- ✅ `@StateObject` usage works
- ✅ UI updates reactively

---

### 1.3 Lint Debt Paydown Phase 1
**Priority**: P1 (High)  
**Estimate**: 2 days

**Goal**: 1,673 → <1000 warnings

**Auto-Fix**:
```bash
# Remove unused imports
autoflake -ir --remove-all-unused-imports src/ scripts/

# Remove unused variables
autoflake -ir --remove-unused-variables src/ scripts/

# Format
black src/ scripts/
isort src/ scripts/
```

**Manual Fixes**:
- [ ] Convert lambda assignments to def (E731) - ~80 instances
- [ ] Fix == True/False comparisons (E712) - ~70 instances
- [ ] Add specific exception types (E722) - high priority only

**Acceptance Criteria**:
- ✅ Warnings reduced to <1000
- ✅ CI still green
- ✅ No functionality broken

---

## 🧪 Sprint 2: Quality & Testing

### 2.1 Lint Debt Paydown Phase 2
**Priority**: P1 (High)  
**Estimate**: 3 days

**Goal**: <1000 → <500 warnings

**Focus Areas**:
- [ ] Fix bare excepts in critical paths (E722)
- [ ] Fix import order violations (E402)
- [ ] Clean up test files
- [ ] Remove dead code

**Acceptance Criteria**:
- ✅ Warnings <500
- ✅ All critical paths have proper exception handling
- ✅ Import order consistent

---

### 2.2 Unit Test Coverage
**Priority**: P2 (Medium)  
**Estimate**: 2 days

**Tasks**:
- [ ] Add tests for `KeyCatchingTextEditor`
- [ ] Add tests for `FirstResponderKeeper`
- [ ] Add tests for avatar state management
- [ ] Add tests for platform guards

**Target**: 60% coverage on new code

**Acceptance Criteria**:
- ✅ Core components have tests
- ✅ Tests pass on CI
- ✅ Coverage report generated

---

### 2.3 Performance Profiling
**Priority**: P2 (Medium)  
**Estimate**: 1 day

**Tasks**:
- [ ] Profile app startup time
- [ ] Profile avatar rendering
- [ ] Identify bottlenecks
- [ ] Optimize hot paths

**Targets**:
- Startup: <2s
- Avatar render: <16ms (60fps)
- Memory: <200MB idle

---

## 🎭 Sprint 3: Avatar Activation

### 3.1 Photoreal Avatar Rights
**Priority**: P0 (Blocker for activation)  
**Estimate**: N/A (external)

**Tasks**:
- [ ] Complete rights verification
- [ ] Document provenance
- [ ] Get legal clearance
- [ ] Update `PHOTOREAL_RIGHTS_VERIFIED` flag

**Acceptance Criteria**:
- ✅ Rights verified and documented
- ✅ Legal approval received
- ✅ Flag set to `true`

---

### 3.2 Cinematic Morph Implementation
**Priority**: P1 (High)  
**Estimate**: 3 days

**Tasks**:
- [ ] Remove `#if AVATAR_API_ENABLED` guards
- [ ] Namespace conflicting types
- [ ] Implement morph animation
- [ ] Add awareness-driven triggers
- [ ] Test smooth transitions

**Features**:
- Ghost ↔ photoreal fade (1.2s)
- Awareness threshold triggers (0.65)
- Hysteresis to prevent flickering (0.20)
- Idle timeout (120s)

**Acceptance Criteria**:
- ✅ Smooth morph animation
- ✅ Awareness-driven triggers work
- ✅ No visual glitches
- ✅ Performant (60fps)

---

### 3.3 Backend Avatar Controller
**Priority**: P1 (High)  
**Estimate**: 2 days

**Tasks**:
- [ ] Enable avatar API routes
- [ ] Test Redis state management
- [ ] Add Prometheus metrics
- [ ] Implement rollback mechanism

**Already Implemented** (just needs testing):
- `/v1/avatar/status`
- `/v1/avatar/switch`
- Redis state tracking
- Feature flags

**Acceptance Criteria**:
- ✅ API endpoints work
- ✅ State persists correctly
- ✅ Metrics reported
- ✅ Rollback tested

---

## 🚀 Sprint 4: Polish & Ship

### 4.1 Final QA
**Priority**: P0 (Blocker)  
**Estimate**: 2 days

**Tasks**:
- [ ] Full regression test
- [ ] Test on multiple macOS versions
- [ ] Test on iOS devices
- [ ] Performance verification
- [ ] Security audit

**Acceptance Criteria**:
- ✅ No P0/P1 bugs
- ✅ All platforms working
- ✅ Performance targets met

---

### 4.2 Documentation
**Priority**: P1 (High)  
**Estimate**: 1 day

**Tasks**:
- [ ] Update README.md
- [ ] Update API documentation
- [ ] Write migration guide (v1.0.2 → v1.0.3)
- [ ] Update operator's runbook
- [ ] Create release notes

**Acceptance Criteria**:
- ✅ All docs updated
- ✅ Migration guide tested
- ✅ Release notes reviewed

---

### 4.3 Release Preparation
**Priority**: P0 (Blocker)  
**Estimate**: 1 day

**Tasks**:
- [ ] Create `v1.0.3` tag
- [ ] Build release artifacts
- [ ] Test on clean system
- [ ] Prepare rollback plan
- [ ] Schedule deployment

---

## 📋 Backlog (Future)

### Nice-to-Haves (v1.1.0)
- [ ] Advanced avatar expressiveness (eyes, subtle motion)
- [ ] Speech energy visualization
- [ ] Multiple avatar identities
- [ ] Custom avatar training
- [ ] Voice-driven animations

### Technical Debt
- [ ] Reduce lint warnings to <50
- [ ] Increase test coverage to 80%
- [ ] Add E2E tests
- [ ] Performance optimization
- [ ] Accessibility improvements

---

## 🎯 Success Metrics

### Code Quality
- Lint warnings: <500 (from 1,673)
- Test coverage: >60%
- Build time: <10s
- CI success rate: >95%

### Functionality
- iOS + macOS working
- Photoreal avatar active
- Smooth morph transitions
- Zero regressions

### Performance
- Startup: <2s
- Avatar render: <16ms
- Memory: <200MB
- Latency p95: <500ms

---

## 🔄 Daily Standup Template

```markdown
**Yesterday**:
- What I completed

**Today**:
- What I'm working on

**Blockers**:
- What's blocking me

**Lint Progress**:
- Current warning count: XXX
- Target: <500
```

---

## 📊 Progress Tracking

| Sprint | Status | Warnings | Completion |
|--------|--------|----------|------------|
| Sprint 1 | 📋 Planning | 1,673 | 0% |
| Sprint 2 | 📋 Planned | Target: <1000 | - |
| Sprint 3 | 📋 Planned | Target: <500 | - |
| Sprint 4 | 📋 Planned | Target: <500 | - |

---

## 🏁 Definition of Done

A task is "done" when:
- [ ] Code complete and reviewed
- [ ] Tests written and passing
- [ ] Documentation updated
- [ ] Lint warnings not increased
- [ ] CI passing
- [ ] Deployed to staging
- [ ] Accepted by product owner

---

**Board Owner**: [Your Name]  
**Last Updated**: October 14, 2025  
**Next Review**: October 21, 2025

*"Progress over perfection. Ship incrementally."*

