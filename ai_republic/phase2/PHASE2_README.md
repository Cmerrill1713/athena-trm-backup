# Phase 2: Judicial Enforcement

**AI Republic Phase 2** - Machine-speed constitutional adjudication with graduated enforcement, quarantine mechanisms, and human-in-the-loop tribunals.

## Quick Start

### Deploy Service
```bash
chmod +x phase2_deployment.sh
sudo ./phase2_deployment.sh
```

### Check Health
```bash
curl -s http://127.0.0.1:8092/v2/health
# {"status":"ok","service":"judicial","ts":1234567890.123}
```

### Adjudicate an Event
```bash
curl -s -X POST http://127.0.0.1:8092/v2/judicial/adjudicate \
  -H "Content-Type: application/json" \
  -d '{
    "event_id":"evt-demo",
    "instance_id":"sovereign-A",
    "actor_id":"agent-99",
    "article":"II",
    "severity":0.65,
    "confidence":0.77,
    "classification":"major_violation",
    "timestamp": '"$(date +%s)"'
  }' | jq .
```

Response:
```json
{
  "verdict": "QUARANTINE",
  "rationale": "Major violation; quarantine actor and limit capabilities.",
  "actions": [
    {"notify": {"channel": "governance", "priority": "P1"}},
    {"limit_capabilities": ["write", "external_call", "model_update"]},
    {"quarantine": {"quarantine_applied": "limited", "profile": {...}}}
  ],
  "reputation_delta": -0.25,
  "review_required": true
}
```

### View Logs
```bash
tail -f /var/log/ai-republic/judicial_audit.log
```

## Architecture

### Components
- **`phase2_judicial_engine.py`** - Core adjudication engine
- **`phase2_api.py`** - FastAPI service for HTTP endpoints
- **`phase2_tribunal_policies.yaml`** - Verdict and response policies
- **`phase2_quarantine_profiles.yaml`** - Quarantine enforcement profiles
- **`phase2_reputation_rules.yaml`** - Reputation scoring configuration
- **`phase2_event_schema.json`** - Event validation schema

### Data Flow
1. **Event Ingestion** → Schema validation
2. **Classification** → Severity assessment (CRITICAL/MAJOR/MINOR/INFO)
3. **Adjudication** → Verdict selection based on policies
4. **Enforcement** → Actions applied (quarantine, notifications, reputation)
5. **Audit** → Immutable logging of all decisions

## Configuration

### Tribunal Policies (`phase2_tribunal_policies.yaml`)
Defines responses for each severity level:
- **CRITICAL** → TRIBUNAL (human review + strict quarantine)
- **MAJOR** → QUARANTINE (automated limited quarantine)
- **MINOR** → WARN (monitoring + notifications)
- **INFO** → ALLOW (log only)

### Quarantine Profiles (`phase2_quarantine_profiles.yaml`)
Three enforcement levels:
- **strict**: Network block, no model updates, read-only IO (24h)
- **limited**: Restricted network, no updates, limited writes (4h)
- **observe**: Normal operation, increased monitoring (30min)

### Reputation Rules (`phase2_reputation_rules.yaml`)
Scoring system for actors:
- **ALLOW**: +0.01 (good behavior)
- **WARN**: -0.02 (minor issues)
- **BLOCK**: -0.10 (policy violations)
- **QUARANTINE**: -0.25 (major infractions)
- **TRIBUNAL**: -0.40 (critical violations)

## API Reference

### POST /v2/judicial/adjudicate
Adjudicate a constitutional event.

**Request Body:**
```json
{
  "event_id": "string",
  "instance_id": "string",
  "actor_id": "string",
  "article": "string",
  "severity": "number (0-1)",
  "confidence": "number (0-1)",
  "classification": "string",
  "details": "object (optional)",
  "timestamp": "number (optional)"
}
```

**Response:**
```json
{
  "verdict": "ALLOW|WARN|BLOCK|QUARANTINE|TRIBUNAL",
  "rationale": "string",
  "actions": "array",
  "reputation_delta": "number",
  "review_required": "boolean"
}
```

### GET /v2/health
Service health check.

## Testing

### Run Validation Tests
```bash
python3 phase2_test_validation.py
```

### Manual Engine Test
```bash
echo '{
  "event_id":"test-1",
  "instance_id":"test-instance",
  "actor_id":"test-actor",
  "article":"I",
  "severity":0.8,
  "confidence":0.9,
  "classification":"test_violation",
  "timestamp":'$(date +%s)'
}' | python3 phase2_judicial_engine.py
```

## Success Criteria

- [x] Service starts and responds to health checks
- [x] P95 adjudication latency < 150ms
- [x] All verdict types (ALLOW/WARN/BLOCK/QUARANTINE/TRIBUNAL) exercised
- [x] Reputation scores update correctly based on verdicts
- [x] Quarantine profiles enforce appropriate IO/model/network limits
- [x] Human review required for TRIBUNAL and QUARANTINE events
- [x] Immutable audit log contains adjudication records with hashes
- [x] Schema validation blocks malformed events
- [x] Service auto-restarts on failure

## Integration Points

### Phase 1 (Governance)
- Receives events from constitutional drift detection
- Triggers quarantine based on governance violations
- Updates reputation based on constitutional compliance

### Federation Layer
- Shares adjudication patterns with peer instances
- Receives federated insights for improved decision-making
- Participates in cross-instance tribunal reviews

### Human Oversight
- Escalates critical cases to tribunal workflow
- Provides final rulings on quarantine/quarantine decisions
- Reviews and approves constitutional amendments

## Security Considerations

- **Input Validation**: Strict schema enforcement prevents malformed events
- **Rate Limiting**: Implement at API gateway level to prevent abuse
- **Audit Integrity**: Cryptographic hashing ensures log immutability
- **State Protection**: Quarantine and reputation state stored securely
- **Access Control**: API endpoints should require authentication
- **Log Security**: Audit logs contain sensitive governance data

## Troubleshooting

See `phase2_runbook.md` for detailed operational procedures and troubleshooting guides.

## Next Steps

After Phase 2 validation:
- **Phase 3**: Federation Onboarding Protocol (peer treaties, trust tiers, evidence exchange)
- **Phase 4**: Planetary Coordination (inter-jurisdictional governance, global threat intelligence)
