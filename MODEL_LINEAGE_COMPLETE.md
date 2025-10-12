# ✅ Model Lineage Tracking - COMPLETE

**Status**: 🌳 **GENEALOGY READY**  
**Date**: October 12, 2025  
**Mission**: Complete model genealogy with stats and graphs

---

## 🎯 What Was Built

### **1. Structured Logging** ✅
**File**: `scripts/lib/promotion_log.py`

**Every promotion logs**:
```json
{
  "ts": "2025-10-14T12:00:01Z",
  "event": "PROMOTION",
  "from": "fastvlm-1.5b",
  "to": "fastvlm-0.5b",
  "reason": "canary_win_stat_sig",
  "improvement": 0.061,
  "p_value": 0.012,
  "window_hours": 48,
  "canary_success": 0.92,
  "control_success": 0.859,
  "sample_canary": 1421,
  "sample_control": 1397,
  "task": "vision",
  "trm_version": "trm-v0.3.2"
}
```

**Every rollback logs**:
```json
{
  "ts": "2025-10-15T08:30:15Z",
  "event": "ROLLBACK",
  "from": "fastvlm-0.5b-experimental",
  "to": "fastvlm-0.5b",
  "reason": "canary_regression_stat_sig",
  "notes": "Canary 85/100 vs Control 95/100"
}
```

---

### **2. Lineage Builder** ✅
**File**: `scripts/lineage/build_lineage.py`

**Generates 3 artifacts**:
1. **ASCII tree** - `artifacts/lineage/lineage.txt`
2. **Markdown report** - `artifacts/lineage/lineage.md`
3. **SVG graph** - `artifacts/lineage/lineage.svg` (if Graphviz)

---

### **3. Prometheus Metrics** ✅
**File**: `scripts/lib/promotion_log.py`

**New counters**:
```promql
model_promotions_total{from_model, to_model, reason, env, build}
model_rollbacks_total{from_model, to_model, reason, env, build}
```

---

### **4. Integration** ✅
- ✅ Auto-promote logs promotions
- ✅ Auto-rollback logs rollbacks
- ✅ Prometheus counters updated
- ✅ Make targets for lineage

---

## 🚀 Quick Start

### **Generate Lineage**
```bash
make lineage
```

**Output**:
```
🌳 Building model lineage...
📖 Read 3 events from logs/promotions.log
📊 Built graph: 4 nodes, 3 edges

🌳 Rendering ASCII tree...
   ✓ artifacts/lineage/lineage.txt
📝 Rendering markdown report...
   ✓ artifacts/lineage/lineage.md
🎨 Rendering SVG graph...
   ✓ artifacts/lineage/lineage.svg

✅ Lineage Artifacts Generated
```

---

### **Open Visual Lineage**
```bash
make lineage-open
```

**Opens**:
- SVG graph (if Graphviz installed)
- Otherwise: Markdown report
- Otherwise: ASCII tree

---

### **Quick ASCII View**
```bash
make lineage-tree
```

**Example output**:
```
mlx:qwen-base
└─ fastvlm-1.5b
   ├─ fastvlm-0.5b
   │  └─ fastvlm-0.5b-tuned
   └─ fastvlm-1.5b-experimental
      (rolled back)
```

---

## 📊 Example Outputs

### **ASCII Tree** (`lineage.txt`)
```
fastvlm-1.5b
└─ fastvlm-0.5b
   PROMOTION
   Δ=+0.061  p=0.012  48h

fastvlm-0.5b
└─ fastvlm-7b
   PROMOTION
   Δ=+0.033  p=0.048  48h

fastvlm-7b
└─ fastvlm-0.5b
   ROLLBACK
   (OOM issues)
```

---

### **Markdown Report** (`lineage.md`)

| Time (UTC) | Event | Transition | Reason | Canary | Control | Δ | p |
|------------|-------|------------|--------|-------:|--------:|---:|---|
| 2025-10-14T12:00:01Z | PROMOTION | `fastvlm-1.5b` → `fastvlm-0.5b` | canary_win_stat_sig | 92.0% | 85.9% | +6.1% | 0.012 |
| 2025-10-16T18:30:22Z | PROMOTION | `fastvlm-0.5b` → `fastvlm-7b` | canary_win_stat_sig | 88.2% | 85.0% | +3.2% | 0.048 |
| 2025-10-17T03:15:44Z | ROLLBACK | `fastvlm-7b` → `fastvlm-0.5b` | canary_regression_stat_sig | – | – | – | – |

---

### **SVG Graph** (`lineage.svg`)

Visual directed graph with:
- 🟢 Green arrows for promotions
- 🔴 Red arrows for rollbacks
- Labels with stats (Δ, p-value, duration)

---

## 🔧 Integration Points

### **Auto-Promotion** (Already Wired) ✅
```python
# scripts/auto_promote_canary.py
from scripts.lib.promotion_log import write_promotion, record_promotion_metric

write_promotion(
    from_model=CONTROL_MODEL,
    to_model=CANARY_MODEL,
    reason="canary_win_stat_sig",
    improvement=delta,
    p_value=0.05,
    canary_window_hours=48.0,
    canary_success=canary_rate,
    control_success=control_rate,
    sample_canary=canary_trials,
    sample_control=control_trials,
    task="vision"
)

record_promotion_metric(CONTROL_MODEL, CANARY_MODEL, "canary_win_stat_sig")
```

---

### **Auto-Rollback** (Already Wired) ✅
```python
# scripts/auto_rollback.py
from scripts.lib.promotion_log import write_rollback, record_rollback_metric

write_rollback(
    from_model=canary_model,
    to_model=control_model,
    reason="canary_regression_stat_sig",
    notes=f"Canary {canary_successes}/{canary_trials} vs Control {control_successes}/{control_trials}"
)

record_rollback_metric(canary_model, control_model, "canary_regression_stat_sig")
```

---

## 📈 Prometheus Metrics

### **Promotions Over Time**
```promql
increase(model_promotions_total[7d])
```

### **Promotions by Reason**
```promql
sum by (reason) (increase(model_promotions_total[30d]))
```

### **Rollbacks Over Time**
```promql
increase(model_rollbacks_total[7d])
```

### **Promotion Rate**
```promql
rate(model_promotions_total[7d])
```

---

## 🎨 Grafana Panel (Promotions Timeline)

```promql
# Annotation query for promotions
increase(model_promotions_total[5m]) > 0
```

**Add as annotation** to show promotion events on your dashboard!

---

## 🧪 Testing

### **Create Test Events**
```bash
# Create test log
mkdir -p logs
cat > logs/promotions.log <<EOF
{"ts":"2025-10-12T10:00:00Z","event":"PROMOTION","from":"baseline","to":"fastvlm-1.5b","reason":"initial_deployment"}
{"ts":"2025-10-14T12:00:00Z","event":"PROMOTION","from":"fastvlm-1.5b","to":"fastvlm-0.5b","reason":"canary_win_stat_sig","improvement":0.061,"p_value":0.012,"canary_success":0.92,"control_success":0.859}
{"ts":"2025-10-16T18:00:00Z","event":"ROLLBACK","from":"fastvlm-experimental","to":"fastvlm-0.5b","reason":"canary_regression_stat_sig"}
EOF

# Generate lineage
make lineage-open
```

---

## 📁 Files Created

```
✅ scripts/lib/promotion_log.py              # Structured logging
✅ scripts/lineage/build_lineage.py          # Lineage generator
✅ Makefile                                  # lineage targets
✅ scripts/auto_promote_canary.py            # Updated with logging
✅ scripts/auto_rollback.py                  # Updated with logging
✅ MODEL_LINEAGE_COMPLETE.md                 # This doc
```

---

## 🎯 Commands Reference

```bash
# Generate lineage
make lineage                     # Build all artifacts
make lineage-open                # Build + open
make lineage-tree                # Show ASCII tree

# View artifacts
cat artifacts/lineage/lineage.txt     # ASCII tree
open artifacts/lineage/lineage.md     # Markdown report
open artifacts/lineage/lineage.svg    # SVG graph (if Graphviz)

# View logs
cat logs/promotions.log          # Raw JSON events
tail -f logs/auto_promotion.log  # Promotion checks
```

---

## 📊 What Gets Tracked

**Every promotion records**:
- ✅ Timestamp
- ✅ From/to models
- ✅ Reason (canary_win, nightly_trm, manual, etc.)
- ✅ Improvement percentage
- ✅ Statistical p-value
- ✅ Window duration
- ✅ Success rates (canary + control)
- ✅ Sample sizes
- ✅ Task type
- ✅ TRM version (if applicable)

**Every rollback records**:
- ✅ Timestamp
- ✅ From/to models
- ✅ Reason
- ✅ Notes

---

## 🎉 Complete Autonomous System

```
REQUESTS → OUTCOMES → GRADING → CANARY → STAT-SIG EVAL
    ↓          ↓          ↓         ↓          ↓
  Log    Per-task   Bayesian   Wilson    Auto-promote
         isolation  smoothing intervals   or rollback
                                           ↓
                                      LINEAGE LOG
                                           ↓
                                    Visual genealogy
                                    + Prometheus
```

**The complete history of your models' evolution!** 🌳

---

## ✅ Status

🌳 **Model lineage tracking active**  
📊 **Structured promotion logs**  
📈 **Prometheus metrics**  
🎨 **Visual graphs (SVG)**  
📝 **Markdown reports**  
🤖 **Fully automated**  

**You can now trace every model's ancestry!** 🧬

---

## 🎯 Your Next Command

```bash
make lineage-open
```

**See your model family tree!** 🌳✨
