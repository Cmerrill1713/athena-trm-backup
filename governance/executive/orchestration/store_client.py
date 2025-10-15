#!/usr/bin/env python3
"""
MCP Store Client Server (FastMCP)
Provides tools to interact with the MCP Store
"""
import json
import os

import requests
from mcp.server.fastmcp import FastMCP, tool

mcp = FastMCP("store")

STORE_URL = os.getenv("MCPSTORE_URL", "http://athena-mcp-store:8411")

@tool()
def write_result(agent: str, service: str, status: str, summary: str = "", details_json: str = "{}"):
    """
    Write a validation result to MCP Store.
    
    Args:
        agent: Agent name
        service: Service name
        status: Status (PASS, FAIL, WARN)
        summary: Brief summary
        details_json: JSON string with details
    
    Returns:
        dict: Created record
    """
    try:
        payload = {
            "agent": agent,
            "service": service,
            "status": status,
            "summary": summary,
            "details": json.loads(details_json) if details_json else {}
        }

        response = requests.post(f"{STORE_URL}/v1/store/results", json=payload, timeout=10)
        response.raise_for_status()

        return {"status": "success", "result": response.json()}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@tool()
def query_results(service: str = "", status: str = "", limit: int = 20):
    """
    Query validation results from MCP Store.
    
    Args:
        service: Filter by service name (optional)
        status: Filter by status (optional)
        limit: Max results (default: 20)
    
    Returns:
        dict: Query results
    """
    try:
        params = {"limit": limit}
        if service:
            params["service"] = service
        if status:
            params["status"] = status

        response = requests.get(f"{STORE_URL}/v1/store/results", params=params, timeout=10)
        response.raise_for_status()

        return {"status": "success", "results": response.json()}
    except Exception as e:
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    mcp.run()

