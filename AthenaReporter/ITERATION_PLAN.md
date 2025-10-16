# Athena Swift UI - 10 Iteration Plan

**Base App:** AthenaReporter (~40,000 lines production code)  
**Goal:** Add comprehensive governance monitoring and control  
**Status:** Iteration 1 Complete ✅

---

## Iteration 1 - Remediation Monitor ✅ COMPLETE

**Goal:** Add basic remediation monitoring UI

**Deliverables:**

- ✅ RemediationMonitor.swift created (~500 lines)
- ✅ Three-tab interface (Metrics/Health/Events)
- ✅ Real-time polling from localhost:9112
- ✅ Service health indicators
- ✅ Success rate gauge
- ✅ Menu integration (⌘⇧R)

**Files Changed:**

- `RemediationMonitor.swift` (NEW)
- `AthenaReporter.swift` (modified)

**Tests:** Manual validation - app builds and runs ✅

**Status:** ✅ COMPLETE - App running with live monitoring

---

## Iteration 2 - Orchestrator Client & Models

**Goal:** Create structured API clients and data models

**Prompt for Cursor:**

```
ITERATION 2 - Orchestrator Client & Models

Goal: Implement OrchestratorClient, CanaryClient with async/await, timeout 3s,
token header if ATHENA_CONTROL_TOKEN set. Add models: Health, VerdictRequest,
ExecState, PromQueryResponse. Add unit tests with mocked URLProtocol.

Keep diffs < 300 LOC. Build+tests must pass.

Create:
- Services/OrchestratorClient.swift
- Services/CanaryClient.swift
- Services/PrometheusClient.swift
- Models/GovernanceModels.swift
- Services/NetworkClient.swift (base with timeout/token)
- Tests/ClientTests.swift

Connect to:
- http://localhost:9110 (orchestrator)
- http://localhost:9111 (canary)
- http://localhost:9112 (remediator) - already done
- http://localhost:9090 (prometheus)
```

**Acceptance:**

- [ ] All clients implement protocol
- [ ] Timeout set to 3s
- [ ] Token header support
- [ ] Models decode correctly
- [ ] Unit tests with mocks
- [ ] Build passes
- [ ] CHANGELOG updated

---

## Iteration 3 - Enhanced Dashboard

**Goal:** Dashboard with health, ECE gauge, verdict counters

**Prompt for Cursor:**

```
ITERATION 3 - Dashboard Health & Gauges

Goal: Create DashboardView showing:
- Service health (orch/canary/remediator)
- ECE gauge (query Prom: governance_ece_post)
- Verdict counters (governance_verdicts_total by label)
- Swift Charts line chart of ECE over last hour

Add DashboardViewModel with @Published state.
Add unit tests for view model.
Graceful fallback to placeholder on network error.

Keep diffs < 400 LOC.
```

**Acceptance:**

- [ ] DashboardView renders
- [ ] Health indicators show real data
- [ ] ECE gauge displays
- [ ] Charts render or show placeholder
- [ ] ViewModel tested
- [ ] Build+tests pass

---

## Iteration 4 - Verdict Submission Form

**Goal:** UI to submit verdicts to orchestrator

**Prompt for Cursor:**

```
ITERATION 4 - Verdict Form

Goal: VerdictView with form:
- task_id (TextField)
- verdict enum (Picker: PASS/SOFT_FAIL/HARD_FAIL)
- ece_post (Double input)
- entropy (Double input)
- actions (MultiSelect: ROLLBACK, CANARY_5PCT, etc.)

POST to /verdict endpoint.
Show idempotence feedback ("applied" vs "idempotent_skip").
Disable submit until valid.
Tests: payload building, mock success/dup/error.

Keep diffs < 400 LOC.
```

**Acceptance:**

- [ ] Form renders
- [ ] Validation works
- [ ] POST succeeds
- [ ] Idempotence shown
- [ ] Error handling
- [ ] Tests pass

---

## Iteration 5 - Canary Monitor

**Goal:** Dedicated canary monitoring panel

**Prompt for Cursor:**

```
ITERATION 5 - Canary Monitor

Goal: CanaryView displays:
- Canary health from :9111/health
- Window size, samples, last decision
- Query Prom for:
  - governance_solve_rate_delta
  - governance_violation_rate_delta
  - governance_canary_samples_total
- Status pill (PROMOTE/HOLD/ROLLBACK)

Tests: model decode, formatting, status logic.

Keep diffs < 350 LOC.
```

**Acceptance:**

- [ ] CanaryView renders
- [ ] Metrics display
- [ ] Status pill correct
- [ ] Prometheus queries work
- [ ] Tests pass

---

## Iteration 6 - Mode Switch (Safe)

**Goal:** Control Shadow/Canary/Enforce modes

**Prompt for Cursor:**

```
ITERATION 6 - Mode Switch

Goal: SettingsView with:
- Shadow/Canary/Enforce segmented control
- POST /mode with confirmation dialog
- Token header if ATHENA_CONTROL_TOKEN set
- "Dry run" toggle (/mode?dry_run=true)
- Gray out if endpoint missing

Tests: no crash when endpoint missing, confirmation flow.

Keep diffs < 300 LOC.
```

**Acceptance:**

- [ ] Mode switcher renders
- [ ] Confirmation dialog
- [ ] POST with token
- [ ] Dry run works
- [ ] Graceful missing endpoint
- [ ] Tests pass

---

## Iteration 7 - Resilience & Offline

**Goal:** Robust error handling and offline support

**Prompt for Cursor:**

```
ITERATION 7 - Resilience & Offline

Goal: Add:
- Retry/backoff (max 2 retries)
- Graceful empty states
- Loading spinners
- Cache last good metrics
- Polling cadence: 5s health, 15s metrics
- Pause when backgrounded

Tests: timeout handling, cache behavior.

Keep diffs < 350 LOC.
```

**Acceptance:**

- [ ] Retry logic works
- [ ] Empty states shown
- [ ] Spinners display
- [ ] Cache working
- [ ] Background pausing
- [ ] Tests pass

---

## Iteration 8 - Events & Alerts

**Goal:** Client-side event log and critical alerts

**Prompt for Cursor:**

```
ITERATION 8 - Observability UX

Goal: Add:
- "Events" list (client-side log)
- Append when verdict submitted or mode changed
- Critical alert banner when:
  - ECE > 0.08
  - Entropy >= 0.25
  - Violation spike detected
- Dismissible banners

Tests: banner rule logic, event appending.

Keep diffs < 300 LOC.
```

**Acceptance:**

- [ ] Events list shows
- [ ] Appends correctly
- [ ] Alert banners trigger
- [ ] Rules tested
- [ ] Dismissible
- [ ] Tests pass

---

## Iteration 9 - Fit & Finish

**Goal:** Professional UI polish

**Prompt for Cursor:**

```
ITERATION 9 - Fit & Finish

Goal: Polish:
- Unified typography system
- Icon system
- Haptic feedback on actions
- Accessibility labels
- Dynamic type support
- Dark mode refinement
- Color palette (SF Symbols + system colors)

Tests: Snapshot tests if infra exists; otherwise a11y labels only.

Keep diffs < 400 LOC.
```

**Acceptance:**

- [ ] Typography consistent
- [ ] Icons throughout
- [ ] Haptics on buttons
- [ ] Accessibility labels
- [ ] Dynamic type works
- [ ] Dark mode polished

---

## Iteration 10 - Release Readiness

**Goal:** Production deployment preparation

**Prompt for Cursor:**

```
ITERATION 10 - Release Readiness

Goal: Add:
- Diagnostics screen (versions, URLs, token status, last updates)
- Integration test (stub orch/canary, run Dashboard→Verdict→Dashboard)
- Smoke tests
- RELEASE_NOTES.md
- Ensure `xcodebuild build && test` passes

Keep diffs < 300 LOC.
```

**Acceptance:**

- [ ] Diagnostics screen
- [ ] Integration tests
- [ ] Smoke tests
- [ ] Build passes
- [ ] Tests pass
- [ ] RELEASE_NOTES complete

---

## Current Status

**✅ Iteration 1 COMPLETE**

- RemediationMonitor.swift created and integrated
- App builds successfully
- Running with live backend integration

**➡️ Ready for Iteration 2**

---

## How to Run Each Iteration

### Step 1: PLAN

```
Ask Cursor: "PLAN: Summarize the smallest change to meet [Iteration N] goal. List files to edit."
```

### Step 2: WRITE

```
Ask Cursor: "WRITE: Propose diff hunks file-by-file for [Iteration N]."
```

### Step 3: TEST

```
Ask Cursor: "TEST: Add or update unit tests for [Iteration N]."
```

### Step 4: RUN

```
cd /Users/christianmerrill/Documents/GitHub/AthenaReporter
swiftc -parse *.swift
# Or full build:
# xcodebuild -scheme AthenaReporter build
```

### Step 5: DOC

```
Ask Cursor: "DOC: Update CHANGELOG.md for iteration N."
```

---

## Acceptance Checklist Template

```markdown
### Swift UI Iteration N — Acceptance

- [ ] Builds: `swift build` or `swiftc -o AthenaReporter *.swift`
- [ ] Tests pass: unit tests execute
- [ ] No crash when endpoints down
- [ ] Feature works as specified
- [ ] CHANGELOG updated
- [ ] Diffs ≤ 500 LOC
```

---

## Build Commands

### Quick Compile Check

```bash
cd /Users/christianmerrill/Documents/GitHub/AthenaReporter
swiftc -parse *.swift
```

### Full Build

```bash
cd /Users/christianmerrill/Documents/GitHub/AthenaReporter
swiftc -o AthenaReporter *.swift -framework SwiftUI -framework AppKit -framework AVFoundation
```

### Run

```bash
./AthenaReporter
```

---

## Progress Tracking

| Iteration | Feature             | Status | LOC  | Date   |
| --------- | ------------------- | ------ | ---- | ------ |
| 1         | Remediation Monitor | ✅     | ~500 | Oct 16 |
| 2         | Orchestrator Client | ⏳     | TBD  | TBD    |
| 3         | Enhanced Dashboard  | ⏳     | TBD  | TBD    |
| 4         | Verdict Form        | ⏳     | TBD  | TBD    |
| 5         | Canary Monitor      | ⏳     | TBD  | TBD    |
| 6         | Mode Switch         | ⏳     | TBD  | TBD    |
| 7         | Resilience          | ⏳     | TBD  | TBD    |
| 8         | Events & Alerts     | ⏳     | TBD  | TBD    |
| 9         | Polish              | ⏳     | TBD  | TBD    |
| 10        | Release             | ⏳     | TBD  | TBD    |

---

**Current:** Iteration 1 complete, ready to begin Iteration 2  
**Next:** Copy Iteration 2 prompt and paste into Cursor Chat
