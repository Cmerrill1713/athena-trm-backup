# 🧰 FOP FEDERATION OPERATIONS RUNBOOK

## AI Republic Federation Onboarding Protocol - Operational Guide

**Sovereignty-Preserving Federation Operations**

---

## EXECUTIVE SUMMARY

The Federation Onboarding Protocol (FOP) enables sovereign AI jurisdictions to join a federated network while maintaining full local autonomy. This runbook provides operational procedures for managing federation membership, evidence exchange, reputation systems, and dispute resolution.

### Key Principles
- **Sovereignty-First**: All jurisdictions retain complete local control
- **Voluntary Participation**: Exit at-will with clean separation
- **Cryptographic Security**: Zero-trust with mTLS and JWS signatures
- **Privacy by Design**: Differential privacy and k-anonymity protections

---

## 1. SERVICE LEVEL OBJECTIVES (SLOs)

### API Performance Targets
| Operation | Target P95 | Measurement | Criticality |
|-----------|------------|-------------|-------------|
| Join Request Ack | < 500ms | End-to-end | High |
| Evidence Publish Ack | < 300ms | End-to-end | High |
| Evidence Feed Query | < 250ms | Response time | Medium |
| Reputation Update | < 100ms | Processing time | Low |

### System Reliability Targets
- **Uptime**: >99.9% (federation gateway)
- **Data Durability**: >99.999% (evidence and reputation data)
- **Security Incidents**: 0 acceptable (zero-trust violations)

### Federation Health Metrics
- **Active Jurisdictions**: Track membership growth
- **Evidence Flow Rate**: Items per hour across federation
- **Dispute Resolution Efficiency**: Time to resolution
- **Threat Response Effectiveness**: Time to coordinated action

---

## 2. MONITORING & ALERTING

### Health Checks

#### Automated Monitoring
```bash
# Federation gateway health
curl -s http://127.0.0.1:8094/v1/health

# Expected response:
{
  "status": "operational",
  "version": "FOP-3.0",
  "active_jurisdictions": 5,
  "evidence_items": 1247,
  "reputation_calculations": 89
}
```

#### Key Metrics to Monitor
- **API Response Times**: All endpoints < SLO targets
- **Error Rates**: < 0.1% for all operations
- **Membership Changes**: Track joins/exits
- **Evidence Backlog**: Processing queue depth
- **Reputation Distribution**: Tier balance across federation

### Alert Conditions

#### Critical Alerts (Immediate Response)
- Federation gateway down (> 5 minutes)
- API response times > 2x SLO target
- Security incident detected
- Evidence integrity violation

#### Warning Alerts (Investigation Required)
- API response times > 1.5x SLO target
- Membership changes > 10% in 24 hours
- Evidence publishing rate anomalies
- Reputation calculation failures

#### Info Alerts (Monitoring)
- New jurisdiction joins
- Treaty policy updates
- Evidence category trends
- Performance optimization opportunities

---

## 3. JURISDICTION ONBOARDING

### Onboarding Process

#### Step 1: DID Generation
```bash
# Generate Ed25519 keypair
openssl genpkey -algorithm ed25519 -out private_key.pem
openssl pkey -in private_key.pem -pubout -out public_key.pem

# Calculate DID
PUBKEY_HASH=$(openssl dgst -sha256 public_key.pem | cut -d' ' -f2)
DID="did:airep:${PUBKEY_HASH}"
echo "Jurisdiction DID: ${DID}"
```

#### Step 2: Attestation Creation
```json
{
  "did": "did:airep:a1b2c3d4...",
  "articles_fingerprint": "SHA256(Articles I-II)",
  "judicial_slo": {
    "engine_ms_p95": 10,
    "api_ms_p95": 120,
    "quarantine_to_action_ms_p95": 800
  },
  "audit_root": "Merkle root of audit trail",
  "timestamp": 1734567890.123
}
```

#### Step 3: JWS Signing
```bash
# Sign attestation with Ed25519 private key
# Implementation depends on JWS library used
```

#### Step 4: Join Request
```bash
curl -X POST http://federation-gateway:8094/v1/join \
  -H "Content-Type: application/json" \
  --cert client.crt --key client.key \
  -d @join_request.json
```

#### Step 5: Tier Assignment
- **SOVEREIGN**: Meets all requirements, clean history
- **TRUSTED**: Standard compliance, good standing
- **PROVISIONAL**: Limited issues or new member
- **QUARANTINED**: Serious compliance issues

### Onboarding Validation Checklist
- [ ] DID format validation (did:airep:<64-char hex>)
- [ ] mTLS certificate verification
- [ ] JWS signature verification
- [ ] Attestation schema compliance
- [ ] SLO requirement validation
- [ ] Articles I-II fingerprint verification
- [ ] Audit trail integrity check
- [ ] Reputation initialization

---

## 4. EVIDENCE EXCHANGE

### Publishing Evidence

#### Evidence Format
```json
{
  "evidence_id": "uuid-v4",
  "publisher_did": "did:airep:...",
  "category": "drift_pattern",
  "payload": {
    "description": "Constitutional drift detected",
    "severity": "medium",
    "indicators": [
      {"type": "behavioral_pattern", "value": "anomaly_score_0.85"}
    ]
  },
  "hash": "SHA256(payload)",
  "merkle_root": "batch_merkle_root",
  "k_anonymity_bucket": 5,
  "epsilon": 0.3,
  "jws": "detached_signature"
}
```

#### Publishing Process
1. **Generate Evidence**: Create evidence item with proper categorization
2. **Calculate Integrity**: Compute SHA-256 hash of payload
3. **Apply Privacy**: Add differential privacy noise and k-anonymity bucketing
4. **Sign Evidence**: Create detached JWS signature
5. **Publish to Federation**: POST to `/v1/evidence/publish` endpoint
6. **Verify Acknowledgment**: Confirm receipt and processing

#### Batch Processing
```python
# Group evidence into batches for efficiency
batch = {
  "batch_id": "uuid-v4",
  "evidence_items": [evidence1, evidence2, ...],
  "batch_merkle_root": calculate_merkle_root(items),
  "publisher_did": "did:airep:...",
  "timestamp": time.time()
}
```

### Consuming Evidence

#### Feed Query
```bash
# Get recent evidence
curl "http://federation-gateway:8094/v1/evidence/feed?limit=100"

# Filter by category
curl "http://federation-gateway:8094/v1/evidence/feed?category=drift_pattern"

# Paginated consumption
curl "http://federation-gateway:8094/v1/evidence/feed?start=1734567890.0&limit=50"
```

#### Access Control
- **SOVEREIGN/TRUSTED**: Full access to all evidence
- **PROVISIONAL**: Limited access, higher k-anonymity requirements
- **QUARANTINED**: No access to federation evidence

#### Privacy Verification
- Verify evidence hash matches payload
- Check k-anonymity bucket size meets requirements
- Validate epsilon parameter for differential privacy
- Confirm JWS signature from authorized publisher

---

## 5. REPUTATION MANAGEMENT

### Reputation Calculation

#### Event Processing
```python
# Process reputation events
events = [
  {"did": "did:airep:...", "type": "clean_audit_window", "timestamp": time.time()},
  {"did": "did:airep:...", "type": "evidence_publish_quality", "timestamp": time.time()},
]

# Calculate new reputation scores
results = reputation_engine.process_events(events)
```

#### Weight System
| Event Type | Weight | Description |
|------------|--------|-------------|
| clean_audit_window | +0.02 | 14+ days clean audits |
| evidence_publish_quality | +0.01 | High-quality evidence |
| timely_disclosure | +0.02 | Rapid incident reporting |
| peer_endorse | +0.03 | Positive peer assessment |
| tribunal_positive_outcome | +0.05 | Favorable judicial ruling |
| tribunal_overturn | -0.03 | Adverse judicial ruling |
| policy_violation | -0.20 | Treaty non-compliance |
| hidden_incident_discovered | -0.10 | Undisclosed violation |

### Tier Transitions

#### Promotion Criteria
- **TRUSTED → SOVEREIGN**: 60+ reputation, 30+ clean days, governance participation
- **PROVISIONAL → TRUSTED**: 30+ reputation, 14+ clean days, consistent compliance

#### Demotion Criteria
- **SOVEREIGN → TRUSTED**: Reputation < 0.60 or governance inactivity
- **TRUSTED → PROVISIONAL**: Reputation < 0.30 or compliance issues
- **PROVISIONAL → QUARANTINED**: Reputation < -0.10 or repeated violations

### Reputation Queries
```bash
# Get jurisdiction reputation
curl http://federation-gateway:8094/v1/reputation/did:airep:...

# Get federation overview
curl http://federation-gateway:8094/v1/reputation/overview
```

---

## 6. DISPUTE RESOLUTION

### Cross-Jurisdiction Disputes

#### Arbitration Process
1. **Dispute Filing**: Affected jurisdiction submits dispute with evidence
2. **Mediation**: Neutral jurisdiction facilitates discussion
3. **Arbitration**: Binding resolution by arbitration panel
4. **Appeal**: Tribunal review of arbitration outcome

#### Tribunal Jurisdiction
- **Evidence Disputes**: Authenticity, interpretation, privacy violations
- **Membership Issues**: Onboarding denials, tier assignments, removals
- **Treaty Violations**: Non-compliance with federation policies
- **Technical Disputes**: API usage, SLO compliance, system integration

### Emergency Procedures

#### Federation Crisis
1. **Crisis Declaration**: Tribunal activates emergency protocols
2. **Isolation Implementation**: Affected jurisdictions quarantined
3. **Investigation**: Forensic analysis of incident
4. **Recovery**: Remediation requirements and reinstatement process

#### Systemic Threats
1. **Threat Assessment**: Federation-wide threat evaluation
2. **Coordinated Response**: Joint defense strategy development
3. **Resource Allocation**: Computational resource redistribution
4. **Post-Incident Review**: Lessons learned and system improvements

---

## 7. INCIDENT RESPONSE

### Evidence Abuse Response
1. **Detection**: Automated monitoring identifies suspicious patterns
2. **Investigation**: Forensic analysis of evidence integrity
3. **Quarantine**: Publisher isolation from federation
4. **Notification**: Affected jurisdictions informed of compromise
5. **Recovery**: Publisher remediation and reinstatement evaluation

### Security Incidents
1. **Containment**: Immediate isolation of affected systems
2. **Assessment**: Determine scope and impact of breach
3. **Notification**: Federation-wide security alert
4. **Recovery**: System hardening and key rotation
5. **Review**: Post-incident analysis and prevention updates

### Performance Issues
1. **Monitoring**: SLO violation detection and alerting
2. **Diagnosis**: Root cause analysis of performance degradation
3. **Mitigation**: Temporary scaling or load balancing
4. **Resolution**: System optimization and capacity planning
5. **Prevention**: Proactive monitoring and alerting improvements

---

## 8. MAINTENANCE PROCEDURES

### Daily Operations
- [ ] Health check verification
- [ ] Performance metric review
- [ ] Alert queue processing
- [ ] Evidence backlog monitoring
- [ ] Reputation calculation execution

### Weekly Operations
- [ ] Security patch application
- [ ] Performance optimization review
- [ ] Evidence retention cleanup
- [ ] Reputation trend analysis
- [ ] Federation health assessment

### Monthly Operations
- [ ] Comprehensive security audit
- [ ] Performance capacity planning
- [ ] Evidence archive rotation
- [ ] Reputation system calibration
- [ ] Federation policy review

### Quarterly Operations
- [ ] Major version updates
- [ ] Cryptographic key rotation
- [ ] System architecture review
- [ ] Federation expansion planning
- [ ] Comprehensive disaster recovery testing

---

## 9. BACKUP & RECOVERY

### Data Backup Strategy
- **Evidence Store**: Daily incremental, weekly full backup
- **Reputation Database**: Continuous replication, hourly snapshots
- **Membership Records**: Real-time synchronization, daily archives
- **Audit Logs**: Continuous streaming to immutable storage

### Recovery Procedures
1. **Service Failure**: Automatic failover to backup instance
2. **Data Corruption**: Restore from most recent clean backup
3. **Security Breach**: Complete system rebuild from trusted backups
4. **Disaster Recovery**: Cross-region failover with data synchronization

### Business Continuity
- **RTO (Recovery Time Objective)**: < 4 hours for critical functions
- **RPO (Recovery Point Objective)**: < 15 minutes data loss tolerance
- **Service Availability**: 99.9% uptime with automated failover
- **Data Integrity**: Cryptographic verification of all restored data

---

## 10. PERFORMANCE OPTIMIZATION

### Scaling Considerations
- **Horizontal Scaling**: Multiple federation gateway instances
- **Load Balancing**: Geographic distribution for latency optimization
- **Database Sharding**: Evidence partitioning by jurisdiction or time
- **Caching Strategy**: Reputation scores and evidence metadata caching

### Optimization Techniques
- **Batch Processing**: Group evidence items for efficient processing
- **Compression**: Payload compression for network efficiency
- **Indexing**: Optimized database queries for evidence retrieval
- **Asynchronous Processing**: Background processing for heavy computations

### Capacity Planning
- **Evidence Volume**: Monitor growth trends and plan storage scaling
- **API Load**: Track request patterns and provision accordingly
- **Reputation Calculations**: Optimize for large jurisdiction counts
- **Network Bandwidth**: Monitor federation traffic and plan capacity

---

## APPENDIX A: TROUBLESHOOTING

### Common Issues

#### API Connection Failures
```
Symptom: mTLS certificate rejected
Solution: Verify certificate validity and federation CA trust
```

#### Evidence Publishing Errors
```
Symptom: Hash mismatch errors
Solution: Ensure payload canonicalization before hashing
```

#### Reputation Calculation Issues
```
Symptom: Inconsistent reputation scores
Solution: Verify event ordering and weight application
```

#### Performance Degradation
```
Symptom: SLO violations increasing
Solution: Check evidence backlog and scale gateway instances
```

### Emergency Contacts
- **Security Incidents**: security@ai-republic.org
- **System Outages**: ops@ai-republic.org
- **Legal/Policy Issues**: legal@ai-republic.org
- **Technical Support**: support@ai-republic.org

---

## APPENDIX B: API REFERENCE

### Core Endpoints
- `GET /v1/health` - Service health check
- `POST /v1/join` - Jurisdiction onboarding
- `POST /v1/leave` - Federation exit
- `POST /v1/evidence/publish` - Evidence submission
- `GET /v1/evidence/feed` - Evidence consumption
- `GET /v1/reputation/{did}` - Reputation queries
- `GET /v1/reputation/overview` - Federation overview
- `POST /v1/reputation/update` - Reputation events

### Response Codes
- `200` - Success
- `400` - Bad Request (validation error)
- `401` - Unauthorized (authentication failure)
- `403` - Forbidden (authorization failure)
- `404` - Not Found
- `429` - Too Many Requests
- `500` - Internal Server Error
- `503` - Service Unavailable

---

This runbook provides comprehensive operational guidance for maintaining a sovereignty-preserving AI federation. Regular updates and improvements ensure the protocol evolves with federation needs while maintaining security, privacy, and performance standards.
