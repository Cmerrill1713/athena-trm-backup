#!/usr/bin/env python3
"""
MCP Server wrapper for MCP Store
Exposes validation storage as MCP tools
"""
import json
import os

import requests
from mcp.server.fastmcp import FastMCP, tool

STORE = os.getenv("MCPSTORE_URL", "http://athena-mcp-store:8411")

mcp = FastMCP("mcp-store")

@tool()
def store_write(agent: str, service: str, status: str, summary: str="", details_json: str="{}", commit: str="", correlation_id: str=""):
    """
    Write a validation result to the MCP Store.
    
    Args:
        agent: Name of the agent performing validation (e.g., 'validator', 'bridge-test')
        service: Name of the service being validated (e.g., 'bridge', 'athena', 'uat')
        status: Validation status ('PASS', 'FAIL', 'WARN')
        summary: Brief summary of the validation result
        details_json: JSON string containing detailed validation metrics and results
        commit: Git commit SHA or version identifier
        correlation_id: Optional unique identifier for idempotent writes
    
    Returns:
        dict: Created validation record with id, created_at timestamp, and all input fields
    """
    payload = {
        "agent": agent,
        "service": service,
        "status": status,
        "summary": summary,
        "details": json.loads(details_json) if details_json else {},
        "commit": commit,
        "correlation_id": correlation_id if correlation_id else None
    }
    r = requests.post(f"{STORE}/v1/store/results", json=payload, timeout=10)
    r.raise_for_status()
    return r.json()

@tool()
def store_get(id: str):
    """
    Fetch a validation record by its unique ID.
    
    Args:
        id: UUID of the validation record
    
    Returns:
        dict: Validation record with all fields
    """
    r = requests.get(f"{STORE}/v1/store/results/{id}", timeout=10)
    r.raise_for_status()
    return r.json()

@tool()
def store_list(agent: str = "", service: str = "", status: str = "", limit: int = 100):
    """
    List validation results with optional filters.
    
    Args:
        agent: Filter by agent name (optional)
        service: Filter by service name (optional)
        status: Filter by status ('PASS', 'FAIL', 'WARN') (optional)
        limit: Maximum number of results to return (default: 100)
    
    Returns:
        dict: List of validation records matching the filters
    """
    params = {}
    if agent:
        params["agent"] = agent
    if service:
        params["service"] = service
    if status:
        params["status"] = status
    params["limit"] = limit

    r = requests.get(f"{STORE}/v1/store/results", params=params, timeout=10)
    r.raise_for_status()
    return r.json()

@tool()
def store_health():
    """
    Check the health status of the MCP Store service.
    
    Returns:
        dict: Health status including service availability and enabled backends
    """
    r = requests.get(f"{STORE}/health", timeout=5)
    r.raise_for_status()
    return r.json()

if __name__ == "__main__":
    mcp.run()

