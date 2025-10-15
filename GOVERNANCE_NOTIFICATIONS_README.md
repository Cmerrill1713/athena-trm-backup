# Governance Notifications & Audit Trail

## Overview

Your governance system now provides **real-time team visibility** and **complete audit trails** for all governance decisions. No more guessing what happened - the system tells you immediately via Slack and logs everything for postmortems.

## 🔔 Real-Time Slack Notifications

### Setup
1. **Create Slack App**: Go to https://api.slack.com/apps
2. **Add Webhook**: Create an "Incoming Webhook" for your channel
3. **Get URL**: Copy the webhook URL (starts with `https://hooks.slack.com/services/...`)
4. **Add Secret**: In GitHub repo settings → Secrets → Add `SLACK_WEBHOOK_URL`

### What Gets Notified

The system sends Slack messages for **every governance decision**:

#### ✅ **PROMOTE** (Green)
```
*Governance Decision: PROMOTE*
All KPIs passed. Canary promoted.
```

#### 🚫 **ROLLBACK** (Red)
```
*Governance Decision: ROLLBACK*
Hard breakers triggered. Canary rolled back.
```

#### ⏳ **HOLD** (Yellow)
```
*Governance Decision: HOLD*
Waiting for sufficient signal.
```

### When Notifications Fire

- **GitHub Actions**: After canary analysis completes
- **Automatic**: No manual intervention needed
- **Immediate**: Team sees decisions in real-time

### Notification Script

The `scripts/gov_notify_slack.sh` script handles formatting and delivery:

```bash
# Manual testing
SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..." \
./scripts/gov_notify_slack.sh PROMOTE "Custom message here"
```

## 📋 Complete Audit Trail

### Automatic Logging

Every governance decision gets logged to `logs/canary_decisions.log`:

```log
Tue Oct 14 19:25:19 2025 - DECISION: HOLD - REASON: samples=None < 200 - METRICS: {"solve_rate_delta": null, "violation_rate_delta": null, "latency_p95_delta": null, "ece_post": null, "edge_case_score": null, "consistency_index": null, "samples": null}
```

### Log Structure

Each entry contains:
- **Timestamp**: When the decision was made
- **Decision**: PROMOTE / HOLD / ROLLBACK
- **Reason**: Why the decision was made
- **Metrics**: Complete KPI snapshot at decision time

### Audit Benefits

#### 🔍 **Postmortems & RCA**
- **Historical analysis**: See decision patterns over time
- **KPI correlation**: Understand what metrics drove decisions
- **Timeline reconstruction**: Exact sequence of events

#### 📊 **Performance Tracking**
- **Decision frequency**: How often rollbacks happen
- **Common reasons**: Most frequent failure modes
- **Threshold effectiveness**: Are your governance rules working?

#### 📈 **Improvement Insights**
- **Trend analysis**: Are rollbacks decreasing over time?
- **Metric correlation**: Which KPIs most predict success/failure?
- **Process optimization**: Identify bottlenecks in canary analysis

### Log Management

```bash
# View recent decisions
tail -10 logs/canary_decisions.log

# Search for rollbacks
grep "ROLLBACK" logs/canary_decisions.log

# Analyze decision patterns
grep "DECISION:" logs/canary_decisions.log | cut -d' ' -f4 | sort | uniq -c
```

## 🔧 Technical Implementation

### Slack Notifications

**Script**: `scripts/gov_notify_slack.sh`
- Uses `jq` for JSON formatting
- Requires `SLACK_WEBHOOK_URL` environment variable
- Silent operation (no output unless error)

**GitHub Actions Integration**:
```yaml
- name: Notify Slack on PROMOTE
  if: ${{ steps.decide.outputs.exit_code == '0' }}
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
  run: ./scripts/gov_notify_slack.sh PROMOTE "All KPIs passed. Canary promoted."
```

### Audit Logging

**Location**: `logs/canary_decisions.log`
- **Auto-created**: Directory and file created on first decision
- **Append-only**: Historical decisions preserved
- **Error-tolerant**: Logging failures don't break decisions

**Format**:
```
{TIMESTAMP} - DECISION: {PROMOTE|HOLD|ROLLBACK} - REASON: {explanation} - METRICS: {json}
```

## 🎯 Impact Comparison

| Feature | Before | After |
|---------|--------|-------|
| **Decision visibility** | Manual logs only | Real-time Slack alerts |
| **Team awareness** | After investigation | Immediate notification |
| **Rollback confirmation** | Manual verification | Slack message with reason |
| **Postmortems** | Manual log digging | Complete audit trail |
| **Process transparency** | Opaque | Fully visible |

## 🚀 Usage Examples

### Local Testing

```bash
# Test notifications
SLACK_WEBHOOK_URL="https://test.com" ./scripts/gov_notify_slack.sh PROMOTE "Test message"

# Test decision logging
make governance-canary-watch  # Creates audit entry

# View audit trail
tail -5 logs/canary_decisions.log
```

### Production Monitoring

1. **Watch Slack channel** for governance decisions
2. **Check audit logs** during postmortems
3. **Analyze trends** to improve governance rules
4. **Correlate KPIs** with business outcomes

### Log Analysis

```bash
# Decision summary
grep "DECISION:" logs/canary_decisions.log | \
  sed 's/.*DECISION: \([^ ]*\).*/\1/' | \
  sort | uniq -c

# Recent rollbacks with reasons
grep "ROLLBACK" logs/canary_decisions.log | tail -5

# KPI correlation analysis
grep "ROLLBACK" logs/canary_decisions.log | \
  grep -o '"ece_post":[^,}]*' | \
  sort | uniq -c
```

## 🛡️ Reliability Features

### Slack Notifications
- **Fails gracefully**: Network issues don't break CI/CD
- **No sensitive data**: Only decision status and basic message
- **Configurable**: Easy to enable/disable per environment

### Audit Logging
- **Never fails decisions**: Logging errors don't affect governance logic
- **Atomic writes**: Complete log entries or none
- **Structured data**: JSON metrics for programmatic analysis

## 📋 Setup Checklist

### Slack Setup
- [ ] Create Slack app with incoming webhook
- [ ] Get webhook URL
- [ ] Add `SLACK_WEBHOOK_URL` to GitHub secrets
- [ ] Test notification: `./scripts/gov_notify_slack.sh TEST "Hello world"`

### Audit Trail
- [ ] Verify `logs/` directory exists
- [ ] Run test decision: `make governance-canary-watch`
- [ ] Check log created: `cat logs/canary_decisions.log`
- [ ] Verify JSON structure is valid

### Integration Testing
- [ ] Run canary workflow manually
- [ ] Verify Slack notifications arrive
- [ ] Check audit log has new entries
- [ ] Confirm CI/CD pipeline completes successfully

---

Your governance system now has **complete transparency and accountability**. The team sees every decision immediately, and you have full audit trails for analysis and improvement. No more governance black boxes! 🧠⚖️📢
