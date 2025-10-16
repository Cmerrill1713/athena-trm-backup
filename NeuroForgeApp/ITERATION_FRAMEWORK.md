# NeuroForgeApp Iteration Framework

**Goal:** Production-grade Governance Dashboard (SwiftUI + Governance Backend)

---

## Iteration Loop (Repeat 10×)

### Step 1: Pick User Story

- Select ONE story from `backlog.md`
- Ensure it's testable and has clear acceptance criteria
- Mark story as "In Progress"

### Step 2: Implement

- Write the Swift code (View/ViewModel/Model)
- Follow MVVM pattern
- Add inline documentation
- Use `@MainActor` for UI state
- Use `async/await` for network calls

### Step 3: Test

- Add snapshot test (SwiftUI Preview or ViewInspector if available)
- Wire to `GovernanceClient.swift`
- Verify against live orchestrator (port 9110)
- Test offline behavior (stop orchestrator, verify graceful degradation)

### Step 4: E2E Test

- Add 1 E2E UI test using XCTest
- Test the complete user flow
- Verify integration with backend
- Test error scenarios

### Step 5: Document

- Update `CHANGELOG_UI.md` with changes
- Add screenshot to `docs/screenshots/`
- Update `backlog.md` (mark story complete)
- Add any new API endpoints to docs

### Step 6: Verify

```bash
make -f Makefile.ui ui-verify
```

- Must pass: build, tests, lint
- No warnings allowed
- No TODO comments in production code

### Step 7: Fix or Ship

- If verification fails:
  - Collect logs from `.build/debug/`
  - Fix issues
  - Re-run verification
- If verification passes:
  - Commit changes
  - Move to next iteration

---

## Quick Reference Commands

```bash
# Full check
make -f Makefile.ui ui-full-check

# Just build
make -f Makefile.ui ui-build

# Run app
make -f Makefile.ui ui-run

# Test backend integration
make -f Makefile.ui ui-gov-test
```

---

**Use this file as your Cursor iteration guide!**
