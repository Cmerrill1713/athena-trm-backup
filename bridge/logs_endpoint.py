"""
Bridge Logs Endpoint - Proxy for service logs
Allows frontend to fetch logs without direct file access
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import os
import subprocess

router = APIRouter(prefix="/ops", tags=["operations"])

# Map service names to log file paths
SERVICE_LOGS = {
    "athena": "logs/athena_8090.log",
    "uat": "logs/uat_8181.log",
    "bridge": "logs/bridge_8014.log",
    "kokoro": "logs/kokoro_8020.log",
    "rag": "logs/rag_8015.log",
    "fastvlm": "logs/fastvlm_8811.log",
    "vision_rag": "logs/vision_rag_8016.log",
}

def redact_secrets(text: str) -> str:
    """
    Redact secrets from log lines
    Removes: Bearer tokens, API keys, passwords, emails
    """
    import re
    
    # Redact Bearer tokens
    text = re.sub(r'Bearer\s+[A-Za-z0-9_\-\.]+', 'Bearer ***REDACTED***', text)
    
    # Redact Authorization headers
    text = re.sub(r'Authorization:\s*[^\s\n]+', 'Authorization: ***REDACTED***', text, flags=re.IGNORECASE)
    
    # Redact API keys
    text = re.sub(r'[Aa][Pp][Ii]_?[Kk][Ee][Yy][\s=:]+[A-Za-z0-9_\-]+', 'api_key=***REDACTED***', text)
    
    # Redact tokens
    text = re.sub(r'[Tt][Oo][Kk][Ee][Nn][\s=:]+[A-Za-z0-9_\-]+', 'token=***REDACTED***', text)
    
    # Redact passwords
    text = re.sub(r'[Pp][Aa][Ss][Ss][Ww][Oo][Rr][Dd][\s=:]+[^\s\n]+', 'password=***REDACTED***', text)
    
    # Redact emails (PII)
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '***EMAIL_REDACTED***', text)
    
    # Redact common secret patterns
    text = re.sub(r'sk-[A-Za-z0-9]{32,}', 'sk-***REDACTED***', text)  # OpenAI-style keys
    text = re.sub(r'xox[baprs]-[A-Za-z0-9\-]+', 'xox***REDACTED***', text)  # Slack tokens
    
    return text


@router.get("/logs")
async def get_service_logs(
    service: str = Query(..., description="Service name (athena, uat, bridge, etc.)"),
    tail: int = Query(100, ge=10, le=2000, description="Number of lines to return (max 2000)"),
    since: Optional[str] = Query(None, description="ISO timestamp to filter from"),
):
    """
    Get service logs via tail (with secret redaction)
    
    Examples:
        /ops/logs?service=athena&tail=100
        /ops/logs?service=athena&tail=500&since=2025-10-12T20:00:00
    
    Security:
    - Only allows whitelisted services
    - Max 2000 lines enforced
    - Secrets automatically redacted
    - 5 second timeout
    """
    service_key = service.lower().replace(" ", "_")
    
    # Validate service is in allowlist
    if service_key not in SERVICE_LOGS:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown service: {service}. Available: {list(SERVICE_LOGS.keys())}"
        )
    
    # Enforce max tail (defense in depth)
    tail = min(tail, 2000)
    
    log_path = SERVICE_LOGS[service_key]
    
    # Support absolute or relative paths
    if not log_path.startswith("/"):
        # Relative to repo root
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_path = os.path.join(repo_root, log_path)
    
    if not os.path.exists(log_path):
        raise HTTPException(
            status_code=404,
            detail=f"Log file not found: {log_path}"
        )
    
    try:
        # Use tail command for efficiency (doesn't load entire file)
        result = subprocess.run(
            ["tail", "-n", str(tail), log_path],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to read logs: {result.stderr}"
            )
        
        logs = result.stdout
        
        # Optional: Filter by timestamp if 'since' provided
        if since:
            # Simple line filtering (assumes ISO timestamps in logs)
            lines = logs.split("\n")
            filtered = [line for line in lines if since in line or not any(char.isdigit() for char in line[:20])]
            logs = "\n".join(filtered)
        
        # SECURITY: Redact secrets before returning
        logs = redact_secrets(logs)
        
        return {
            "ok": True,
            "service": service,
            "lines": len(logs.split("\n")),
            "bytes": len(logs),
            "path": log_path,
            "content": logs,
            "redacted": True  # Indicate secrets were scrubbed
        }
    
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Log read timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading logs: {str(e)}")


@router.get("/logs/list")
async def list_available_logs():
    """
    List all available service logs
    """
    available = []
    
    for service_name, log_path in SERVICE_LOGS.items():
        # Resolve relative paths
        if not log_path.startswith("/"):
            repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            full_path = os.path.join(repo_root, log_path)
        else:
            full_path = log_path
        
        exists = os.path.exists(full_path)
        size = os.path.getsize(full_path) if exists else 0
        
        available.append({
            "service": service_name,
            "path": log_path,
            "exists": exists,
            "size_bytes": size,
            "size_mb": round(size / 1024 / 1024, 2)
        })
    
    return {
        "ok": True,
        "services": available,
        "total": len(available)
    }

