# Phase 2 Judicial Enforcement Runbook

## Purpose
Machine-speed adjudication & quarantine with human-review tribunals for constitutional violations in the AI Republic.

## SLOs
- **P95 adjudication latency**: <10 ms (engine), <150 ms (API)
- **Drift→action**: <1 s for quarantine trigger
- **Uptime**: 99.9% (auto-restart on failure)

## Dashboards
Ingest `judicial_audit.log` into your observability stack (Loki/ELK/Prometheus):
```bash
# Sample log lines
{"type":"adjudication","level":"MAJOR","event":{...},"adjudication":{"verdict":"QUARANTINE",...},"rep_score":-0.25,"hash":"..."}
```

## Incident Flow

### 1. Event Ingestion
- Events arrive via API or direct engine call
- Schema validation ensures required fields present
- Classification determines severity level (CRITICAL/MAJOR/MINOR/INFO)

### 2. Adjudication
- **CRITICAL** → TRIBUNAL verdict → auto-quarantine (strict profile)
- **MAJOR** → QUARANTINE verdict → limited capabilities
- **MINOR** → WARN verdict → increased monitoring
- **INFO** → ALLOW verdict → continue normal operation

### 3. Enforcement
- Quarantine profiles applied immediately
- Reputation scores updated
- Notifications sent to appropriate channels

### 4. Human Review (when required)
- TRIBUNAL and QUARANTINE events require human oversight
- P0 alerts for critical constitutional risks
- Tribunal workflow for final ruling

### 5. Resolution
- Human ruling recorded with hash for immutability
- Quarantine lifted or extended based on ruling
- Reputation adjusted based on final outcome

## Rollback Procedures

### Quarantine Rollback
```bash
# Remove quarantine state
rm /var/lib/ai-republic/phase2/quarantine_{actor_id}.json
# Restore capabilities (implement in your enforcement layer)
```

### Reputation Reset
```bash
# Manual reputation adjustment
echo '{"score": 0.0}' > /var/lib/ai-republic/phase2/rep_{actor_id}.json
```

## Monitoring & Alerts

### Key Metrics
- Adjudication latency (P50/P95/P99)
- Verdict distribution (ALLOW/WARN/BLOCK/QUARANTINE/TRIBUNAL)
- Quarantine duration and success rates
- Reputation score distribution
- Schema validation failure rate

### Alert Conditions
- P95 latency > 150ms
- Tribunal queue > 10 pending reviews
- Reputation scores < -1.0 (expulsion threshold)
- Service unavailable for > 5 minutes

## Troubleshooting

### Common Issues

#### "Schema missing fields" errors
- Check event format matches `phase2_event_schema.json`
- Ensure all required fields are present
- Validate JSON structure

#### Quarantine not applied
- Check `phase2_quarantine_profiles.yaml` syntax
- Verify state directory permissions (`/var/lib/ai-republic/phase2`)
- Check quarantine profile mapping in policies

#### API timeouts
- Increase timeout in client code
- Check system resources (CPU/memory)
- Review adjudication latency metrics

#### Reputation not updating
- Check `phase2_reputation_rules.yaml` syntax
- Verify actor_id consistency
- Check state directory permissions

## Maintenance

### Weekly Tasks
- Review tribunal cases and outcomes
- Analyze verdict distribution trends
- Clean up old quarantine states (>30 days)

### Monthly Tasks
- Audit reputation scores for fairness
- Review and update policy thresholds
- Analyze adjudication performance metrics

### Quarterly Tasks
- Complete security audit of judicial engine
- Review and update quarantine profiles
- Assess effectiveness of graduated enforcement
