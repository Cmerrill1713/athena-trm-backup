# Phase 3 Federation Runbook

## Purpose
Zero-trust sovereignty onboarding, treaty-based federation, and evidence exchange for planetary-scale AI governance coordination.

## Service Architecture

### API Endpoints
- **Federation API**: `http://127.0.0.1:8093/federation/*`
- **Health Check**: `GET /federation/health`
- **Full Status**: `GET /federation/status`

### Ports
- **8092**: Phase 2 Judicial API
- **8093**: Phase 3 Federation API

### Data Storage
- **State Files**: `/var/lib/ai-republic/`
  - `federation_state.json`: Sovereignty registry, treaties, disputes
  - `onboarding_state.json`: Onboarding applications and challenges
  - `evidence_exchange_state.json`: Evidence packages and aggregates
- **Logs**: `/var/log/ai-republic/`
  - `judicial_audit.log`: Phase 2 judicial decisions
  - `federation_health_monitor.log`: Phase 3 health checks

## Onboarding Procedures

### Initiating Onboarding
```bash
# 1. Submit onboarding application
curl -X POST http://127.0.0.1:8093/federation/onboard/initiate \
  -H "Content-Type: application/json" \
  -d '{"instance_id": "sovereign-new", "public_key": "sha256_xxx"}'

# Response includes application_id
{"application_id": "onboard_1234567890_abc", "status": "initiated"}
```

### Identity Verification
```bash
# 2. Get pending challenges
curl http://127.0.0.1:8093/federation/onboard/challenges

# 3. Respond to challenge (instance must compute SHA-256)
echo -n "${challenge_data}_${instance_id}" | sha256sum
# Respond with computed hash
curl -X POST http://127.0.0.1:8093/federation/onboard/challenge/challenge_123/respond \
  -H "Content-Type: application/json" \
  -d '{"response": "computed_sha256_hash"}'
```

### Judicial History Submission
```bash
# 4. Submit judicial history (minimum 10 decisions)
curl -X POST http://127.0.0.1:8093/federation/onboard/onboard_1234567890_abc/judicial-history \
  -H "Content-Type: application/json" \
  -d '[
    {
      "decision_timestamp": "2024-01-01T00:00:00Z",
      "verdict": "QUARANTINE",
      "severity": 0.8,
      "article": "II"
    }
    // ... 9+ more decisions
  ]'
```

### Treaty Ratification
```bash
# 5. Check treaty ratification status
curl http://127.0.0.1:8093/federation/onboard/onboard_1234567890_abc/treaty-check

# 6. Existing sovereigns must ratify
curl -X POST http://127.0.0.1:8093/federation/treaties/treaty_xxx/ratify \
  -H "Content-Type: application/json" \
  -d '{"sovereign_id": "existing_sovereign"}'
```

### Sovereignty Advancement
```bash
# Check advancement eligibility
curl http://127.0.0.1:8093/federation/sovereigns/sovereign-new/advancement

# Advance to next tier
curl -X POST http://127.0.0.1:8093/federation/sovereigns/sovereign-new/advance
```

## Evidence Exchange Procedures

### Sharing Evidence
```bash
# 1. Prepare evidence package
curl -X POST http://127.0.0.1:8093/federation/evidence/prepare \
  -H "Content-Type: application/json" \
  -d '{
    "evidence_type": "judicial_decision",
    "content": {
      "actor_id": "agent_123",
      "verdict": "QUARANTINE",
      "severity": 0.85
    },
    "privacy_level": "anonymized"
  }'

# 2. Submit for federation validation
curl -X POST http://127.0.0.1:8093/federation/evidence/submit/package_xxx
```

### Validating Evidence
```bash
# Sovereigns validate evidence packages
curl -X POST http://127.0.0.1:8093/federation/evidence/validate/package_xxx \
  -H "Content-Type: application/json" \
  -d '{
    "validator_instance": "sovereign-validator",
    "approved": true
  }'
```

### Querying Evidence
```bash
# Query federation evidence
curl "http://127.0.0.1:8093/federation/evidence/query?evidence_type=judicial_decision&date_from=2024-01-01T00:00:00Z"
```

### Creating Aggregates
```bash
# Create statistical aggregate for privacy
curl -X POST http://127.0.0.1:8093/federation/evidence/aggregate/judicial_decision \
  -H "Content-Type: application/json" \
  -d '{"aggregation_hours": 24}'
```

## Treaty Management

### Proposing Treaties
```bash
curl -X POST http://127.0.0.1:8093/federation/treaties/propose \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Mutual Defense Pact",
    "description": "Collective response to systemic threats",
    "articles": [
      {
        "article": "I",
        "title": "Threat Sharing",
        "text": "Members share evidence of systemic threats"
      }
    ],
    "proposer_id": "sovereign-alpha",
    "ratification_threshold": 0.67
  }'
```

### Ratifying Treaties
```bash
# List pending treaties
curl http://127.0.0.1:8093/federation/treaties?status=proposed

# Ratify treaty
curl -X POST http://127.0.0.1:8093/federation/treaties/treaty_xxx/ratify \
  -H "Content-Type: application/json" \
  -d '{"sovereign_id": "sovereign-ratifier"}'
```

## Dispute Resolution

### Initiating Disputes
```bash
curl -X POST http://127.0.0.1:8093/federation/disputes/initiate \
  -H "Content-Type: application/json" \
  -d '{
    "plaintiff_instance": "sovereign-alpha",
    "defendant_instance": "sovereign-beta",
    "treaty_violated": "mutual_defense_pact",
    "evidence_ids": ["evidence_001", "evidence_002"]
  }'
```

### Voting on Disputes
```bash
# Federation court judges vote
curl -X POST http://127.0.0.1:8093/federation/disputes/dispute_xxx/vote \
  -H "Content-Type: application/json" \
  -d '{
    "judge_instance": "sovereign-judge",
    "vote": "plaintiff"
  }'
```

## Sovereignty Management

### Listing Sovereigns
```bash
curl http://127.0.0.1:8093/federation/sovereigns
```

### Sovereign Exit
```bash
curl -X POST http://127.0.0.1:8093/federation/sovereigns/sovereign-exiting/exit \
  -H "Content-Type: application/json" \
  -d '{"exit_reason": "Strategic realignment"}'
```

## Monitoring & Health Checks

### Federation Health
```bash
/opt/ai-republic/phase3/monitor_federation_health.sh
```

### API Health Checks
```bash
# Federation API
curl http://127.0.0.1:8093/federation/health

# Judicial API (Phase 2)
curl http://127.0.0.1:8092/v2/health
```

### Service Status
```bash
systemctl status ai-republic-federation
systemctl status ai-republic-judicial
systemctl status ai-republic-constitutional
```

## Backup & Recovery

### State Backup
```bash
# Backup federation state
cp /var/lib/ai-republic/federation_state.json /backup/federation_$(date +%Y%m%d_%H%M%S).json
cp /var/lib/ai-republic/onboarding_state.json /backup/onboarding_$(date +%Y%m%d_%H%M%S).json
cp /var/lib/ai-republic/evidence_exchange_state.json /backup/evidence_$(date +%Y%m%d_%H%M%S).json
```

### State Recovery
```bash
# Stop services
systemctl stop ai-republic-federation

# Restore state files
cp /backup/federation_20241201_120000.json /var/lib/ai-republic/federation_state.json

# Restart services
systemctl start ai-republic-federation
```

## Troubleshooting

### Common Issues

#### Onboarding Challenges Fail
**Symptom**: Identity verification repeatedly fails
**Check**:
- Instance ID consistency across requests
- SHA-256 computation correctness
- Challenge expiration (15-minute timeout)
**Fix**:
- Regenerate challenge
- Verify cryptographic implementation

#### Treaty Ratification Stuck
**Symptom**: Treaty shows "proposed" status indefinitely
**Check**:
- Eligible sovereign count (must have sovereign/contributor/archon tiers)
- Ratification threshold calculation
- Sovereign connectivity and API access
**Fix**:
- Manually trigger ratification checks
- Verify sovereign tier assignments

#### Evidence Validation Timeout
**Symptom**: Evidence packages stuck in "pending_validation"
**Check**:
- Available validators (sovereign/archon tiers only)
- Validation timeout (24 hours)
- Validator instance connectivity
**Fix**:
- Check validator instance status
- Manually trigger validation completion
- Adjust validation requirements

#### Federation Health Degradation
**Symptom**: Federation health score drops below 0.7
**Check**:
- Sovereign activity and connectivity
- Evidence sharing frequency
- Dispute resolution backlog
- Reputation score distribution
**Fix**:
- Investigate inactive sovereigns
- Clear dispute backlog
- Boost evidence sharing incentives

#### API Timeouts
**Symptom**: Federation API requests timeout
**Check**:
- Service resource utilization (CPU/memory)
- Database file sizes and fragmentation
- Network connectivity and latency
**Fix**:
- Increase timeout values in client code
- Optimize database queries
- Scale service resources

### Debug Commands

#### Check Service Logs
```bash
# Federation service logs
journalctl -u ai-republic-federation -f

# Judicial service logs
journalctl -u ai-republic-judicial -f

# Application logs
tail -f /var/log/ai-republic/judicial_audit.log
```

#### Inspect State Files
```bash
# Federation state
python3 -m json.tool /var/lib/ai-republic/federation_state.json

# Onboarding state
python3 -m json.tool /var/lib/ai-republic/onboarding_state.json

# Evidence state
python3 -m json.tool /var/lib/ai-republic/evidence_exchange_state.json
```

#### Manual State Queries
```bash
# Count sovereigns by tier
python3 -c "
import json
with open('/var/lib/ai-republic/federation_state.json') as f:
    data = json.load(f)
sovereigns = data['sovereigns']
tiers = {}
for s in sovereigns.values():
    tier = s['sovereignty_tier']
    tiers[tier] = tiers.get(tier, 0) + 1
print('Sovereignty distribution:', tiers)
"
```

### Emergency Procedures

#### Federation Split-Brain
**Condition**: Multiple federation instances claim leadership
**Response**:
1. Identify primary instance by constitution timestamp
2. Halt secondary instances
3. Merge evidence and sovereignty registries
4. Restart with unified state

#### Mass Sovereignty Exit
**Condition**: Multiple sovereigns exit simultaneously
**Response**:
1. Assess treaty impact and succession requirements
2. Trigger emergency ratification for critical treaties
3. Redistribute governance responsibilities
4. Communicate exit terms to remaining sovereigns

#### Evidence Corruption
**Condition**: Evidence validation failures exceed 50%
**Response**:
1. Quarantine affected evidence packages
2. Audit evidence validation logic
3. Regenerate cryptographic proofs
4. Implement additional validation layers

## Performance Tuning

### Scaling Recommendations
- **1-10 Sovereigns**: Single federation instance sufficient
- **11-50 Sovereigns**: Add read replicas for evidence queries
- **51-200 Sovereigns**: Implement federation sharding by region
- **200+ Sovereigns**: Hierarchical federation with regional hubs

### Optimization Settings
```json
{
  "evidence_batch_size": 100,
  "validation_timeout_hours": 24,
  "cache_ttl_seconds": 300,
  "max_concurrent_validations": 10,
  "evidence_retention_days": 90
}
```

## Compliance & Audit

### Audit Logging
All federation actions are logged with cryptographic hashes for immutability:
- Sovereignty changes
- Treaty ratifications
- Evidence validations
- Dispute resolutions

### Compliance Checks
- **Data Sovereignty**: All instance data remains under local control
- **Voluntary Participation**: No forced federation membership
- **Evidence Transparency**: All decisions based on verifiable evidence
- **Dispute Fairness**: Equal access to federation court

### Regulatory Alignment
- **GDPR**: Evidence anonymization and consent-based sharing
- **CCPA**: Data minimization and deletion capabilities
- **AI Safety Standards**: Constitutional governance and oversight
- **International Law**: Treaty-based international AI cooperation
