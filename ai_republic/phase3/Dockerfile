FROM python:3.11-slim

WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    fastapi==0.109.0 \
    uvicorn[standard]==0.27.0 \
    pyyaml==6.0.1 \
    pydantic==2.5.0 \
    cryptography==41.0.7

# Copy all phase3 files
COPY . .

# Create state directories
RUN mkdir -p /app/federation_state /app/logs

EXPOSE 8097

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8097/federation/health || exit 1

CMD ["python", "-m", "uvicorn", "phase3_federation_api:app", "--host", "0.0.0.0", "--port", "8097"]
