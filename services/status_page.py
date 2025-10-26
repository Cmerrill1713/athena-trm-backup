#!/usr/bin/env python3
"""
Unified Status Page - Complete Stack Health
Aggregates status from RAG, Model Pool, Embedding Service, Weaviate
"""

import asyncio
import logging
from typing import Dict, Any

import httpx
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Stack Status Page", version="1.0.0")

async def check_service(url: str, name: str) -> Dict[str, Any]:
    """Check if a service is healthy"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            return {
                "name": name,
                "status": "up" if response.status_code == 200 else "degraded",
                "code": response.status_code,
                "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else None
            }
    except Exception as e:
        return {
            "name": name,
            "status": "down",
            "error": str(e)
        }

@app.get("/", response_class=HTMLResponse)
async def status_page():
    """Unified status page with real-time data"""
    
    # Check all services
    checks = await asyncio.gather(
        check_service("http://localhost:8085/health", "Model Pool"),
        check_service("http://localhost:8085/status", "Model Pool Status"),
        check_service("http://localhost:8086/health", "Embedding Service"),
        check_service("http://localhost:8087/health", "Dynamic RAG"),
        check_service("http://localhost:8090/v1/.well-known/ready", "Weaviate"),
        check_service("http://localhost:11434/api/tags", "Ollama"),
        return_exceptions=True
    )
    
    # Parse results
    services = {}
    for check in checks:
        if isinstance(check, Exception):
            continue
        services[check["name"]] = check
    
    # Extract key metrics
    model_pool_status = services.get("Model Pool Status", {}).get("data", {})
    active_model = model_pool_status.get("active_model")
    vram_mb = model_pool_status.get("vram_mb", 0)
    queue_depth = model_pool_status.get("queue_depth", 0)
    hotswaps_5m = model_pool_status.get("hotswaps_5m", 0)
    loaded_models = model_pool_status.get("loaded", [])
    
    # Build HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Athena Intelligent Stack - Status</title>
        <meta http-equiv="refresh" content="10">
        <style>
            body {{
                font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
                background: #0a0a0a;
                color: #00ff00;
                padding: 20px;
                margin: 0;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
            }}
            h1 {{
                border-bottom: 2px solid #00ff00;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }}
            .status-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }}
            .service-card {{
                background: #1a1a1a;
                border: 1px solid #333;
                border-radius: 8px;
                padding: 15px;
            }}
            .service-card h3 {{
                margin-top: 0;
                color: #00ffff;
            }}
            .status-up {{
                color: #00ff00;
            }}
            .status-down {{
                color: #ff0000;
            }}
            .status-degraded {{
                color: #ffaa00;
            }}
            .metric {{
                margin: 5px 0;
                padding: 5px;
                background: #0f0f0f;
                border-radius: 4px;
            }}
            .metric-label {{
                color: #888;
                font-size: 0.9em;
            }}
            .metric-value {{
                color: #00ff00;
                font-weight: bold;
            }}
            .footer {{
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #333;
                color: #666;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>✨ Athena Intelligent Stack - Live Status</h1>
            
            <div class="status-grid">
                <!-- Services -->
                {"".join([
                    f'''
                    <div class="service-card">
                        <h3>{name}</h3>
                        <div class="status-{svc.get("status", "down")}"">
                            ● {svc.get("status", "unknown").upper()}
                        </div>
                        {f'<div style="color: #ff6666; margin-top: 5px;">{svc.get("error", "")}</div>' if svc.get("error") else ""}
                    </div>
                    '''
                    for name, svc in services.items()
                    if "Status" not in name
                ])}
            </div>
            
            <h2>🧠 Model Pool Manager</h2>
            <div class="metric">
                <span class="metric-label">Active Model:</span>
                <span class="metric-value">{active_model or "None"}</span>
            </div>
            <div class="metric">
                <span class="metric-label">VRAM Usage:</span>
                <span class="metric-value">{vram_mb} MB</span>
            </div>
            <div class="metric">
                <span class="metric-label">Queue Depth:</span>
                <span class="metric-value">{queue_depth}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Hot-Swaps (5min):</span>
                <span class="metric-value">{hotswaps_5m}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Loaded Models:</span>
                <span class="metric-value">{", ".join(loaded_models) if loaded_models else "None"}</span>
            </div>
            
            <h2>📚 Model Details</h2>
            <div class="status-grid">
                {
                    "".join([
                        f'''
                        <div class="service-card">
                            <h3>{model_id}</h3>
                            <div class="metric">
                                <span class="metric-label">State:</span>
                                <span class="metric-value">{details.get("warm_state", "unknown")}</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">Idle:</span>
                                <span class="metric-value">{details.get("idle_seconds", 0):.1f}s</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">Inferences:</span>
                                <span class="metric-value">{details.get("infer_count", 0)}</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">VRAM:</span>
                                <span class="metric-value">{details.get("vram_mb", 0)} MB</span>
                            </div>
                        </div>
                        '''
                        for model_id, details in model_pool_status.get("models", {}).items()
                    ])
                }
            </div>
            
            <h2>⚡ Quick Actions</h2>
            <div style="margin: 20px 0;">
                <a href="http://localhost:8085/status" target="_blank" style="color: #00ffff; margin-right: 20px;">Model Pool Status</a>
                <a href="http://localhost:9092/metrics" target="_blank" style="color: #00ffff; margin-right: 20px;">Model Pool Metrics</a>
                <a href="http://localhost:9090/graph" target="_blank" style="color: #00ffff; margin-right: 20px;">Prometheus</a>
                <a href="http://localhost:3000" target="_blank" style="color: #00ffff;">Grafana</a>
            </div>
            
            <div class="footer">
                Last updated: {asyncio.get_event_loop().time()} | Auto-refresh every 10s
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

@app.get("/api/status")
async def api_status():
    """JSON status endpoint"""
    checks = await asyncio.gather(
        check_service("http://localhost:8085/health", "model-pool"),
        check_service("http://localhost:8085/status", "model-pool-detail"),
        check_service("http://localhost:8086/health", "embedding-service"),
        check_service("http://localhost:8087/health", "dynamic-rag"),
        check_service("http://localhost:8090/v1/.well-known/ready", "weaviate"),
        return_exceptions=True
    )
    
    services = {}
    for check in checks:
        if not isinstance(check, Exception):
            services[check["name"]] = {
                "status": check["status"],
                "data": check.get("data")
            }
    
    return {
        "stack": "intelligent",
        "version": "1.0.0",
        "services": services,
        "overall_health": "up" if all(s.get("status") == "up" for s in services.values()) else "degraded"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8084"))
    logger.info(f"Starting Status Page on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

