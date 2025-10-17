# Athena Governance Executive API
# Port 9110 | Verdict system + Policy control

FROM python:3.11-slim

WORKDIR /app

# Install curl for healthchecks
RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    fastapi>=0.104.0 \
    uvicorn[standard]>=0.24.0 \
    pydantic>=2.4.0 \
    prometheus-client>=0.19.0 \
    requests>=2.31.0

# Copy application
COPY . /app/governance/executive/

# Expose API port
EXPOSE 9110

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:9110/health || exit 1

# Run API
CMD ["python", "/app/governance/executive/api.py"]

