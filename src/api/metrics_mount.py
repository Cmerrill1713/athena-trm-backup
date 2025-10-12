# src/api/metrics_mount.py
from prometheus_client import make_asgi_app

def mount_metrics(app):
    """Mount Prometheus metrics endpoint at /metrics"""
    try:
        # Optional: Add PrometheusMiddleware if starlette_exporter is installed
        from starlette_exporter import PrometheusMiddleware
        app.add_middleware(PrometheusMiddleware)
    except ImportError:
        pass  # Continue without middleware if not installed
    
    app.mount("/metrics", make_asgi_app())
    return app

