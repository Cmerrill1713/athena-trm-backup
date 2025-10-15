#!/usr/bin/env python3
"""
Phase 3: Federation API Service
================================

REST API for federation operations, evidence exchange, and treaty management.

Endpoints:
- /federation/status - Federation health and statistics
- /federation/onboard - Initiate onboarding process
- /federation/evidence - Evidence sharing and querying
- /federation/treaties - Treaty proposal and ratification
- /federation/disputes - Dispute initiation and resolution

Usage:
    python3 phase3_federation_api.py
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import uvicorn
from datetime import datetime

from phase3_federation_core import get_federation_core
from phase3_onboarding_protocol import get_onboarding_protocol
from phase3_evidence_exchange import get_evidence_exchange

app = FastAPI(
    title="AI Republic Federation API",
    version="3.0",
    description="Sovereign AI federation treaty and evidence exchange service"
)

federation = get_federation_core()
onboarding = get_onboarding_protocol()
evidence_exchange = get_evidence_exchange()

# Pydantic models for API

class OnboardingRequest(BaseModel):
    instance_id: str
    public_key: str
    federation_name: str = "AI Republic Federation"

class EvidenceSubmission(BaseModel):
    evidence_type: str
    content: Dict[str, Any]
    privacy_level: str = "anonymized"
    target_instances: Optional[List[str]] = None

class TreatyProposal(BaseModel):
    title: str
    description: str
    articles: List[Dict[str, Any]]
    proposer_id: str
    ratification_threshold: float = Field(ge=0.5, le=1.0, default=0.67)

class DisputeInitiation(BaseModel):
    plaintiff_instance: str
    defendant_instance: str
    treaty_violated: str
    evidence_ids: List[str]

class ValidationVote(BaseModel):
    dispute_id: str
    judge_instance: str
    vote: str  # "plaintiff", "defendant", or justification text

# Federation Status Endpoints

@app.get("/federation/status")
def get_federation_status():
    """Get comprehensive federation status."""
    return {
        "federation_name": federation.federation_name,
        "status": "active",
        "sovereigns": federation.get_federation_status(),
        "onboarding": onboarding.get_onboarding_statistics(),
        "evidence_exchange": evidence_exchange.get_exchange_statistics(),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/federation/health")
def federation_health():
    """Basic federation health check."""
    return {
        "status": "healthy",
        "sovereign_count": len(federation.sovereigns),
        "federation_health": federation.get_federation_status()["federation_health"],
        "timestamp": datetime.now().isoformat()
    }

# Onboarding Endpoints

@app.post("/federation/onboard/initiate")
async def initiate_onboarding(request: OnboardingRequest, background_tasks: BackgroundTasks):
    """Initiate the federation onboarding process."""
    try:
        application_id = await onboarding.initiate_onboarding(
            applicant_instance_id=request.instance_id,
            applicant_public_key=request.public_key,
            federation_name=request.federation_name
        )
        return {
            "application_id": application_id,
            "status": "initiated",
            "next_step": "complete_identity_challenge",
            "message": "Onboarding initiated. Complete identity verification challenge."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/federation/onboard/challenges")
def get_pending_challenges():
    """Get all pending identity verification challenges."""
    return {"challenges": onboarding.get_pending_challenges()}

@app.post("/federation/onboard/challenge/{challenge_id}/respond")
async def respond_to_challenge(challenge_id: str, response: Dict[str, str]):
    """Respond to an identity verification challenge."""
    success = await onboarding.respond_to_challenge(challenge_id, response["response"])
    if success:
        return {"status": "verified", "message": "Identity verified. Proceed to judicial audit."}
    else:
        raise HTTPException(status_code=400, detail="Challenge verification failed")

@app.post("/federation/onboard/{application_id}/judicial-history")
async def submit_judicial_history(application_id: str, judicial_records: List[Dict[str, Any]]):
    """Submit judicial history for audit."""
    success = await onboarding.submit_judicial_history(application_id, judicial_records)
    if success:
        return {"status": "accepted", "message": "Judicial history accepted. Awaiting treaty ratification."}
    else:
        raise HTTPException(status_code=400, detail="Judicial history validation failed")

@app.get("/federation/onboard/{application_id}/status")
def get_onboarding_status(application_id: str):
    """Get onboarding application status."""
    status = onboarding.get_onboarding_status(application_id)
    if not status:
        raise HTTPException(status_code=404, detail="Application not found")
    return status

@app.get("/federation/onboard/{application_id}/treaty-check")
async def check_treaty_ratification(application_id: str):
    """Check if membership treaty has been ratified."""
    ratified, treaty_id = await onboarding.check_treaty_ratification(application_id)
    return {
        "ratified": ratified,
        "treaty_id": treaty_id,
        "status": "completed" if ratified else "pending"
    }

# Evidence Exchange Endpoints

@app.post("/federation/evidence/prepare")
async def prepare_evidence(request: EvidenceSubmission, background_tasks: BackgroundTasks):
    """Prepare an evidence package for exchange."""
    try:
        from phase3_evidence_exchange import EvidenceType, PrivacyLevel

        evidence_type = EvidenceType(request.evidence_type)
        privacy_level = PrivacyLevel(request.privacy_level)

        package_id = await evidence_exchange.prepare_evidence_package(
            evidence_type=evidence_type,
            content=request.content,
            privacy_level=privacy_level,
            target_instances=request.target_instances
        )

        return {
            "package_id": package_id,
            "status": "prepared",
            "message": "Evidence package prepared. Submit to federation for validation."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/federation/evidence/submit/{package_id}")
async def submit_evidence_package(package_id: str, background_tasks: BackgroundTasks):
    """Submit a prepared evidence package to the federation."""
    success = await evidence_exchange.submit_evidence_package(package_id)
    if success:
        return {"status": "submitted", "message": "Evidence submitted for federation validation"}
    else:
        raise HTTPException(status_code=404, detail="Package not found or submission failed")

@app.post("/federation/evidence/validate/{package_id}")
async def validate_evidence_package(package_id: str, validator_instance: str, approved: bool):
    """Submit validation vote for an evidence package."""
    success = await evidence_exchange.validate_evidence_package(package_id, validator_instance, approved)
    if success:
        return {"status": "vote_recorded", "message": f"Validation vote recorded: {'approved' if approved else 'rejected'}"}
    else:
        raise HTTPException(status_code=404, detail="Package not found or validation failed")

@app.get("/federation/evidence/query")
def query_evidence(evidence_type: Optional[str] = None, instance_filter: Optional[str] = None,
                  date_from: Optional[str] = None, privacy_level: Optional[str] = None):
    """Query evidence from the federation ledger."""
    from phase3_evidence_exchange import EvidenceType, PrivacyLevel

    evidence_type_enum = EvidenceType(evidence_type) if evidence_type else None
    privacy_level_enum = PrivacyLevel(privacy_level) if privacy_level else None
    date_from_dt = datetime.fromisoformat(date_from) if date_from else None

    # Note: In production, this would implement proper access controls
    results = evidence_exchange.query_evidence(
        evidence_type=evidence_type_enum,
        instance_filter=instance_filter,
        date_from=date_from_dt,
        privacy_level=privacy_level_enum
    )

    return {"evidence": results, "count": len(results)}

@app.post("/federation/evidence/aggregate/{evidence_type}")
async def create_evidence_aggregate(evidence_type: str, aggregation_hours: int = 24):
    """Create statistical aggregate of evidence."""
    from phase3_evidence_exchange import EvidenceType

    evidence_type_enum = EvidenceType(evidence_type)
    aggregate_id = await evidence_exchange.create_evidence_aggregate(
        evidence_type=evidence_type_enum,
        aggregation_hours=aggregation_hours
    )

    if aggregate_id:
        return {"aggregate_id": aggregate_id, "status": "created"}
    else:
        raise HTTPException(status_code=400, detail="Insufficient evidence for aggregation")

# Treaty Management Endpoints

@app.post("/federation/treaties/propose")
async def propose_treaty(request: TreatyProposal, background_tasks: BackgroundTasks):
    """Propose a new federation treaty."""
    try:
        treaty_id = await federation.propose_treaty(
            proposer_id=request.proposer_id,
            title=request.title,
            description=request.description,
            articles=request.articles,
            ratification_threshold=request.ratification_threshold
        )

        return {
            "treaty_id": treaty_id,
            "status": "proposed",
            "message": "Treaty proposed. Awaiting ratification by sovereign instances."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/federation/treaties/{treaty_id}/ratify")
async def ratify_treaty(treaty_id: str, sovereign_id: str):
    """Ratify a treaty as a sovereign instance."""
    success = await federation.ratify_treaty(treaty_id, sovereign_id)
    if success:
        return {"status": "ratified", "message": "Treaty ratified and effective"}
    else:
        return {"status": "pending", "message": "Ratification recorded. Awaiting additional signatures"}

@app.get("/federation/treaties")
def list_treaties(status: Optional[str] = None):
    """List federation treaties."""
    treaties = []
    for tid, treaty in federation.treaties.items():
        if not status or treaty.status.value == status:
            treaties.append({
                "treaty_id": tid,
                "title": treaty.title,
                "status": treaty.status.value,
                "signatories": treaty.signatories,
                "ratification_threshold": treaty.ratification_threshold,
                "created_at": treaty.created_at.isoformat(),
                "effective_at": treaty.effective_at.isoformat() if treaty.effective_at else None
            })

    return {"treaties": treaties, "count": len(treaties)}

# Dispute Resolution Endpoints

@app.post("/federation/disputes/initiate")
async def initiate_dispute(request: DisputeInitiation, background_tasks: BackgroundTasks):
    """Initiate a federation dispute."""
    try:
        dispute_id = await federation.initiate_dispute(
            plaintiff_instance=request.plaintiff_instance,
            defendant_instance=request.defendant_instance,
            treaty_violated=request.treaty_violated,
            evidence_ids=request.evidence_ids
        )

        return {
            "dispute_id": dispute_id,
            "status": "initiated",
            "message": "Dispute initiated. Assigned federation judges will review."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/federation/disputes/{dispute_id}/vote")
async def cast_dispute_vote(dispute_id: str, vote: ValidationVote):
    """Cast a vote in a federation dispute."""
    success = await federation.cast_dispute_vote(
        dispute_id=dispute_id,
        judge_instance=vote.judge_instance,
        vote=vote.vote
    )

    if success:
        return {"status": "vote_recorded", "message": "Vote recorded in dispute"}
    else:
        raise HTTPException(status_code=404, detail="Dispute not found or voting failed")

@app.get("/federation/disputes")
def list_disputes(status: Optional[str] = None):
    """List federation disputes."""
    disputes = []
    for did, dispute in federation.active_disputes.items():
        if not status or dispute.status == status:
            disputes.append({
                "dispute_id": did,
                "plaintiff": dispute.plaintiff_instance,
                "defendant": dispute.defendant_instance,
                "treaty_violated": dispute.treaty_violated,
                "status": dispute.status,
                "created_at": dispute.created_at.isoformat(),
                "resolution": dispute.resolution,
                "assigned_judges": dispute.assigned_judges
            })

    return {"disputes": disputes, "count": len(disputes)}

# Sovereignty Management Endpoints

@app.get("/federation/sovereigns")
def list_sovereigns():
    """List all sovereign instances in the federation."""
    sovereigns = []
    for sid, sovereign in federation.sovereigns.items():
        sovereigns.append({
            "instance_id": sid,
            "sovereignty_tier": sovereign.sovereignty_tier.value,
            "reputation_score": sovereign.reputation_score,
            "joined_at": sovereign.joined_at.isoformat(),
            "last_active": sovereign.last_active.isoformat(),
            "evidence_contributed": sovereign.evidence_contributed,
            "voting_weight": federation.calculate_voting_weight(sid)
        })

    return {"sovereigns": sovereigns, "count": len(sovereigns)}

@app.post("/federation/sovereigns/{instance_id}/exit")
async def initiate_sovereign_exit(instance_id: str, exit_reason: str = ""):
    """Initiate graceful exit from federation."""
    success = await onboarding.initiate_exit(instance_id, exit_reason)
    if success:
        return {"status": "exit_initiated", "message": "Exit initiated. 30-day transition period begins."}
    else:
        raise HTTPException(status_code=404, detail="Sovereign not found")

@app.get("/federation/sovereigns/{instance_id}/advancement")
def check_sovereign_advancement(instance_id: str):
    """Check if a sovereign is eligible for tier advancement."""
    new_tier = onboarding.check_tier_advancement(instance_id)
    if new_tier:
        return {
            "eligible": True,
            "new_tier": new_tier.value,
            "message": f"Eligible for advancement to {new_tier.value} tier"
        }
    else:
        return {
            "eligible": False,
            "message": "Not yet eligible for advancement"
        }

@app.post("/federation/sovereigns/{instance_id}/advance")
async def advance_sovereign_tier(instance_id: str):
    """Advance a sovereign to the next tier."""
    new_tier = onboarding.check_tier_advancement(instance_id)
    if not new_tier:
        raise HTTPException(status_code=400, detail="Not eligible for advancement")

    success = await onboarding.advance_tier(instance_id, new_tier)
    if success:
        return {"status": "advanced", "new_tier": new_tier.value}
    else:
        raise HTTPException(status_code=500, detail="Advancement failed")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8093)
