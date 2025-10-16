# AthenaReporter - Change Log

All notable changes to the AthenaReporter Swift application.

---

## [Unreleased]

### Added - Iteration 1 (Oct 16, 2025)

- **RemediationMonitor.swift** - Auto-remediation monitoring UI
  - Three-tab interface (Metrics/Health/Events)
  - Real-time polling from http://localhost:9112/metrics
  - Service health indicators for remediator/orchestrator/prometheus
  - Success rate gauge with color coding
  - Auto-refresh every 5 seconds
  - Connection status indicator
- Menu integration: "Athena → Open Remediation Monitor" (⌘⇧R)
- Window management for remediation monitor

### Modified - Iteration 1

- **AthenaReporter.swift** - Added remediation monitor window
- **AthenaReporter.swift** - Added keyboard shortcut ⌘⇧R

### Technical Details

- Lines added: ~500
- API integration: http://localhost:9112 (remediator service)
- Prometheus format parsing for metrics
- URLSession with async/await for health checks
- 5-second polling timer with @MainActor safety

---

## [1.0.0] - 2025-10-11

### Initial Release

- Report viewer with markdown rendering
- Voice synthesis (System TTS + Kokoro integration)
- Voice hard-locking via VoiceSentinel
- Voice diagnostics via VoiceDoctor
- URL scheme handling (athena://report)
- Multi-window management
- Data persistence via ReportStore
- Deduplication logic

### Components

- **AthenaReporter.swift** (12,535 lines) - Main app
- **VoiceManager.swift** (9,628 lines) - TTS backends
- **VisionReporter.swift** (7,582 lines) - Vision processing
- **VoiceSentinel.swift** (4,176 lines) - Voice monitoring
- **VoiceDoctor.swift** (1,142 lines) - Diagnostics
- **ReportStore.swift** (1,538 lines) - Persistence
- **Dedupe.swift** (1,261 lines) - Deduplication

---

## Next Iterations (Planned)

### Iteration 2 - Orchestrator Integration

- [ ] Add OrchestratorClient.swift
- [ ] Connect to http://localhost:9110
- [ ] Fetch /health, /metrics, /state
- [ ] Display orchestrator status in dashboard
- [ ] Unit tests with mocked responses

### Iteration 3 - Enhanced Dashboard

- [ ] ECE gauge from Prometheus
- [ ] Verdict counters by type
- [ ] Swift Charts integration
- [ ] Historical metrics (last hour)
- [ ] Snapshot tests for dashboard

### Iteration 4 - Verdict Submission

- [ ] Verdict form UI
- [ ] POST to /verdict endpoint
- [ ] Idempotence feedback
- [ ] Form validation
- [ ] Success/error states

### Iteration 5 - Canary Integration

- [ ] CanaryClient.swift
- [ ] Connect to http://localhost:9111
- [ ] Display canary window status
- [ ] Show last decision
- [ ] Sample count tracking

### Iteration 6 - Mode Control

- [ ] Mode switcher (Shadow/Canary/Enforce)
- [ ] POST /mode with confirmation
- [ ] Token authentication support
- [ ] Dry-run preview
- [ ] Safety confirmations

### Iteration 7 - Resilience

- [ ] Retry logic with backoff
- [ ] Offline mode with cached data
- [ ] Graceful degradation
- [ ] Empty states and spinners
- [ ] Background/foreground polling

### Iteration 8 - Events & Alerts

- [ ] Client-side event log
- [ ] Critical alert banner (ECE>0.08)
- [ ] Entropy drift warnings
- [ ] Violation spike indicators
- [ ] Alert acknowledgment

### Iteration 9 - Polish

- [ ] Typography system
- [ ] Icon system
- [ ] Haptic feedback
- [ ] Accessibility labels
- [ ] Dynamic type support
- [ ] Dark mode refinement
- [ ] Color palette

### Iteration 10 - Release

- [ ] Diagnostics screen
- [ ] Integration tests
- [ ] Smoke tests
- [ ] RELEASE_NOTES.md
- [ ] Final build verification
- [ ] App notarization prep

---

## Version History

- **1.0.0** (Oct 11, 2025) - Initial release with voice and reporting
- **1.1.0** (Oct 16, 2025) - Added auto-remediation monitoring (Iteration 1)
- **1.2.0** (Planned) - Full governance integration (Iterations 2-10)

---

## Notes

- Each iteration must build and pass tests
- Diffs kept surgical (≤500 LOC per iteration)
- Features developed incrementally
- Tests written before UI polish
- .cursorrules enforced for all changes
