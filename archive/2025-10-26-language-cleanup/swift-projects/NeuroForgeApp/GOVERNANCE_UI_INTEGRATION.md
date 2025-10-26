# Governance UI Integration - SwiftUI Dashboard

**Complete SwiftUI integration for Athena Governance**

---

## ✅ **What Was Added**

### New Files

1. **Sources/Athena/GovernanceAPIClient.swift** - API client for orchestrator (9110) and Prometheus (9090)
2. **Sources/Athena/GovernanceDashboardView.swift** - Main governance dashboard UI

### Updated Files

1. **Sources/AthenaModels.swift** - Added governance models (GovernanceMode, KPIs, VerdictPayload, etc.)
2. **Sources/AthenaState.swift** - Added governance state management & monitoring
3. **Sources/AthenaDashboardView.swift** - Integrated governance dashboard

---

## 🎯 **Features**

### 1. Real-Time KPI Monitoring

- **ECE** (Expected Calibration Error) - with color-coded thresholds
- **Entropy Drift** - system entropy tracking
- **Verdicts** - rendered verdicts (5min window)
- **Actions** - executed actions (5min window)
- **Hard Fails** - critical verdicts count

### 2. Mode Control

**Three Modes:**

- 🔵 **Shadow** (0% impact) - Observe only
- 🟡 **Canary** (1-5% impact) - Partial enforcement
- 🟢 **Enforce** (100% impact) - Full governance

**Switch with one tap** - calls orchestrator `/mode` endpoint

### 3. Quick Test Verdicts

- ✅ **Send PASS** - Test successful verdict
- ⚠️ **Send SOFT_FAIL** - Test warning verdict
- ❌ **Send HARD_FAIL** - Test critical verdict
- 🎛️ **Custom Verdict** - Full control (sheet)

### 4. Live Alerts

Auto-generated alerts based on KPIs:

- 🔴 ECE >0.08 (Critical) - Rollback recommended
- 🟠 ECE >0.06 (Warning) - Monitor closely
- 🔴 Entropy ≥0.25 (Critical) - Rollback required
- 🟠 Hard Fails detected
- 🔴 Orchestrator DOWN

### 5. Auto-Refresh

- Polls every 5 seconds
- Updates KPIs from Prometheus
- Checks orchestrator health
- Updates alerts automatically

---

## 🔌 **How It Works**

### API Integration

```
SwiftUI App (macOS/iOS)
    ↓
GovernanceAPIClient
    ├─→ http://localhost:9110/health (orchestrator health)
    ├─→ http://localhost:9110/verdict (send verdicts)
    ├─→ http://localhost:9110/mode (switch modes)
    └─→ http://localhost:9090/api/v1/query (fetch KPIs)
```

### State Flow

```
Timer (every 5s)
    ↓
AthenaState.refreshGovernance()
    ├─→ checkOrchestratorHealth()
    ├─→ refreshKPIs()
    └─→ updateAlerts()
        ↓
    SwiftUI View Updates
```

---

## 🚀 **Usage**

### In Xcode

1. Open `NeuroForgeApp.xcodeproj`
2. Build and run (⌘R)
3. Navigate to "Athena Dashboard"
4. Governance controls appear at the top

### Requirements

- macOS 14+ or iOS 17+
- Governance services running:
  - Port 9110 (orchestrator)
  - Port 9109 (metrics exporter)
  - Port 9090 (Prometheus)

### Start Services

```bash
# Before running the app
cd /path/to/athena
make governance-up
docker start athena-prometheus
```

---

## 📊 **UI Components**

### Mode Switcher

```
┌─────────────────────────────────────┐
│ Governance Mode                     │
│ ┌─────────┬─────────┬────────────┐ │
│ │ Shadow  │ Canary  │  Enforce   │ │
│ └─────────┴─────────┴────────────┘ │
│ 🔵 0% impact - Observe only         │
└─────────────────────────────────────┘
```

### KPI Grid (6 cards)

```
┌──────────┐ ┌──────────┐ ┌──────────┐
│ ECE      │ │ Entropy  │ │ Verdicts │
│ 0.045 🟢 │ │ 0.12 🟢  │ │ 42       │
└──────────┘ └──────────┘ └──────────┘
┌──────────┐ ┌──────────┐ ┌──────────┐
│ Actions  │ │HardFails │ │ Status   │
│ 35       │ │ 2 🟠     │ │ applied  │
└──────────┘ └──────────┘ └──────────┘
```

### Alerts (dynamic)

```
┌────────────────────────────────────────┐
│ 🟠 ECE Warning (>0.06) - Monitor       │
│    2 minutes ago                        │
├────────────────────────────────────────┤
│ 🟠 2 HARD_FAIL verdict(s) in last 5min │
│    1 minute ago                         │
└────────────────────────────────────────┘
```

### Quick Actions

```
┌───────────────────────────────────────────┐
│ [✅ Send PASS] [⚠️ Send SOFT_FAIL]        │
│ [❌ Send HARD_FAIL] [🎛️ Custom Verdict]  │
└───────────────────────────────────────────┘
```

---

## 🔧 **Configuration**

### Endpoint URLs

Hardcoded defaults (can be made configurable):

```swift
orchestratorURL: http://localhost:9110
prometheusURL: http://localhost:9090
```

### Refresh Interval

```swift
Timer interval: 5 seconds  // KPI refresh rate
```

### To Change

Edit `GovernanceAPIClient.swift` init method.

---

## 📋 **Models Added**

### GovernanceMode

```swift
enum GovernanceMode: String {
    case shadow, canary, enforce
}
```

### GovernanceKPIs

```swift
struct GovernanceKPIs {
    var ece: Double
    var entropy: Double
    var verdicts_5m: Int
    var actions_5m: Int
    var hard_fails_5m: Int
}
```

### VerdictPayload

```swift
struct VerdictPayload {
    let task_id: String
    let verdict: String
    let ece_post: Double?
    let entropy: Double?
    let actions: [String]?
    let ts: String
}
```

### GovernanceAlert

```swift
struct GovernanceAlert {
    let message: String
    let severity: AlertSeverity
    let timestamp: Date
}
```

---

## 🎨 **UI Design**

### Color Coding

- 🟢 **Green** - Normal (ECE <0.06, Entropy <0.25)
- 🟠 **Orange** - Warning (ECE 0.06-0.08, Hard Fails present)
- 🔴 **Red** - Critical (ECE >0.08, Entropy ≥0.25, Orchestrator down)

### Icons

- `eye.fill` - Shadow mode
- `bird.fill` - Canary mode
- `shield.fill` - Enforce mode
- `chart.line.uptrend.xyaxis` - ECE
- `waveform.path.ecg` - Entropy
- `checkmark.seal.fill` - Verdicts
- `bolt.fill` - Actions
- `exclamationmark.triangle.fill` - Hard Fails

---

## 🧪 **Testing**

### Manual Test

1. Start governance services: `make governance-up`
2. Run NeuroForgeApp in Xcode
3. Go to Athena Dashboard
4. Click "Send PASS" button
5. Watch KPI cards update in ~5 seconds

### Expected Behavior

- ✅ Green circle appears (orchestrator healthy)
- ✅ KPIs show real values (not "—")
- ✅ Mode switcher works
- ✅ Test verdict buttons work
- ✅ Metrics increment after sending verdict

---

## 🔌 **Backend Integration**

### Required Endpoints

**Orchestrator (9110):**

- `GET /health` → `{"status":"healthy"}`
- `POST /verdict` → `{"status":"applied"}`
- `POST /mode` → `{"status":"ok"}` (optional)
- `GET /metrics` → Prometheus format

**Prometheus (9090):**

- `/api/v1/query?query=governance_ece_post`
- `/api/v1/query?query=governance_entropy_drift`
- `/api/v1/query?query=sum(increase(governance_verdicts_total[5m]))`
- `/api/v1/query?query=sum(increase(governance_actions_total[5m]))`
- `/api/v1/query?query=sum(increase(governance_verdicts_total{verdict_type="hard_fail"}[5m]))`

**All already working in your backend!** ✅

---

## 🎯 **Next Steps**

### Phase 1: Basic Integration ✅

- ✅ Models added
- ✅ API client created
- ✅ Dashboard view built
- ✅ Integrated into existing app

### Phase 2: Enhanced Features (Optional)

- [ ] WebSocket live events (`/events` endpoint)
- [ ] Receipt history view (recent traffic)
- [ ] Grafana panel embedding (WKWebView)
- [ ] Settings view (configure endpoints)
- [ ] Rollback wizard (one-tap emergency rollback)

### Phase 3: Polish (Optional)

- [ ] Chart visualizations (SwiftUI Charts)
- [ ] Historical trends (ECE/Entropy over time)
- [ ] Export reports (PDF/CSV)
- [ ] Dark mode optimization
- [ ] iOS companion app

---

## 📚 **Code Structure**

```
NeuroForgeApp/Sources/
├── AthenaModels.swift           # UPDATED: Added governance models
├── AthenaState.swift            # UPDATED: Added governance state
├── AthenaDashboardView.swift   # UPDATED: Integrated governance
└── Athena/
    ├── GovernanceAPIClient.swift      # NEW: API layer
    └── GovernanceDashboardView.swift  # NEW: UI components
```

---

## 🎊 **Result**

You now have a **native macOS/iOS app** to:

- ✅ Monitor governance KPIs in real-time
- ✅ Switch modes (shadow/canary/enforce)
- ✅ Send test verdicts for drills
- ✅ View active alerts
- ✅ Check orchestrator health

**All with zero backend changes** - it just calls your existing endpoints! 🚀

---

**Build and run:**

```bash
cd NeuroForgeApp
xcodebuild -scheme NeuroForgeApp -configuration Debug
```

Or open in Xcode and press ⌘R
