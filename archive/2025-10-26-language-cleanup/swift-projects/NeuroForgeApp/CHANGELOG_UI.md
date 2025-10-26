# NeuroForgeApp UI Changelog

All notable changes to the NeuroForgeApp Swift UI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Added

- Full governance backend integration
- `GovernanceClient.swift` - HTTP client for orchestrator communication
- `GovernanceViewModel.swift` - MVVM state management with retry logic
- `GovernanceDashboardLiveView.swift` - Real-time dashboard UI
- Health check with auto-refresh (5s interval)
- Verdict submission form with validation
- Real-time metrics display (verdict counts, remediation stats)
- Offline verdict queue (saves to `~/Library/Application Support/Athena/PendingVerdicts.jsonl`)
- Retry logic with jitter (3 attempts, 200-800ms delays)
- OSLog integration for structured logging

### Changed

- Updated main app to use new governance components
- Improved error handling with detailed messages
- Enhanced UI with status badges and color-coded metrics

### Fixed

- Build errors in `AvatarNotificationService` (UserNotifications bundle issue)
- Type conflicts in `AvatarKit/AvatarTypes.swift`
- UIDevice references replaced with macOS equivalents

---

## [Iteration 1] - 2025-10-16

### User Story

**As a** governance operator  
**I want** to see the orchestrator health status in real-time  
**So that** I know when the system is operational

### Acceptance Criteria

- [x] Health badge shows 🟢 when orchestrator is up
- [x] Health badge shows 🔴 when orchestrator is down
- [x] Status message updates every 5 seconds
- [x] Manual refresh button available
- [x] Error messages displayed clearly

### Implementation

- Created `GovernanceClient` with health check endpoint
- Created `GovernanceViewModel` with auto-refresh timer
- Created health status UI with color-coded indicators
- Added structured logging with OSLog

### Files Added

- `NeuroForgeApp/Sources/Governance/GovernanceClient.swift` (370 lines)
- `NeuroForgeApp/Sources/Governance/GovernanceViewModel.swift` (290 lines)
- `NeuroForgeApp/Sources/Governance/GovernanceDashboardLiveView.swift` (480 lines)

### Testing

- [x] Health check connects to `localhost:9110`
- [x] UI updates when orchestrator stops/starts
- [x] Auto-refresh works every 5 seconds
- [x] Manual refresh triggers immediately

### Screenshots

- `docs/screenshots/iteration-1-health-status.png` (TODO)

---

## [Iteration 2] - TBD

### User Story

**As a** governance operator  
**I want** to submit verdicts through the UI  
**So that** I can test the governance system manually

### Acceptance Criteria

- [ ] Form with task ID, verdict type, actions
- [ ] Submit button disabled when offline
- [ ] Success/error feedback shown
- [ ] Idempotent submissions detected
- [ ] Metrics update after submission

### Status

⏳ Pending

---

## [Iteration 3] - TBD

### User Story

**As a** governance operator  
**I want** to see verdict counts in real-time  
**So that** I can monitor system activity

### Acceptance Criteria

- [ ] PASS/SOFT_FAIL/HARD_FAIL counts displayed
- [ ] Counts refresh every 5 seconds
- [ ] Visual indicators (colors, icons)
- [ ] Historical trend (optional)

### Status

⏳ Pending

---

## [Iteration 4] - TBD

### User Story

**As a** governance operator  
**I want** to see remediation metrics  
**So that** I can track auto-remediation performance

### Acceptance Criteria

- [ ] Requested/completed/promoted/rolled back counts
- [ ] Success rate calculation
- [ ] Visual charts (Swift Charts)
- [ ] Refresh with verdict counts

### Status

⏳ Pending

---

## [Future Iterations]

### Iteration 5: Settings Panel

- Orchestrator URL configuration
- Refresh interval adjustment
- Dark mode toggle
- Queue management

### Iteration 6: Offline Mode Enhancement

- Visual queue indicator
- Manual flush button
- Queue persistence across restarts
- Failed verdict retry UI

### Iteration 7: Menu Bar Widget

- Status indicator (🟢/🟡/🔴)
- Last verdict count
- Quick actions menu
- Click to open dashboard

### Iteration 8: Notifications

- Verdict result notifications
- Remediation completion alerts
- Error notifications
- User preferences

### Iteration 9: Error Recovery UI

- Retry button for failed verdicts
- View error logs
- Export logs button
- Clear error history

### Iteration 10: Release Polish

- App icon
- About window
- Help documentation
- DMG package creation
- Code signing

---

## Technical Debt

### Known Issues

- [ ] `AvatarNotificationService` causes crash when run as CLI app (needs proper bundle)
- [ ] SwiftLint not configured yet (optional)
- [ ] No unit tests yet for ViewModel
- [ ] No UI tests yet for dashboard

### Future Improvements

- [ ] Add ViewInspector for snapshot testing
- [ ] Add mock `GovernanceClient` for tests
- [ ] Add Swift Charts for trend visualization
- [ ] Add keyboard shortcuts for actions
- [ ] Add accessibility audit
- [ ] Add performance profiling

---

## Dependencies

- Swift 5.9+
- macOS 14.0+ (Sonoma)
- Foundation
- SwiftUI
- OSLog

### Optional

- SwiftLint (for linting)
- ViewInspector (for snapshot tests)
- Swift Charts (for visualizations)

---

## Build Information

### Current Build

- **Version:** 0.1.0 (Iteration 1)
- **Build Date:** 2025-10-16
- **Compiler:** Swift 5.9
- **Target:** macOS 14.0+

### Build Commands

```bash
# Full verification
make -f Makefile.ui ui-verify

# Quick build
cd NeuroForgeApp && swift build

# Run tests
cd NeuroForgeApp && swift test

# Run app
cd NeuroForgeApp && .build/debug/NeuroForgeApp
```

---

## Contributors

- Christian Merrill (@Cmerrill1713)
- Cursor AI Assistant

---

**Note:** This changelog is updated after each iteration. Screenshots and detailed implementation notes are added as development progresses.
