import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import psycopg
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

import redis
import weaviate

PG_URL = os.getenv("MCPSTORE_PG", "postgresql://postgres:postgres@localhost:5432/universal_ai_tools")
WV_HOST = os.getenv("MCPSTORE_WEAVIATE_HOST", "http://127.0.0.1:8080")
REDIS_URL = os.getenv("MCPSTORE_REDIS", "redis://127.0.0.1:6379")
USE_WV = os.getenv("MCPSTORE_ENABLE_WEAVIATE", "true").lower() == "true"
USE_REDIS = os.getenv("MCPSTORE_ENABLE_REDIS", "true").lower() == "true"

pg = psycopg.connect(PG_URL, autocommit=True)
wclient = weaviate.Client(WV_HOST) if USE_WV else None
rds = redis.from_url(REDIS_URL) if USE_REDIS else None

# Ensure table exists
with pg.cursor() as cur:
    cur.execute("""
    create table if not exists validation_results (
      id uuid primary key default gen_random_uuid(),
      correlation_id text unique,
      agent text not null,
      service text not null,
      status text not null check (status in ('PASS','FAIL','WARN')),
      summary text,
      details jsonb,
      commit_sha text,
      created_at timestamptz not null default now()
    );
    """)
    # Extensions may require superuser; skip if not available
    try: cur.execute("create extension if not exists pgcrypto;")
    except Exception: pass

class ValidationInput(BaseModel):
    agent: str
    service: str
    status: str
    summary: Optional[str] = ""
    details: Dict[str, Any] = {}
    commit: Optional[str] = None
    correlation_id: Optional[str] = None
    ts: Optional[str] = None
    embed_text: Optional[str] = None

class ValidationRecord(ValidationInput):
    id: str
    created_at: str

app = FastAPI(title="MCP Store", version="0.1.0")

@app.get("/health")
def health():
    return {"ok": True, "service": "mcp-store", "weaviate": USE_WV, "redis": USE_REDIS}

@app.post("/v1/store/results", response_model=ValidationRecord)
def write_result(data: ValidationInput, x_mcp_tenant: Optional[str] = Header(default=None)):
    # 1) idempotency via redis
    if rds and data.correlation_id:
        if not rds.setnx(f"mcpstore:{data.correlation_id}", "1"):
            rec = get_by_corr(data.correlation_id)
            if rec: return rec
        rds.expire(f"mcpstore:{data.correlation_id}", 600)

    # 2) write to Postgres
    with pg.cursor() as cur:
        cur.execute("""
          insert into validation_results(correlation_id,agent,service,status,summary,details,commit_sha)
          values (%s,%s,%s,%s,%s,%s,%s)
          returning id, created_at
        """, (data.correlation_id, data.agent, data.service, data.status, data.summary, json.dumps(data.details), data.commit))
        id_, created_at = cur.fetchone()

    # 3) fire-and-forget to Weaviate
    if wclient:
        text = data.embed_text or f"{data.summary}\n{json.dumps(data.details)[:5000]}"
        obj = {
          "agent": data.agent, "service": data.service, "status": data.status,
          "summary": data.summary or "", "details": json.dumps(data.details)[:5000],
          "commit": data.commit or "", "ts": (data.ts or datetime.now(timezone.utc).isoformat())
        }
        try:
            wclient.data_object.create(obj, class_name="ValidationResult")  # assumes class exists
        except Exception:
            # best-effort; don't fail
            pass

    return ValidationRecord(id=str(id_), created_at=created_at.isoformat(), **data.dict())

def get_by_corr(corr_id: str) -> Optional[ValidationRecord]:
    with pg.cursor() as cur:
        cur.execute("select id, agent, service, status, summary, details, commit_sha, created_at, correlation_id from validation_results where correlation_id=%s", (corr_id,))
        row = cur.fetchone()
        if not row: return None
        id_, agent, service, status, summary, details, commit_sha, created_at, correlation_id = row
        return ValidationRecord(
            id=str(id_), agent=agent, service=service, status=status,
            summary=summary, details=details, commit=commit_sha,
            created_at=created_at.isoformat(), correlation_id=correlation_id
        )

@app.get("/v1/store/results/{rec_id}", response_model=ValidationRecord)
def get_result(rec_id: str):
    with pg.cursor() as cur:
        cur.execute("select id, agent, service, status, summary, details, commit_sha, created_at, correlation_id from validation_results where id=%s::uuid", (rec_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(404, "not found")
        id_, agent, service, status, summary, details, commit_sha, created_at, correlation_id = row
        return ValidationRecord(
            id=str(id_), agent=agent, service=service, status=status,
            summary=summary, details=details, commit=commit_sha,
            created_at=created_at.isoformat(), correlation_id=correlation_id
        )

@app.get("/v1/store/results")
def list_results(agent: Optional[str] = None, service: Optional[str] = None, status: Optional[str] = None, limit: int = 100):
    """List validation results with optional filters"""
    query = "select id, agent, service, status, summary, details, commit_sha, created_at, correlation_id from validation_results where 1=1"
    params = []

    if agent:
        query += " and agent = %s"
        params.append(agent)
    if service:
        query += " and service = %s"
        params.append(service)
    if status:
        query += " and status = %s"
        params.append(status)

    query += " order by created_at desc limit %s"
    params.append(limit)

    with pg.cursor() as cur:
        cur.execute(query, params)
        rows = cur.fetchall()
        results = []
        for row in rows:
            id_, agent, service, status, summary, details, commit_sha, created_at, correlation_id = row
            results.append(ValidationRecord(
                id=str(id_), agent=agent, service=service, status=status,
                summary=summary, details=details, commit=commit_sha,
                created_at=created_at.isoformat(), correlation_id=correlation_id
            ))
        return {"results": results, "count": len(results)}

