#!/usr/bin/env python3
# FastAPI service for judicial endpoints
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import time
from typing import Dict, Any
from phase2_judicial_engine import adjudicate

app = FastAPI(title="AI Republic – Judicial API", version="2.0")

# Add CORS middleware for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Event(BaseModel):
    event_id: str
    instance_id: str
    actor_id: str
    article: str
    severity: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    classification: str
    details: Dict[str, Any] = {}
    timestamp: float = Field(default_factory=lambda: time.time())

@app.post("/v2/judicial/adjudicate")
def api_adjudicate(ev: Event):
    res = adjudicate(ev.dict())
    return {"verdict": res.verdict.value, "rationale": res.rationale, "actions": res.actions,
            "reputation_delta": res.reputation_delta, "review_required": res.review_required}

@app.get("/v2/health")
def health():
    return {"status":"ok","service":"judicial","ts":time.time()}

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8096))
    uvicorn.run(app, host="0.0.0.0", port=port)
