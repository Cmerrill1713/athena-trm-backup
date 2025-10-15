# Governance Auto-Promote / Auto-Rollback Integration

## Overview

Your governance CI/CD system now includes **automatic canary analysis** that watches KPIs in Prometheus and makes promote/rollback decisions without human intervention.

## 🚀 What Was Added

### 1. **Canary Decision Engine** (`scripts/gov_canary_decider.py`)
- Queries Prometheus for canary KPIs every few minutes
- Makes **PROMOTE / HOLD / ROLLBACK** decisions based on governance thresholds
- **Exit codes**:
  - `0` → PROMOTE (all criteria met)
  - `10` → HOLD (insufficient data or waiting for metrics)
  - `20` → ROLLBACK (hard breakers triggered)

### 2. **Automated Workflow** (`.github/workflows/governance-canary-watch.yml`)
- Manual trigger with configurable window size
- Runs decider and automatically executes promote/rollback scripts
- Branches logic based on decision outcomes

### 3. **Makefile Integration**
```bash
make governance-canary-watch  # Test canary decision locally
```

## 📊 Required Prometheus Metrics

The decider looks for these metrics (expose them from your governance exporter):

### Core KPIs
- `governance_solve_rate_delta` - Change in task solve rate
- `governance_violation_rate_delta` - Change in policy violation rate
- `governance_latency_p95_delta` - Change in 95th percentile latency
- `governance_ece_post` - Post-deployment evolutionary computation efficiency
- `governance_edge_case_score` - Edge case handling score (0.0-1.0)
- `governance_consistency_index` - Response consistency score (0.0-1.0)

### Sample Counter
- `governance_canary_samples_total` - Total tasks processed in canary window

## ⚙️ Configuration

### Environment Variables
```bash
# Prometheus
PROM_URL=http://localhost:9090

# Window settings
WINDOW_MINUTES=15      # Minutes to observe after deploy
MIN_SAMPLES=200        # Minimum tasks needed to decide

# Thresholds (match governance_policy.yaml)
REQ_SOLVE_DELTA_GE=0.02   # Solve rate must improve by 2%
REQ_VIOL_DELTA_LE=0.005   # Violation rate increase ≤ 0.5%
REQ_P95_DELTA_LE=0.25     # Latency increase ≤ 25%
REQ_ECE_POST_LE=0.06      # Post-deploy ECE ≤ 6%
REQ_EDGE_SCORE_GE=0.80    # Edge case score ≥ 80%
REQ_CONSIST_IDX_GE=0.90   # Consistency index ≥ 90%
```

### Decision Logic

#### 🚫 Hard Rollback Triggers (immediate action)
- ECE post-deploy > 6%
- Violation rate delta > 0.5%
- P95 latency delta > 25%

#### ✅ Promotion Requirements
- **Must have**: Solve rate delta ≥ 2%
- **Must have**: Edge case score ≥ 80%
- **Must have**: Consistency index ≥ 90%
- **Must have**: ≥200 samples in window

#### ⏳ Hold Conditions
- Insufficient samples (<200)
- Missing required metrics
- Waiting for positive promotion criteria

## 🚦 Usage

### Manual Testing
```bash
# Test decision locally
make governance-canary-watch

# With custom thresholds
PROM_URL=http://prometheus:9090 WINDOW_MINUTES=10 make governance-canary-watch
```

### GitHub Actions
1. Go to repository Actions tab
2. Find "governance-canary-watch" workflow
3. Click "Run workflow"
4. Configure window size and minimum samples
5. Watch it automatically promote or rollback

### CI/CD Integration
Add after your deployment job:

```yaml
- name: Watch canary and decide
  uses: ./.github/workflows/governance-canary-watch.yml
  with:
    window_minutes: "15"
    min_samples: "200"
```

## 📈 Adding Metrics to Your Exporter

If you need to expose canary sample counts, add this to your governance metrics exporter:

```python
# In governance/observability/governance_metrics_exporter.py
from prometheus_client import Gauge, Counter

# Existing metrics...
canary_samples = Gauge('governance_canary_samples_total',
                      'Total tasks processed in current canary window')

# When processing tasks in canary mode:
def process_task(task_data):
    # ... existing logic ...

    # Track canary samples
    if is_canary_deployment():
        canary_samples.inc()

    # ... rest of processing ...
```

## 🔄 Workflow Examples

### Decision Flow
```
Deploy → Wait WINDOW_MINUTES → Query KPIs → Decide:
├── ✅ PROMOTE (exit 0) → Run gov_promote.sh
├── 🚫 ROLLBACK (exit 20) → Run gov_rollback.sh
└── ⏳ HOLD (exit 10) → Log and exit (rerun later)
```

### CI/CD Pipeline
```
1. Push to main
2. Pre-deploy gate (governance health)
3. Deploy to production
4. Auto-watch canary for 15 minutes
5. Auto-promote or auto-rollback
6. Alert team on final outcome
```

## 🛡️ Safety Features

- **Insufficient data protection**: Won't decide with <200 samples
- **Hard rollback triggers**: Immediate action on critical KPIs
- **Threshold alignment**: Uses same values as governance_policy.yaml
- **Graceful degradation**: HOLD when metrics unavailable
- **No false positives**: Requires positive promotion signals

## 🔍 Monitoring

Watch the decider output:
```json
{
  "solve_rate_delta": 0.035,
  "violation_rate_delta": 0.002,
  "latency_p95_delta": 0.15,
  "ece_post": 0.045,
  "edge_case_score": 0.85,
  "consistency_index": 0.92,
  "samples": 450
}
[decider] PROMOTE
```

## 🚨 Troubleshooting

### Common Issues

1. **Always HOLD (insufficient samples)**
   - **Cause**: `governance_canary_samples_total` not exposed or < 200
   - **Fix**: Add sample counter to your metrics exporter

2. **Missing metrics**
   - **Cause**: KPIs not exposed from governance exporter
   - **Fix**: Add the required Prometheus metrics

3. **Wrong thresholds**
   - **Cause**: Env vars don't match your governance_policy.yaml
   - **Fix**: Verify REQ_* environment variables

### Testing Thresholds
```bash
# Force a rollback scenario
curl -X POST http://localhost:9110/api/v1/simulate-kpis \
  -d '{"ece_post": 0.08}'  # Above 0.06 threshold

# Test with custom thresholds
REQ_ECE_POST_LE=0.10 make governance-canary-watch
```

---

Your governance system now **automatically manages canary deployments** without human intervention. The decider watches real production KPIs and makes confident promote/rollback decisions based on your governance policies! 🧠⚖️🤖
