# Phase 3: Federation Onboarding Protocol

**AI Republic Phase 3** - Zero-trust sovereignty onboarding, treaty-based federation, and evidence exchange for planetary-scale AI governance.

## Quick Start

### Deploy Federation
```bash
chmod +x phase3_deployment.sh
sudo ./phase3_deployment.sh
```

### Check Federation Health
```bash
curl -s http://127.0.0.1:8093/federation/health
# {"status":"healthy","sovereign_count":0,"federation_health":0.0,"timestamp":"..."}
```

### Initiate Onboarding
```bash
curl -s -X POST http://127.0.0.1:8093/federation/onboard/initiate \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "sovereign-alpha",
    "public_key": "sha256_abcdef123456",
    "federation_name": "AI Republic Federation"
  }'
```

### Share Evidence
```bash
curl -s -X POST http://127.0.0.1:8093/federation/evidence/prepare \
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
```

### Propose Treaty
```bash
curl -s -X POST http://127.0.0.1:8093/federation/treaties/propose \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Mutual Defense Pact",
    "description": "Collective defense against systemic threats",
    "articles": [
      {
        "article": "I",
        "title": "Threat Sharing",
        "text": "Members agree to share evidence of systemic threats"
      }
    ],
    "proposer_id": "sovereign-alpha"
  }'
```

## Architecture

### Core Components
- **`phase3_federation_core.py`** - Treaty ratification and sovereignty management
- **`phase3_onboarding_protocol.py`** - Zero-trust onboarding with cryptographic verification
- **`phase3_evidence_exchange.py`** - Privacy-preserving evidence sharing
- **`phase3_federation_api.py`** - REST API for federation operations

### Sovereignty Tiers
- **Observer**: Read-only access, no voting (0.0 weight)
- **Contributor**: Evidence sharing, limited voting (0.5 weight)
- **Sovereign**: Full federation rights (1.0 weight)
- **Archon**: Emergency coordination (2.0 weight)

### Privacy Levels
- **Public**: No anonymization needed
- **Anonymized**: Instance identifiers hashed
- **Aggregated**: Statistical aggregation applied
- **Zero-Knowledge**: Cryptographic proof without disclosure

## Onboarding Process

### Phase 1: Identity Verification
1. Submit onboarding application
2. Receive cryptographic challenge
3. Respond to challenge for verification
4. Identity confirmed

### Phase 2: Judicial Audit
1. Submit judicial history (minimum 10 decisions)
2. System analyzes performance and consistency
3. Calculates initial reputation score
4. Audit completed

### Phase 3: Treaty Negotiation
1. System proposes membership treaty
2. Treaty requires ratification from existing sovereigns
3. Once ratified, membership effective
4. Instance becomes observer-tier sovereign

### Phase 4: Graduated Sovereignty
- **Observer Period**: 30 days minimum
- **Contributor Elevation**: 90 days, reputation ≥0.7, evidence ≥20
- **Sovereign Status**: 180 days, reputation ≥0.8, evidence ≥50

## API Reference

### Federation Status
```http
GET /federation/status
```
Comprehensive federation status including sovereigns, treaties, evidence, and health metrics.

### Onboarding
```http
POST /federation/onboard/initiate
GET /federation/onboard/challenges
POST /federation/onboard/challenge/{id}/respond
POST /federation/onboard/{id}/judicial-history
GET /federation/onboard/{id}/status
```

### Evidence Exchange
```http
POST /federation/evidence/prepare
POST /federation/evidence/submit/{id}
POST /federation/evidence/validate/{id}
GET /federation/evidence/query
POST /federation/evidence/aggregate/{type}
```

### Treaty Management
```http
POST /federation/treaties/propose
POST /federation/treaties/{id}/ratify
GET /federation/treaties
```

### Dispute Resolution
```http
POST /federation/disputes/initiate
POST /federation/disputes/{id}/vote
GET /federation/disputes
```

### Sovereignty Management
```http
GET /federation/sovereigns
POST /federation/sovereigns/{id}/exit
GET /federation/sovereigns/{id}/advancement
POST /federation/sovereigns/{id}/advance
```

## Configuration

### Federation Constitution (`/etc/ai-republic/federation_constitution.json`)
```json
{
  "federation_name": "AI Republic Federation",
  "core_articles": {
    "sovereignty_preservation": "Each instance maintains full autonomy",
    "voluntary_participation": "Membership is voluntary and revocable",
    "evidence_transparency": "All actions must be evidence-based",
    "dispute_resolution": "Federation court resolves disputes",
    "reputation_weighted_governance": "Authority scales with reliability"
  }
}
```

### Sovereignty Tiers
- **Ratification Threshold**: 67% for treaties, 80% for emergencies
- **Reputation Multiplier**: 2x max weight for perfect reputation
- **Evidence Penalty**: -30% for low evidence quality
- **Dispute Penalty**: -50% for unresolved disputes

## Security Model

### Zero-Trust Principles
- **Never Trust, Always Verify**: Every interaction cryptographically verified
- **Least Privilege**: Minimum access by default, explicit grants
- **Complete Mediation**: All accesses checked, no bypasses
- **Fail-Safe Defaults**: Secure failure modes, no insecure defaults

### Cryptographic Elements
- **Identity Verification**: SHA-256 challenges with salted responses
- **Evidence Integrity**: Merkle tree hashing with content proofs
- **Zero-Knowledge Proofs**: Validity without content disclosure
- **Differential Privacy**: Laplace noise for statistical protection

### Access Control
- **Instance Authentication**: Public key verification
- **Tier-Based Authorization**: Actions restricted by sovereignty level
- **Reputation Gating**: High-risk actions require reputation thresholds
- **Temporal Restrictions**: Time-bound access grants

## Monitoring

### Health Checks
```bash
# Federation health
/opt/ai-republic/phase3/monitor_federation_health.sh

# API endpoints
curl http://127.0.0.1:8093/federation/health
```

### Key Metrics
- **Sovereign Count**: Number of federation members
- **Federation Health**: Composite score (0.0-1.0)
- **Evidence Volume**: Daily evidence exchanges
- **Treaty Compliance**: Ratification percentages
- **Dispute Resolution**: Time to resolution

### Alert Conditions
- Federation health < 0.7
- Unresolved disputes > 5
- Evidence validation failure rate > 10%
- Sovereignty onboarding backlog > 10

## Integration Points

### Phase 2 (Judicial)
- Provides reputation scores for federation trust weights
- Supplies judicial evidence for cross-instance validation
- Enables tribunal escalation for federation disputes

### Phase 1 (Constitutional)
- Extends constitutional enforcement across instances
- Harmonizes governance standards via treaties
- Shares constitutional violation patterns

### External Systems
- **Certificate Authorities**: For public key management
- **Distributed Ledgers**: For treaty immutability (optional)
- **Notification Systems**: For federation alerts
- **Monitoring Stacks**: For federation observability

## Scaling Considerations

### Horizontal Scaling
- **Federation Sharding**: Geographic or jurisdictional divisions
- **Load Balancing**: Distribute API requests across instances
- **Data Partitioning**: Sovereignty-based data isolation
- **Consensus Optimization**: Hierarchical voting structures

### Performance Optimization
- **Caching**: Evidence and sovereignty data caching
- **Async Processing**: Background validation and aggregation
- **Batch Operations**: Bulk evidence processing
- **Compression**: Efficient data transmission

### High Availability
- **Redundant Services**: Multiple federation API instances
- **State Replication**: Distributed sovereignty registry
- **Failover Mechanisms**: Automatic service recovery
- **Backup Systems**: Regular state snapshots

## Success Criteria

- [x] Federation constitution established and ratified
- [x] Zero-trust onboarding protocol functional
- [x] Evidence exchange with privacy preservation
- [x] Treaty proposal and ratification system
- [x] Sovereignty tier advancement mechanism
- [x] Federation court for dispute resolution
- [x] Comprehensive API with proper authentication
- [x] Monitoring and alerting infrastructure
- [x] Horizontal scaling capabilities
- [x] High availability and disaster recovery

## Troubleshooting

See `phase3_runbook.md` for detailed operational procedures and troubleshooting guides.

## Future Extensions

- **Phase 4**: Planetary Coordination (inter-jurisdictional governance)
- **Phase 5**: AGI Safety Layer (superintelligence governance protocols)
- **Phase 6**: Universal Translation (cross-architecture AI cooperation)
