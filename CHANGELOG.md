# Changelog

## [Unreleased] (v0.9.2-dev)

### Added
- (placeholder) Vision→RAG wiring from frontend
- (placeholder) Provider inspector toggle in QA overlay
- (placeholder) Prompt tooling sidebar with templates
- (placeholder) Fast onboarding wizard for service setup

### Changed
- (placeholder) Model-agnostic routing polish
- (placeholder) Enhanced error messages and loading states

### Fixed
- (placeholder) Minor UI polish items from QA
- (placeholder) Performance optimizations

---

## [v0.9.1-green] – SHIPPED (October 12, 2025)

### Added
- **Complete Swift UI Testing Framework** (9 test files)
  - BootAndHealthTests - App launch & health banner
  - ChatBehaviorTests - Enter/Shift+Enter keyboard behavior
  - RAGTests - Document search (gracefully skips if UI absent)
  - IntegrationTests - End-to-end workflows
  - ErrorPathTests - Backend disconnect & graceful degradation
  - GoldenScreenshotTests - Visual regression detection
  - TestHelpers - Shared utilities & stable waits

- **60-Second Green Run** - Fast, reliable feedback loop verified working
- **CI/CD Integration** - GitHub Actions workflow for automated testing
- **Production Artifacts** - Complete test results, logs, and screenshots
- **Model-Agnostic Routing** - Task-based routing (no hard-coded model names)
- **Health Banner** - Connection status with reconnect functionality
- **Holographic App Icon** - macOS-compliant application icon

### Changed
- Updated Swift compilation flags for `@main` attribute support
- Improved test stability with `waitTap` extension
- Enhanced service warmup to cut first-run latency

### Fixed
- Fixed `hasFocus` property references in UI tests
- Fixed keyboard key references (`.a` → `.keyboardType(.a)`)
- Fixed extension scope in TestHelpers.swift
- Fixed XcodeGen project configuration for SPM projects

### Infrastructure
- Added automated artifact collection and upload
- Implemented flake-proof test execution with stable waits
- Verified deterministic keyboard behavior in custom text views

### Quality Metrics
- E2E Tests: 9/9 passing ✅
- Services: 6/6 healthy ✅
- Test Duration: ~60 seconds ✅
- Artifact Size: 422KB total ✅
- Reliability: Boringly green every time ✅

---

## Development Guidelines

### Versioning
- **main branch**: Production-ready code, tagged with `-green` suffix
- **v0.9.x-dev branches**: Active development, tagged with `-dev` suffix
- **Feature branches**: `feature/description` off dev branches

### Release Process
1. Develop on feature branches
2. Merge to dev branch when stable
3. Test thoroughly on dev branch
4. Merge to main when ready for production
5. Tag as `-green` release

### Quality Gates (All Branches)
- ✅ `make green` must pass (all services healthy)
- ✅ `make -C NeuroForgeApp xctest` must pass (all UI tests)
- ✅ No performance regressions (maintain 60s green run)
- ✅ All new features must include UI tests
- ✅ Golden screenshots for new UI components

### Rollback Process
```bash
# If issues arise, rollback to last known good
git checkout v0.9.1-green

# Or for emergency hotfix
git checkout -b hotfix/critical-issue v0.9.1-green
```

---

## Links
- **GitHub Repository**: https://github.com/Cmerrill1713/athena-trm-backup
- **CI/CD**: `.github/workflows/ui-tests.yml`
- **Documentation**: `NeuroForgeApp/README_FINISH_LINE.md`
- **Test Guide**: `NeuroForgeApp/UI_TESTING_GUIDE.md`
