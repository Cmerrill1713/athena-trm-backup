#!/usr/bin/env python3
"""
FOP Federation Gateway API
FastAPI-based REST API for AI Republic Federation Onboarding Protocol.

This gateway handles jurisdiction onboarding, evidence exchange,
and federation coordination with full cryptographic security.
"""

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional
import time
import json
import hashlib
import uuid
import yaml
import uvicorn

# Import federation components
from fop_reputation_agg import ReputationEngine

app = FastAPI(
    title="AI Republic Federation Gateway (FOP)",
    version="3.0",
    description="Federation Onboarding Protocol for Sovereign AI Jurisdictions"
)

# Load configuration
CONFIG_FILE = '/etc/ai-republic/federation.yaml'
try:
    with open(CONFIG_FILE, 'r') as f:
        CONFIG = yaml.safe_load(f)
except FileNotFoundError:
    CONFIG = {
        'api': {'port': 8094, 'host': '0.0.0.0'},
        'security': {'mtls_required': True},
        'limits': {'publish_per_min': 60, 'feed_page': 500}
    }

# Initialize reputation engine
reputation_engine = ReputationEngine()
reputation_engine.load_state()

# In-memory storage (replace with proper database in production)
memberships = {}  # did -> membership_info
evidence_store = []  # List of evidence items
evidence_batches = {}  # batch_id -> evidence_list

# --- Minimal stub verifiers (replace with real mTLS + JWS verify) ---
def verify_mtls(req: Request) -> bool:
    """Verify mutual TLS authentication"""
    # In production: check client certificate against federation CA
    return True

def verify_jws(payload: dict, jws: str, expected_did: str = None) -> bool:
    """Verify JWS signature"""
    # In production: verify EdDSA signature and extract signer DID
    return isinstance(jws, str) and len(jws) > 20

def get_client_did(req: Request) -> str:
    """Extract client DID from mTLS certificate"""
    # In production: extract from client certificate
    return "did:airep:stub_did_for_testing"

# --- Pydantic Models ---

class JoinRequest(BaseModel):
    """Federation join request"""
    did: str = Field(..., description="Jurisdiction DID")
    attestation: Dict[str, Any] = Field(..., description="FOP attestation document")
    jws: str = Field(..., description="JWS signature over attestation")

    @validator('did')
    def validate_did(cls, v):
        if not v.startswith('did:airep:') or len(v) != 71:  # did:airep: + 64 chars
            raise ValueError('Invalid DID format')
        return v

class JoinAck(BaseModel):
    """Join request acknowledgment"""
    accepted: bool
    assigned_tier: str = "PROVISIONAL"
    reason: str = ""
    treaty_version: str = "FOP-1.0"
    membership_id: Optional[str] = None

class EvidenceItem(BaseModel):
    """Evidence submission model"""
    evidence_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    publisher_did: str
    category: str = Field(..., examples=["drift_pattern", "quarantine_outcome"])
    payload: Dict[str, Any] = {}
    hash: str
    merkle_root: str
    k_anonymity_bucket: int = 5
    epsilon: float = 0.3
    ts: float = Field(default_factory=time.time)
    jws: str
    metadata: Optional[Dict[str, Any]] = {}

    @validator('category')
    def validate_category(cls, v):
        valid_categories = [
            "drift_pattern", "quarantine_outcome", "tribunal_summary",
            "policy_delta", "threat_indicator", "performance_anomaly",
            "security_incident", "constitutional_event"
        ]
        if v not in valid_categories:
            raise ValueError(f'Invalid category. Must be one of: {valid_categories}')
        return v

class EvidenceBatch(BaseModel):
    """Evidence batch for processing"""
    batch_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    evidence_items: List[EvidenceItem]
    batch_merkle_root: str
    publisher_did: str
    timestamp: float = Field(default_factory=time.time)

class ReputationUpdate(BaseModel):
    """Reputation update event"""
    jurisdiction_did: str
    event_type: str = Field(..., examples=["clean_audit_window", "peer_endorse"])
    delta: float
    reason: str = ""
    evidence: Optional[Dict[str, Any]] = {}

# --- API Routes ---

@app.get("/v1/health", tags=["System"])
async def v1_health():
    """Federation gateway health check"""
    return {
        "status": "operational",
        "version": "FOP-3.0",
        "uptime": time.time(),
        "active_jurisdictions": len(memberships),
        "evidence_items": len(evidence_store),
        "reputation_calculations": len(reputation_engine.event_history)
    }

@app.post("/v1/join", response_model=JoinAck, tags=["Membership"])
async def v1_join(req: Request, jr: JoinRequest):
    """Join the AI Republic federation"""
    if CONFIG.get('security', {}).get('mtls_required', True) and not verify_mtls(req):
        raise HTTPException(401, "Mutual TLS authentication required")

    if not verify_jws(jr.attestation, jr.jws):
        raise HTTPException(400, "Invalid JWS signature")

    # Validate attestation structure
    attestation = jr.attestation
    required_fields = ['articles_fingerprint', 'judicial_slo', 'audit_root']
    for field in required_fields:
        if field not in attestation:
            raise HTTPException(400, f"Missing required attestation field: {field}")

    # Check SLO compliance
    slo = attestation.get('judicial_slo', {})
    engine_ms = slo.get('engine_ms_p95', 999)
    api_ms = slo.get('api_ms_p95', 999)

    if engine_ms > 20 or api_ms > 200:
        return JoinAck(
            accepted=False,
            assigned_tier="PROVISIONAL",
            reason="Judicial SLO requirements not met"
        )

    # Assign initial tier based on attestation quality
    assigned_tier = "TRUSTED"  # Default for compliant attestations

    # Create membership record
    membership_id = str(uuid.uuid4())
    memberships[jr.did] = {
        'membership_id': membership_id,
        'tier': assigned_tier,
        'joined_at': time.time(),
        'attestation': attestation,
        'last_activity': time.time()
    }

    return JoinAck(
        accepted=True,
        assigned_tier=assigned_tier,
        reason="Successfully joined federation",
        treaty_version="FOP-1.0",
        membership_id=membership_id
    )

@app.post("/v1/evidence/publish", tags=["Evidence"])
async def v1_publish(req: Request, evidence: EvidenceItem):
    """Publish evidence to federation"""
    if CONFIG.get('security', {}).get('mtls_required', True) and not verify_mtls(req):
        raise HTTPException(401, "Mutual TLS authentication required")

    client_did = get_client_did(req)

    # Verify publisher authorization
    if client_did not in memberships:
        raise HTTPException(403, "Jurisdiction not a federation member")

    # Verify evidence integrity
    payload_str = json.dumps(evidence.payload, sort_keys=True, separators=(',', ':'))
    expected_hash = hashlib.sha256(payload_str.encode()).hexdigest()
    if expected_hash != evidence.hash:
        raise HTTPException(400, "Evidence hash mismatch")

    if not verify_jws(evidence.payload, evidence.jws, evidence.publisher_did):
        raise HTTPException(400, "Invalid evidence JWS signature")

    # Check publisher DID matches client
    if evidence.publisher_did != client_did:
        raise HTTPException(403, "Publisher DID mismatch")

    # Add to evidence store
    evidence_dict = evidence.dict()
    evidence_dict['received_at'] = time.time()
    evidence_store.append(evidence_dict)

    # Keep store bounded (last 10000 items)
    if len(evidence_store) > 10000:
        evidence_store[:] = evidence_store[-5000:]

    return {
        "status": "published",
        "evidence_id": evidence.evidence_id,
        "received_at": evidence_dict['received_at']
    }

@app.get("/v1/evidence/feed", tags=["Evidence"])
async def v1_feed(
    req: Request,
    start: float = 0.0,
    limit: int = 100,
    category: Optional[str] = None,
    publisher_did: Optional[str] = None
):
    """Consume federation evidence feed"""
    if CONFIG.get('security', {}).get('mtls_required', True) and not verify_mtls(req):
        raise HTTPException(401, "Mutual TLS authentication required")

    client_did = get_client_did(req)

    # Verify consumer authorization
    if client_did not in memberships:
        raise HTTPException(403, "Jurisdiction not a federation member")

    # Filter evidence based on tier and parameters
    member_tier = memberships[client_did]['tier']
    filtered_evidence = []

    for item in evidence_store:
        # Time-based filtering
        if item['ts'] <= start:
            continue

        # Category filtering
        if category and item['category'] != category:
            continue

        # Publisher filtering
        if publisher_did and item['publisher_did'] != publisher_did:
            continue

        # Tier-based access control
        if member_tier == 'QUARANTINED':
            continue  # No access
        elif member_tier == 'PROVISIONAL':
            # Limited access - only anonymized summaries
            if item.get('k_anonymity_bucket', 0) < 5:
                continue
        # TRUSTED and SOVEREIGN get full access

        filtered_evidence.append(item)

        if len(filtered_evidence) >= limit:
            break

    return {
        "items": filtered_evidence,
        "count": len(filtered_evidence),
        "next": filtered_evidence[-1]['ts'] if filtered_evidence else start
    }

@app.post("/v1/leave", tags=["Membership"])
async def v1_leave(req: Request, body: Dict[str, Any]):
    """Leave the federation"""
    if CONFIG.get('security', {}).get('mtls_required', True) and not verify_mtls(req):
        raise HTTPException(401, "Mutual TLS authentication required")

    client_did = get_client_did(req)

    if client_did not in memberships:
        raise HTTPException(404, "Jurisdiction not found in federation")

    # Remove membership
    del memberships[client_did]

    return {"status": "exited", "did": client_did, "timestamp": time.time()}

@app.get("/v1/reputation/{did}", tags=["Reputation"])
async def v1_get_reputation(req: Request, did: str):
    """Get jurisdiction reputation status"""
    if CONFIG.get('security', {}).get('mtls_required', True) and not verify_mtls(req):
        raise HTTPException(401, "Mutual TLS authentication required")

    status = reputation_engine.get_jurisdiction_status(did)

    return {
        "did": did,
        "reputation_score": status['reputation_score'],
        "tier": status['tier'],
        "tier_requirements": status['tier_requirements'],
        "last_updated": status['last_updated'],
        "event_count": status['event_count']
    }

@app.get("/v1/reputation/overview", tags=["Reputation"])
async def v1_reputation_overview(req: Request):
    """Get federation reputation overview"""
    if CONFIG.get('security', {}).get('mtls_required', True) and not verify_mtls(req):
        raise HTTPException(401, "Mutual TLS authentication required")

    overview = reputation_engine.get_federation_overview()

    return overview

@app.post("/v1/reputation/update", tags=["Reputation"])
async def v1_reputation_update(req: Request, update: ReputationUpdate, background_tasks: BackgroundTasks):
    """Submit reputation update event"""
    if CONFIG.get('security', {}).get('mtls_required', True) and not verify_mtls(req):
        raise HTTPException(401, "Mutual TLS authentication required")

    client_did = get_client_did(req)

    # Create reputation event
    event = {
        'did': update.jurisdiction_did,
        'type': update.event_type,
        'timestamp': time.time(),
        'reason': update.reason,
        'evidence': update.evidence or {},
        'submitted_by': client_did
    }

    # Process event asynchronously
    background_tasks.add_task(reputation_engine.process_events, [event])

    return {"status": "queued", "event_id": str(uuid.uuid4())}

@app.get("/v1/membership/{did}", tags=["Membership"])
async def v1_get_membership(req: Request, did: str):
    """Get jurisdiction membership status"""
    if CONFIG.get('security', {}).get('mtls_required', True) and not verify_mtls(req):
        raise HTTPException(401, "Mutual TLS authentication required")

    if did not in memberships:
        raise HTTPException(404, "Jurisdiction not found")

    membership = memberships[did].copy()
    # Remove sensitive data
    membership.pop('attestation', None)

    return membership

# --- Startup ---
if __name__ == "__main__":
    port = CONFIG.get('api', {}).get('port', 8094)
    host = CONFIG.get('api', {}).get('host', '0.0.0.0')

    print(f"Starting FOP Federation Gateway on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
