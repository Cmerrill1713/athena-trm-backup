# NeuroForgeApp UI Backlog

Sprint planning and user stories for the governance dashboard.

---

## Iteration 1: Foundation ✅ COMPLETE

### User Stories

#### ✅ GOV-001: Orchestrator Health Check

**As a** governance operator  
**I want** to see the orchestrator health status in real-time  
**So that** I know when the system is operational

**Acceptance Criteria:**

- [x] Health badge shows 🟢 when orchestrator is up
- [x] Health badge shows 🔴 when orchestrator is down
- [x] Status message updates every 5 seconds
- [x] Manual refresh button available
- [x] Error messages displayed clearly

**Priority:** P0 (Critical)  
**Effort:** 3 points  
**Status:** ✅ Complete  
**Completed:** 2025-10-16

---

## Iteration 2: Verdict Submission 🔄 IN PROGRESS

### User Stories

#### GOV-002: Submit Verdict Form

**As a** governance operator  
**I want** to submit verdicts through the UI  
**So that** I can test the governance system manually

**Acceptance Criteria:**

- [ ] Form with task ID input
- [ ] Verdict type selector (PASS/SOFT_FAIL/HARD_FAIL)
- [ ] Actions multi-select (PROMOTE/HOLD/QUARANTINE/ROLLBACK/FREEZE)
- [ ] Submit button disabled when offline
- [ ] Success/error feedback shown clearly
- [ ] Idempotent submissions detected and flagged

**Priority:** P0 (Critical)  
**Effort:** 5 points  
**Status:** 🔄 In Progress

**Technical Notes:**

- Use `VerdictRequest` model from `GovernanceClient`
- Validate task ID format
- Show loading spinner during submission
- Display response status prominently

---

#### GOV-003: Demo Verdict Button

**As a** developer  
**I want** a quick "send demo verdict" button  
**So that** I can test the system without filling forms

**Acceptance Criteria:**

- [ ] One-click demo verdict submission
- [ ] Auto-generates task ID with timestamp
- [ ] Always sends PASS verdict
- [ ] Disabled when orchestrator offline
- [ ] Shows success/error feedback

**Priority:** P1 (High)  
**Effort:** 2 points  
**Status:** ✅ Complete (already implemented in VM)

---

## Iteration 3: Metrics Display ⏳ PENDING

### User Stories

#### GOV-004: Verdict Counts Dashboard

**As a** governance operator  
**I want** to see verdict counts in real-time  
**So that** I can monitor system activity

**Acceptance Criteria:**

- [ ] PASS count displayed with green badge
- [ ] SOFT_FAIL count displayed with yellow badge
- [ ] HARD_FAIL count displayed with red badge
- [ ] Counts refresh every 5 seconds
- [ ] Total verdicts shown
- [ ] Empty state for zero verdicts

**Priority:** P0 (Critical)  
**Effort:** 3 points  
**Status:** ✅ Complete (UI exists, needs testing)

---

#### GOV-005: Remediation Metrics

**As a** governance operator  
**I want** to see auto-remediation metrics  
**So that** I can track remediation performance

**Acceptance Criteria:**

- [ ] Requested count
- [ ] Completed count
- [ ] Promoted count
- [ ] Rolled back count
- [ ] Failed count
- [ ] Success rate percentage
- [ ] Visual indicators (colors)

**Priority:** P1 (High)  
**Effort:** 4 points  
**Status:** 🔄 In Progress (UI exists, needs data verification)

---

## Iteration 4: Settings & Configuration ⏳ PENDING

### User Stories

#### GOV-006: Settings Panel

**As a** governance operator  
**I want** to configure the app settings  
**So that** I can customize the behavior

**Acceptance Criteria:**

- [ ] Orchestrator URL input (env var or manual)
- [ ] Refresh interval slider (1-30 seconds)
- [ ] Auto-refresh toggle
- [ ] Dark mode toggle
- [ ] Queue management settings
- [ ] Save settings persistently

**Priority:** P2 (Medium)  
**Effort:** 5 points  
**Status:** 🔄 In Progress (basic UI exists)

---

#### GOV-007: Connection Status Indicator

**As a** governance operator  
**I want** a persistent connection status indicator  
**So that** I always know if I'm online

**Acceptance Criteria:**

- [ ] Always visible indicator (sidebar or status bar)
- [ ] Shows 🟢 when connected
- [ ] Shows 🔴 when disconnected
- [ ] Shows 🟡 when degraded (high latency)
- [ ] Click to see details
- [ ] Shows last successful connection time

**Priority:** P1 (High)  
**Effort:** 3 points  
**Status:** ⏳ Pending

---

## Iteration 5: Offline Mode ⏳ PENDING

### User Stories

#### GOV-008: Offline Verdict Queue

**As a** governance operator  
**I want** verdicts to queue when offline  
**So that** I don't lose data when the orchestrator is down

**Acceptance Criteria:**

- [ ] Verdicts queue automatically when offline
- [ ] Queue indicator shows count
- [ ] Manual "Flush Queue" button
- [ ] Auto-flush when connection restored
- [ ] Queue persists across app restarts
- [ ] Failed verdicts can be retried

**Priority:** P1 (High)  
**Effort:** 6 points  
**Status:** ✅ Complete (VM has queue logic, needs UI enhancement)

---

#### GOV-009: Retry Failed Verdicts

**As a** governance operator  
**I want** to retry failed verdicts  
**So that** I can recover from transient errors

**Acceptance Criteria:**

- [ ] Failed verdicts list view
- [ ] "Retry" button per verdict
- [ ] "Retry All" button
- [ ] Shows error reason
- [ ] Remove from list after success
- [ ] Max retry count (configurable)

**Priority:** P2 (Medium)  
**Effort:** 4 points  
**Status:** ⏳ Pending

---

## Iteration 6: Advanced Visualizations ⏳ PENDING

### User Stories

#### GOV-010: Verdict Trend Chart

**As a** governance operator  
**I want** to see verdict trends over time  
**So that** I can spot patterns

**Acceptance Criteria:**

- [ ] Line chart with PASS/SOFT/HARD over time
- [ ] Time range selector (1h, 6h, 24h, 7d)
- [ ] Refresh with metrics
- [ ] Export chart as image
- [ ] Hover to see exact values

**Priority:** P2 (Medium)  
**Effort:** 8 points  
**Status:** ⏳ Pending

**Technical Notes:**

- Use Swift Charts framework
- Query Prometheus for historical data
- Cache data locally for performance

---

#### GOV-011: Remediation Success Rate

**As a** governance operator  
**I want** to see remediation success rate  
**So that** I can evaluate system performance

**Acceptance Criteria:**

- [ ] Success rate percentage (completed/requested)
- [ ] Visual gauge or progress ring
- [ ] Success/failure breakdown
- [ ] Average remediation time
- [ ] Last 24h vs all-time comparison

**Priority:** P2 (Medium)  
**Effort:** 5 points  
**Status:** ⏳ Pending

---

## Iteration 7: Menu Bar Integration ⏳ PENDING

### User Stories

#### GOV-012: Menu Bar Widget

**As a** governance operator  
**I want** a menu bar status indicator  
**So that** I can monitor the system without opening the app

**Acceptance Criteria:**

- [ ] Menu bar icon (🟢/🟡/🔴 or custom)
- [ ] Click to show quick stats
- [ ] Shows last verdict count
- [ ] "Open Dashboard" menu item
- [ ] "Send Demo Verdict" menu item
- [ ] "Quit" menu item
- [ ] Updates every 10 seconds

**Priority:** P2 (Medium)  
**Effort:** 6 points  
**Status:** ⏳ Pending

**Technical Notes:**

- Use `MenuBarExtra` (macOS 13+)
- Share ViewModel with main app
- Keep menu lightweight (no heavy rendering)

---

## Iteration 8: Notifications ⏳ PENDING

### User Stories

#### GOV-013: Verdict Notifications

**As a** governance operator  
**I want** notifications for important verdicts  
**So that** I'm alerted to critical events

**Acceptance Criteria:**

- [ ] Notification for HARD_FAIL verdicts
- [ ] Notification for remediation failures
- [ ] Notification for successful promotions
- [ ] User preferences for which to notify
- [ ] Click notification to open app
- [ ] Sound toggle

**Priority:** P2 (Medium)  
**Effort:** 5 points  
**Status:** ⏳ Pending

**Technical Notes:**

- Use `UNUserNotificationCenter`
- Request permission on first launch
- Group notifications by type
- Clear on app focus

---

## Iteration 9: Logging & Debugging ⏳ PENDING

### User Stories

#### GOV-014: View Application Logs

**As a** developer  
**I want** to view application logs in the UI  
**So that** I can debug issues without terminal access

**Acceptance Criteria:**

- [ ] Log viewer window
- [ ] Filter by category (governance.ui, governance.net, etc.)
- [ ] Filter by level (debug, info, error)
- [ ] Search logs
- [ ] Export logs to file
- [ ] Clear logs button

**Priority:** P3 (Low)  
**Effort:** 6 points  
**Status:** ⏳ Pending

---

#### GOV-015: Network Request Inspector

**As a** developer  
**I want** to see all network requests  
**So that** I can debug API issues

**Acceptance Criteria:**

- [ ] List of all requests (method, URL, status)
- [ ] Request/response body viewer
- [ ] Timing information
- [ ] Retry indicators
- [ ] Export as cURL command
- [ ] Clear history button

**Priority:** P3 (Low)  
**Effort:** 8 points  
**Status:** ⏳ Pending

---

## Iteration 10: Release Polish ⏳ PENDING

### User Stories

#### GOV-016: App Icon & Branding

**As a** user  
**I want** a professional app icon  
**So that** the app looks polished

**Acceptance Criteria:**

- [ ] Custom app icon (1024x1024)
- [ ] All sizes generated (.iconset)
- [ ] Dock icon looks sharp
- [ ] Menu bar icon (if applicable)
- [ ] Splash screen (optional)

**Priority:** P2 (Medium)  
**Effort:** 3 points  
**Status:** ⏳ Pending

---

#### GOV-017: About Window

**As a** user  
**I want** an about window  
**So that** I know the app version and credits

**Acceptance Criteria:**

- [ ] App name and version
- [ ] Build date
- [ ] Copyright information
- [ ] Credits (contributors)
- [ ] Link to documentation
- [ ] Link to GitHub repo

**Priority:** P3 (Low)  
**Effort:** 2 points  
**Status:** ⏳ Pending

---

#### GOV-018: Help Documentation

**As a** user  
**I want** in-app help  
**So that** I can learn how to use the app

**Acceptance Criteria:**

- [ ] Help menu item
- [ ] Keyboard shortcuts list
- [ ] Feature explanations
- [ ] Troubleshooting guide
- [ ] Link to online docs

**Priority:** P3 (Low)  
**Effort:** 4 points  
**Status:** ⏳ Pending

---

#### GOV-019: DMG Packaging

**As a** distributor  
**I want** a DMG package  
**So that** users can easily install the app

**Acceptance Criteria:**

- [ ] DMG created with `hdiutil`
- [ ] Background image (optional)
- [ ] Applications folder shortcut
- [ ] README included
- [ ] Code signed (if certificate available)
- [ ] Notarized (if certificate available)

**Priority:** P1 (High)  
**Effort:** 5 points  
**Status:** ⏳ Pending

---

## Backlog (Future)

### Nice-to-Have Features

#### GOV-020: Keyboard Shortcuts

- ⌘R: Refresh
- ⌘T: Send demo verdict
- ⌘,: Open settings
- ⌘H: Toggle health check
- ⌘Q: Quit

**Priority:** P3 (Low)  
**Effort:** 2 points

---

#### GOV-021: Export Metrics

- Export to CSV
- Export to JSON
- Export to PDF report
- Scheduled exports

**Priority:** P3 (Low)  
**Effort:** 5 points

---

#### GOV-022: Multi-Environment Support

- Switch between dev/staging/prod
- Saved environment profiles
- Color-coded environment indicator
- Prevent accidental production changes

**Priority:** P2 (Medium)  
**Effort:** 6 points

---

#### GOV-023: Accessibility Audit

- Full VoiceOver support
- Keyboard navigation
- High contrast mode
- Large text support
- Screen reader announcements

**Priority:** P1 (High)  
**Effort:** 8 points

---

#### GOV-024: Performance Profiling

- Track UI render times
- Track network latency
- Memory usage monitoring
- Battery impact assessment
- Performance report export

**Priority:** P3 (Low)  
**Effort:** 10 points

---

## Icebox (Ideas)

- Real-time collaboration (multiple operators)
- Verdict approval workflow (require 2+ approvals)
- Audit log viewer
- Role-based access control
- Mobile companion app (iOS)
- Slack/Discord integration
- Custom alert rules
- Dashboard customization (drag-drop widgets)
- Prometheus query builder
- Grafana dashboard embedding

---

## Sprint Planning

### Sprint 1 (Iterations 1-3)

**Goal:** Core functionality operational  
**Duration:** 1 week  
**Stories:** GOV-001, GOV-002, GOV-003, GOV-004, GOV-005

### Sprint 2 (Iterations 4-6)

**Goal:** Configuration and resilience  
**Duration:** 1 week  
**Stories:** GOV-006, GOV-007, GOV-008, GOV-009

### Sprint 3 (Iterations 7-9)

**Goal:** Advanced features  
**Duration:** 1 week  
**Stories:** GOV-010, GOV-011, GOV-012, GOV-013, GOV-014, GOV-015

### Sprint 4 (Iteration 10)

**Goal:** Release readiness  
**Duration:** 3 days  
**Stories:** GOV-016, GOV-017, GOV-018, GOV-019

---

## Definition of Done

For a story to be considered "Done":

1. ✅ Code implemented and merged
2. ✅ Unit tests written and passing
3. ✅ UI tests written and passing (if applicable)
4. ✅ Integration tested against live orchestrator
5. ✅ Offline behavior tested
6. ✅ Error scenarios tested
7. ✅ Accessibility checked (labels, contrast)
8. ✅ Documentation updated (CHANGELOG_UI.md)
9. ✅ Screenshot added (if visual change)
10. ✅ Code reviewed (if team > 1)
11. ✅ SwiftLint passing (if configured)
12. ✅ No compiler warnings

---

**Last Updated:** 2025-10-16  
**Next Review:** After Iteration 2
