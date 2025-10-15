#!/usr/bin/env python3
"""
FastVLM Server - Apple's vision-language model exposed as FastAPI service
Integrated with Athena's observability and routing infrastructure
"""

import os
import sys
import time
import tempfile
import subprocess
import logging
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Prometheus metrics
try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
    METRICS_ENABLED = True
except ImportError:
    METRICS_ENABLED = False
    logging.warning("prometheus_client not installed - metrics disabled")

# ============================================================================
# Configuration
# ============================================================================

ENV = os.environ.get("ENV", "dev")
BUILD_SHA = os.environ.get("BUILD_SHA", "local")
MODEL_PATH = os.environ.get("FASTVLM_MODEL", "checkpoints/fastvlm_1.5b_stage3")
FASTVLM_ROOT = os.environ.get("FASTVLM_ROOT", "/Users/christianmerrill/Documents/GitHub/fastvlm/ml-fastvlm")
HOST = os.environ.get("FASTVLM_HOST", "127.0.0.1")
PORT = int(os.environ.get("FASTVLM_PORT", "8811"))

# ============================================================================
# Prometheus Metrics
# ============================================================================

if METRICS_ENABLED:
    VISION_REQUESTS = Counter(
        'fastvlm_requests_total',
        'Total FastVLM vision requests',
        ['env', 'build', 'status']
    )

    VISION_LATENCY = Histogram(
        'fastvlm_latency_ms',
        'FastVLM inference latency in milliseconds',
        ['env', 'build'],
        buckets=[50, 100, 200, 500, 1000, 2000, 5000, 10000]
    )

    VISION_IMAGE_SIZE = Histogram(
        'fastvlm_image_size_bytes',
        'Size of uploaded images in bytes',
        ['env', 'build'],
        buckets=[10_000, 50_000, 100_000, 500_000, 1_000_000, 5_000_000]
    )

    VISION_ACTIVE = Gauge(
        'fastvlm_active_requests',
        'Number of active FastVLM requests',
        ['env', 'build']
    )

    # Watchdog restart counter (read from file updated by watchdog)
    WATCHDOG_RESTARTS = Gauge(
        'fastvlm_watchdog_restarts_total',
        'Total number of watchdog restarts',
        ['env', 'build']
    )

    # Circuit breaker state
    WATCHDOG_CIRCUIT_BREAKER = Gauge(
        'fastvlm_watchdog_circuit_open',
        'Circuit breaker state (1=open, 0=closed)',
        ['env', 'build']
    )

    # Last restart timestamp
    WATCHDOG_LAST_RESTART = Gauge(
        'fastvlm_watchdog_last_restart_timestamp',
        'Unix timestamp of last successful restart',
        ['env', 'build']
    )

# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="FastVLM Server",
    description="Apple's FastVLM vision-language model API",
    version="1.0.0"
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("fastvlm")

# ============================================================================
# Request/Response Models
# ============================================================================

class VisionRequest(BaseModel):
    """Vision request with image path"""
    image_path: str = Field(..., description="Path to image file")
    prompt: str = Field(default="Describe the image.", description="Vision prompt")

class VisionResponse(BaseModel):
    """Vision response"""
    text: str = Field(..., description="Model output text")
    latency_ms: float = Field(..., description="Inference latency in milliseconds")
    model: str = Field(..., description="Model name")
    image_size: Optional[int] = Field(None, description="Image size in bytes")

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    model: str
    fastvlm_root: str
    model_exists: bool

# ============================================================================
# Helper Functions
# ============================================================================

def check_fastvlm_setup() -> tuple[bool, str]:
    """Check if FastVLM is properly set up"""
    fastvlm_path = Path(FASTVLM_ROOT)

    if not fastvlm_path.exists():
        return False, f"FastVLM root not found: {FASTVLM_ROOT}"

    predict_script = fastvlm_path / "predict.py"
    if not predict_script.exists():
        return False, f"predict.py not found in {FASTVLM_ROOT}"

    model_path = fastvlm_path / MODEL_PATH
    if not model_path.exists():
        return False, f"Model not found: {model_path}"

    return True, "OK"

def run_inference(image_path: str, prompt: str) -> tuple[str, float]:
    """
    Run FastVLM inference on an image

    Returns:
        (output_text, latency_ms)
    """
    start_time = time.time()

    # Build command
    cmd = [
        sys.executable,
        "predict.py",
        "--model-path", MODEL_PATH,
        "--image-file", image_path,
        "--prompt", prompt
    ]

    logger.info(f"Running inference: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            cwd=FASTVLM_ROOT,
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )

        latency_ms = (time.time() - start_time) * 1000

        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip()
            raise RuntimeError(f"FastVLM inference failed: {error_msg}")

        output = result.stdout.strip()
        logger.info(f"Inference complete in {latency_ms:.0f}ms")

        return output, latency_ms

    except subprocess.TimeoutExpired:
        latency_ms = (time.time() - start_time) * 1000
        raise RuntimeError(f"FastVLM inference timed out after {latency_ms:.0f}ms")
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        logger.error(f"Inference error after {latency_ms:.0f}ms: {e}")
        raise

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    is_ok, message = check_fastvlm_setup()
    model_path = Path(FASTVLM_ROOT) / MODEL_PATH

    return HealthResponse(
        status="healthy" if is_ok else f"unhealthy: {message}",
        model=MODEL_PATH,
        fastvlm_root=FASTVLM_ROOT,
        model_exists=model_path.exists()
    )

@app.post("/v1/vision", response_model=VisionResponse)
async def vision_inference(
    image: UploadFile = File(...),
    prompt: str = Form(default="Describe the image.")
):
    """
    Vision inference endpoint

    Accepts an image file and prompt, returns model output
    """
    if METRICS_ENABLED:
        VISION_ACTIVE.labels(env=ENV, build=BUILD_SHA).inc()

    temp_path = None
    start_time = time.time()

    try:
        # Validate FastVLM setup
        is_ok, error_msg = check_fastvlm_setup()
        if not is_ok:
            if METRICS_ENABLED:
                VISION_REQUESTS.labels(env=ENV, build=BUILD_SHA, status="setup_error").inc()
            raise HTTPException(status_code=503, detail=error_msg)

        # Save uploaded image to temp file
        suffix = Path(image.filename or "image.png").suffix or ".png"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            content = await image.read()
            f.write(content)
            temp_path = f.name
            image_size = len(content)

        if METRICS_ENABLED:
            VISION_IMAGE_SIZE.labels(env=ENV, build=BUILD_SHA).observe(image_size)

        logger.info(f"Processing image: {image.filename} ({image_size} bytes)")

        # Run inference
        output_text, latency_ms = run_inference(temp_path, prompt)

        # Record metrics
        if METRICS_ENABLED:
            VISION_REQUESTS.labels(env=ENV, build=BUILD_SHA, status="success").inc()
            VISION_LATENCY.labels(env=ENV, build=BUILD_SHA).observe(latency_ms)

        return VisionResponse(
            text=output_text,
            latency_ms=latency_ms,
            model=MODEL_PATH,
            image_size=image_size
        )

    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        logger.error(f"Vision inference failed: {e}")

        if METRICS_ENABLED:
            VISION_REQUESTS.labels(env=ENV, build=BUILD_SHA, status="error").inc()

        raise HTTPException(
            status_code=500,
            detail=f"Inference failed: {str(e)}"
        )

    finally:
        # Cleanup
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file: {e}")

        if METRICS_ENABLED:
            VISION_ACTIVE.labels(env=ENV, build=BUILD_SHA).dec()

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    if not METRICS_ENABLED:
        return JSONResponse(
            status_code=503,
            content={"error": "Metrics not available - prometheus_client not installed"}
        )

    # Update watchdog metrics from files
    try:
        # Restart counter (persists across reboots)
        restart_count_file = "/tmp/fastvlm_watchdog_restarts.count"
        if os.path.exists(restart_count_file):
            with open(restart_count_file, 'r') as f:
                count = int(f.read().strip())
                WATCHDOG_RESTARTS.labels(env=ENV, build=BUILD_SHA).set(count)

        # Circuit breaker state
        circuit_file = "/tmp/fastvlm_circuit_breaker"
        if os.path.exists(circuit_file):
            with open(circuit_file, 'r') as f:
                state = int(f.read().strip())
                WATCHDOG_CIRCUIT_BREAKER.labels(env=ENV, build=BUILD_SHA).set(state)
        else:
            WATCHDOG_CIRCUIT_BREAKER.labels(env=ENV, build=BUILD_SHA).set(0)

        # Last restart timestamp
        last_restart_file = "/tmp/fastvlm_last_restart_ts"
        if os.path.exists(last_restart_file):
            with open(last_restart_file, 'r') as f:
                ts = int(f.read().strip())
                WATCHDOG_LAST_RESTART.labels(env=ENV, build=BUILD_SHA).set(ts)
    except Exception as e:
        logger.warning(f"Failed to read watchdog metrics: {e}")

    return generate_latest(REGISTRY)

@app.get("/")
async def root():
    """Root endpoint with service info"""
    return {
        "service": "FastVLM Server",
        "version": "1.0.0",
        "model": MODEL_PATH,
        "endpoints": {
            "health": "/health",
            "vision": "/v1/vision",
            "metrics": "/metrics"
        }
    }

# ============================================================================
# Main
# ============================================================================

def warmup_model():
    """
    Warmup model with a tiny inference to avoid cold-start latency
    First inference can be slow; this primes the model
    """
    try:
        logger.info("Warming up model with test inference...")

        # Create a tiny test image (1x1 red pixel)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            # Simple 1x1 pixel image data (PNG format)
            # Minimal valid PNG: signature + IHDR + IDAT + IEND
            import base64
            tiny_png = base64.b64decode(
                b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=='
            )
            f.write(tiny_png)
            warmup_image = f.name

        start = time.time()
        _, latency = run_inference(warmup_image, "warmup")
        total_time = time.time() - start

        os.unlink(warmup_image)

        logger.info(f"✅ Model warmed up: {latency:.0f}ms inference, {total_time:.1f}s total")
        return True

    except Exception as e:
        logger.warning(f"⚠️  Warmup failed (non-fatal): {e}")
        return False


def main():
    """Start the FastVLM server"""
    # Validate setup before starting
    is_ok, error_msg = check_fastvlm_setup()
    if not is_ok:
        logger.error(f"FastVLM setup validation failed: {error_msg}")
        logger.error("Please set FASTVLM_ROOT environment variable to ml-fastvlm directory")
        sys.exit(1)

    logger.info(f"Starting FastVLM Server on {HOST}:{PORT}")
    logger.info(f"Model: {MODEL_PATH}")
    logger.info(f"FastVLM root: {FASTVLM_ROOT}")
    logger.info(f"Environment: {ENV}")
    logger.info(f"Build: {BUILD_SHA}")
    logger.info(f"Metrics: {'enabled' if METRICS_ENABLED else 'disabled'}")

    # Warmup model before starting server (avoids cold-start on first request)
    warmup_model()

    logger.info(f"🚀 FastVLM Server ready on http://{HOST}:{PORT}")

    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="info"
    )

if __name__ == "__main__":
    main()
