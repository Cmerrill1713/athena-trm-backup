# Governance ChatOps: Human-in-the-Loop Control

## Overview

Your governance system now includes **ChatOps capabilities** - human operators can interact with the governance control plane directly from Slack without leaving the conversation. This provides fine-grained control while maintaining the system's autonomous operation.

## 🚀 Available Slash Commands

### `/governance-status`
**Purpose**: Get real-time governance system status

**What it shows**:
- Current gate check status (PASSED/BLOCKED)
- Recent canary decisions (last 5)
- Active threshold overrides
- System timestamp

**Example Output**:
```
*Governance Status Report*

🔍 *Gate Check*: ✅ PASSED

📋 *Recent Decisions*:
Tue Oct 14 19:25:19 2025 - DECISION: HOLD - REASON: samples=None < 200 - METRICS: {...}

🕐 *Timestamp*: Tue Oct 14 19:30:15 2025
```

### `/governance-force-promote`
**Purpose**: Emergency override to force promote current canary

**Use Case**: When operators determine canary is safe despite governance metrics

**Actions**:
- Executes `gov_promote.sh`
- Logs manual override to audit trail
- Sends confirmation notification

**Example**: `/governance-force-promote`

### `/governance-force-rollback`
**Purpose**: Emergency rollback of current canary

**Use Case**: Immediate rollback needed before governance catches it

**Actions**:
- Executes `gov_rollback.sh`
- Logs emergency rollback to audit trail
- Sends rollback notification

**Example**: `/governance-force-rollback`

### `/governance-override`
**Purpose**: Temporarily adjust governance thresholds

**Parameters**:
- `threshold=X`: New ECE threshold (e.g., 0.08)
- `duration=Y`: Override duration in seconds (default: 300)

**Use Case**: Temporary threshold adjustment for known issues

**Actions**:
- Creates temporary override file in `state/threshold_override.json`
- Automatically expires after specified duration
- Logs override to audit trail

**Examples**:
```
/governance-override threshold=0.08 duration=300
/governance-override threshold=0.10
```

## 🛠️ Setup Instructions

### 1. Create Slack App
1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name: "Governance Control Plane"
4. Select your workspace

### 2. Enable Slash Commands
1. In app settings, go to "Slash Commands"
2. Click "Create New Command" for each:

| Command | Request URL | Description |
|---------|-------------|-------------|
| `/governance-status` | `https://your-domain.com/slack/governance` | Get governance status |
| `/governance-force-promote` | `https://your-domain.com/slack/governance` | Force promote canary |
| `/governance-force-rollback` | `https://your-domain.com/slack/governance` | Emergency rollback |
| `/governance-override` | `https://your-domain.com/slack/governance` | Temporary threshold override |

### 3. Configure Request Signing
1. Go to "Basic Information" → "Signing Secret"
2. Copy the signing secret
3. Add to environment: `SLACK_SIGNING_SECRET=your-secret-here`

### 4. Install App to Workspace
1. Go to "Install App" → "Install to Workspace"
2. Authorize the app
3. Invite to governance channels

### 5. Deploy Slack Bot Service
```bash
# Add to your docker-compose.athena-governance.yml (already included)
docker compose up -d governance-slack-bot

# Verify health
curl http://localhost:8082/health
```

## 🔐 Security Features

### Request Verification
- **Slack signature validation** prevents spoofed requests
- **Timestamp validation** prevents replay attacks
- **Channel restrictions** via Slack app permissions

### Audit Logging
- **All manual actions logged** to `logs/canary_decisions.log`
- **Override actions tracked** with expiration timestamps
- **User identification** for accountability

### Access Control
- **Slack app permissions** control who can use commands
- **Channel-specific** deployment for governance-only access
- **No direct system access** - all actions go through governance scripts

## 🎯 Use Cases & Examples

### Emergency Override Scenario
```
Operator: "I can see the canary is actually working fine, just high variance in metrics"
Operator: /governance-force-promote
Bot: ✅ Force Promote Executed - Canary has been promoted via manual override
```

### Temporary Threshold Adjustment
```
Operator: "Known issue causing elevated ECE, allow 0.08 for 10 minutes"
Operator: /governance-override threshold=0.08 duration=600
Bot: ✅ Threshold Override Applied - ECE Threshold: 0.08 (expires: Tue Oct 14 19:40:15 2025)
```

### Status Check During Incident
```
Operator: "What's governance saying right now?"
Operator: /governance-status
Bot: Shows current gate status, recent decisions, active overrides
```

## 🔄 Integration with Existing Systems

### Audit Trail Integration
Manual overrides appear in audit logs with special markers:
```
Tue Oct 14 19:30:15 2025 - DECISION: MANUAL_FORCE_PROMOTE - REASON: Slack command override
Tue Oct 14 19:35:20 2025 - DECISION: MANUAL_FORCE_ROLLBACK - REASON: Slack command emergency rollback
```

### Notification Integration
Manual actions trigger the same notification flows:
- Slack notifications to governance channels
- Grafana annotations on dashboards
- Standard governance alerting

### CI/CD Integration
Slack commands can be triggered from automated systems:
- PagerDuty webhooks
- Monitoring alerts
- Custom automation scripts

## 📊 Monitoring & Metrics

### Slack Bot Health
- **Health endpoint**: `GET /health`
- **Container monitoring** in Docker
- **Log monitoring** for command usage

### Usage Analytics
Track command usage patterns:
```bash
# Commands used today
grep "Slack command" logs/canary_decisions.log | grep "$(date +%F)" | wc -l

# Most active users
grep "Slack command" logs/canary_decisions.log | sed 's/.*user://' | sort | uniq -c | sort -nr
```

### Override Tracking
Monitor threshold override usage:
```bash
# Active overrides
ls -la state/threshold_override.json 2>/dev/null && cat state/threshold_override.json

# Override history
grep "threshold_override" logs/canary_decisions.log
```

## 🚨 Best Practices

### When to Use Manual Overrides
- ✅ **Known false positives** in governance metrics
- ✅ **Emergency situations** requiring immediate action
- ✅ **Temporary issues** with short-term fixes planned
- ❌ **Regular operations** (should be automated)
- ❌ **Permanent changes** (update policy files instead)

### Override Guidelines
- **Always specify duration** for temporary overrides
- **Document reasoning** in override commands when possible
- **Monitor closely** during override periods
- **Review after expiration** to ensure proper resolution

### Access Control
- **Limit to senior operators** who understand governance logic
- **Require approval** for production overrides
- **Log all access** for audit purposes
- **Regular rotation** of Slack app permissions

## 🔧 Troubleshooting

### Command Not Working
```bash
# Check bot health
curl http://localhost:8082/health

# Check logs
docker logs governance-slack-bot

# Test signature verification
# (Bot will show validation errors in logs)
```

### Override Not Taking Effect
```bash
# Check override file
cat state/threshold_override.json

# Check expiration
python3 -c "import json, time; o=json.load(open('state/threshold_override.json')); print('Expires:', time.ctime(o['expires_at']), 'Current:', time.ctime())"
```

### Permissions Issues
- Verify Slack app is installed in the channel
- Check user permissions in Slack app settings
- Confirm webhook URL is accessible

## 📈 Advanced Features

### Custom Commands
Add new slash commands by extending the `process_command` method in `gov_slack_bot.py`.

### Integration Webhooks
The bot can receive webhooks from other systems to trigger automated responses.

### Multi-Environment Support
Configure different Slack channels for different environments (staging, prod, etc.).

---

## 🎯 Impact Summary

| Capability | Before | After |
|------------|--------|-------|
| **Operator Control** | Manual script execution | Chat-based commands |
| **Response Time** | Minutes to execute | Seconds via Slack |
| **Audit Trail** | Partial logging | Complete command tracking |
| **Team Coordination** | Separate tools | Unified chat interface |
| **Emergency Response** | CLI access required | Available from any device |

Your governance system now supports **human-in-the-loop control** while maintaining full autonomy. Operators can fine-tune decisions without breaking the automated control plane! 🧠⚖️💬
