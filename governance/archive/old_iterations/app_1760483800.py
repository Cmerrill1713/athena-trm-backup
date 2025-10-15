from fastapi import FastAPI
try:
    from prometheus_client import Gauge, generate_latest
    from starlette.responses import Response
except ImportError:
    # Fallback if prometheus not available
    Gauge = lambda *args: type('Mock', (), {'set': lambda self, x: None})()
    generate_latest = lambda: "mock_metrics"
    from fastapi.responses import PlainTextResponse as Response

app = FastAPI()
_g_ready = Gauge("kokoro_ready", "1 when ready"); _g_ready.set(1)

@app.get("/health")
def health(): return {"ok": True}

@app.get("/ready")
def ready(): return {"ok": True}

@app.get("/metrics")
def metrics(): return Response(generate_latest(), media_type="text/plain")
