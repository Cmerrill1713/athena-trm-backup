# 🗣️ Athena Reporter - Voice + Visual Reports

**Status**: ✅ Operational  
**Created**: October 12, 2025

---

## 🎯 What Is This?

**Athena Reporter** gives your assistant a voice and a second screen. When you ask Athena for a report, she:

1. **Queries real metrics** from Prometheus
2. **Generates a visual report** with charts and tables
3. **Opens a floating window** with the full report
4. **Speaks a synopsis** using macOS text-to-speech

---

## 🚀 Quick Start

### One-Time Setup

Build the reporter app:
```bash
make reporter-build
```

This creates `build/Reporter/AthenaReporter`.

### Daily Use

Ask Athena for a report:
```bash
# System health report (recommended)
make report-health

# Evolution status
make report-evolution

# Metrics health
make report-metrics
```

**What happens:**
1. Python script queries Prometheus
2. Generates markdown report
3. Opens Athena Reporter window
4. Athena speaks: "All systems nominal. Seven day success rate 98.7 percent..."

---

## 🎤 Voice Control

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `⌘.` | Stop speaking immediately |
| `⌘S` | Speak the synopsis again |
| `⌘W` | Close window |

### Tuning Voice

Edit `AthenaReporter.swift` line ~76:
```swift
utt.rate = AVSpeechUtteranceDefaultSpeechRate * 0.92  // Speed
utt.pitchMultiplier = 1.05                            // Pitch
utt.volume = 0.85                                     // Volume
```

Then rebuild: `make reporter-build`

---

## 📊 Report Types

### System Health Report

**Command**: `make report-health`

**Queries:**
- 7-day success rate
- p95 & p50 latency
- Active alerts
- Routing decisions (24h & 1h)
- Model promotions (7d)
- Model distribution

**Spoken Summary** (example):
> "All systems nominal. Seven day success rate 98.7 percent. P95 latency 483 milliseconds. P50 latency 156 milliseconds. 1260 routing decisions in the last twenty four hours. Zero active alerts."

**Visual Report** includes:
- Status emoji (✅/⚠️/🔥)
- KPI table with targets
- Model distribution chart
- Concerns list (if any)
- Quick links to Grafana/Prometheus
- Next actions timeline

### Evolution Report

**Command**: `make report-evolution`

**Status**: Coming soon

**Will include:**
- Training run history
- Accuracy trends
- Pending promotions
- Model registry

### Metrics Report

**Command**: `make report-metrics`

**Status**: Coming soon

**Will include:**
- Scrape success rates
- Metrics cardinality
- Query performance
- Target health

---

## 🔧 Technical Details

### How It Works

1. **URL Scheme**: `athena://report?title=...&summary=...&md=...`
2. **Python Script**: Queries Prometheus API, generates markdown
3. **macOS URL Handler**: Opens AthenaReporter app
4. **SwiftUI**: Renders markdown + plays audio

### Architecture

```
make report-health
    ↓
scripts/athena_report.py
    ↓
Query Prometheus API
    ↓
Generate markdown report
    ↓
open athena://report?...
    ↓
AthenaReporter.app
    ├── Display markdown
    └── Speak synopsis (AVSpeechSynthesizer)
```

### Files Created

```
AthenaReporter/
├── AthenaReporter.swift          # Main app (SwiftUI)
└── Info.plist                    # URL scheme registration

scripts/
└── athena_report.py              # Report generator

build/Reporter/
└── AthenaReporter                # Compiled binary

Makefile
├── reporter-build                # Build app
├── reporter-run                  # Launch app
├── report-health                 # Health report
├── report-evolution              # Evolution report
└── report-metrics                # Metrics report
```

---

## 🎨 Customization

### Add New Report Types

Edit `scripts/athena_report.py`:

```python
def synthesize_custom_report():
    """Your custom report"""
    # Query your metrics
    summary = "Short spoken summary"
    md = "# Full Markdown Report\n..."
    return "Report Title", summary, md

# Add to main()
elif mode == "custom":
    title, summary, md = synthesize_custom_report()
```

Add Make target:
```makefile
report-custom:
	@python3 $(SCRIPTS_DIR)/athena_report.py custom
```

### Customize Report Format

Edit markdown template in `synthesize_system_report()`:

```python
md = f"""# {status_emoji} Custom Format

**Your KPIs here**

| Metric | Value |
|--------|-------|
| Custom | {value} |

---

Your analysis here...
"""
```

### Add Charts/Images

Pre-render charts and reference them:

```python
# Generate chart
import matplotlib.pyplot as plt
plt.savefig('/tmp/chart.png')

# Reference in markdown
md += "![Chart](/tmp/chart.png)\n"
```

---

## 🗣️ Integration with Chat Assistant

### Option 1: Direct Integration

In your chat assistant code:

```python
import subprocess

def get_system_report():
    """Generate and display Athena report"""
    result = subprocess.run(
        ["python3", "scripts/athena_report.py", "health"],
        capture_output=True
    )
    return "Report generated" if result.returncode == 0 else "Failed"
```

### Option 2: Voice Command

Train your assistant to recognize:
- "Athena, how are we doing?" → `make report-health`
- "Show me the dashboard" → `make report-health`
- "System status" → `make report-health`
- "Evolution status" → `make report-evolution`

### Option 3: Scheduled Reports

Morning briefing:
```bash
# In crontab
0 9 * * 1-5 cd ~/Documents/GitHub && make report-health
```

---

## 🎯 Use Cases

### 1. Morning Check-In

**You**: "Athena, morning briefing"  
**Command**: `make report-health`  
**Athena**: Speaks KPIs + shows full report

### 2. Weekly Review

**You**: "Athena, weekly summary"  
**Script**: Custom report comparing week-over-week  
**Athena**: Speaks trends + shows comparison table

### 3. Incident Response

**Alert fires** → Auto-generate report:
```bash
# In alert webhook handler
make report-health
```

### 4. Stakeholder Demo

**During presentation**:
```bash
make report-health
```
**Effect**: Professional visual + verbal presentation

---

## 📈 Future Enhancements

### When You're Ready

**Live Mode**:
- Auto-refresh every 30s
- Real-time metric updates
- Streaming charts

**Voice Interactions**:
- Ask follow-up questions
- "Show me model X performance"
- Voice-controlled drill-downs

**Multi-Window**:
- One window per report type
- Side-by-side comparisons
- Persistent windows

**Export Options**:
- Copy as Markdown
- Export to PDF
- Email report
- Slack integration

**Chart Integration**:
- Embedded Prometheus graphs
- Historical trend lines
- Comparison charts

**Custom Voices**:
- Different voices per severity
- Calm voice for normal
- Urgent voice for alerts

---

## 🐛 Troubleshooting

### Reporter Window Doesn't Open

```bash
# Check if built
ls -la build/Reporter/AthenaReporter

# Rebuild
make reporter-build

# Launch manually
make reporter-run
```

### No Voice Output

**Check system settings:**
1. System Settings → Sound → Output volume
2. System Settings → Accessibility → Spoken Content → Speaking Rate

**Test TTS:**
```bash
say "Testing Athena voice"
```

### Metrics Not Loading

**Check Prometheus:**
```bash
curl http://localhost:9090/-/healthy
```

**Check query:**
```bash
curl -s 'http://localhost:9090/api/v1/query?query=up' | jq
```

**Run with debug:**
```bash
python3 scripts/athena_report.py health 2>&1
```

### Window Stays Empty

**Check URL scheme:**
```bash
# Test URL directly
open 'athena://report?title=Test&summary=Testing&md=# Test'
```

**Check logs:**
```bash
# Console.app → search for "AthenaReporter"
```

---

## 🎓 Examples

### Example 1: All Systems Normal

**Spoken**:
> "All systems nominal. Seven day success rate 98.7 percent. P95 latency 483 milliseconds. P50 latency 156 milliseconds. 1260 routing decisions in the last twenty four hours. Two model promotions this week. Zero active alerts."

**Visual**:
```markdown
# ✅ System Health Report

**Status:** ✅ Nominal

## KPIs
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Success Rate | 98.70% | ≥95% | ✅ |
| P95 Latency | 483 ms | <1500ms | ✅ |
...
```

### Example 2: Alert Firing

**Spoken**:
> "System status alerts firing. Two active alerts. Seven day success rate 92.3 percent. P95 latency 1623 milliseconds."

**Visual**:
```markdown
# 🔥 System Health Report

**Status:** 🔥 Alerts Firing

## ⚠️  Concerns
- Success rate below 95% (92.3%)
- p95 latency above threshold (1623ms)
- 2 active alerts
```

---

## 📚 Related Documentation

- [DAILY_OPERATIONS_GUIDE.md](./DAILY_OPERATIONS_GUIDE.md) - Daily monitoring workflow
- [MONITORING_SETUP.md](./MONITORING_SETUP.md) - Complete monitoring setup
- [OBSERVABILITY_COMPLETE.md](./OBSERVABILITY_COMPLETE.md) - Full system summary

---

## 🎉 You Now Have

✅ **Voice Reports**: Athena speaks system status  
✅ **Visual Reports**: Floating window with full details  
✅ **Real Metrics**: Live Prometheus integration  
✅ **One-Liner Commands**: `make report-health`  
✅ **Customizable**: Add your own reports  
✅ **Professional**: Great for demos and reviews  

**Ask Athena anything, she'll show and tell!** 🗣️📊

---

*Created: October 12, 2025*  
*Status: Production-ready*  
*PRD Tags: ST-104, ST-108*

