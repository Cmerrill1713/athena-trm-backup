#!/bin/bash

echo "🔧 FIXING FINAL 4 UNHEALTHY CONTAINERS"
echo "======================================="
echo ""

echo "1️⃣ Adding curl to fastvlm Dockerfile"
echo "--------------------------------------"
cat > services/fastvlm/Dockerfile << 'DOCKERFILE'
FROM python:3.11-slim

WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

EXPOSE 8088

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8088/health || exit 1

CMD ["python", "server.py"]
DOCKERFILE
echo "✅ FastVLM Dockerfile updated"

echo ""
echo "2️⃣ Adding curl to kokoro Dockerfile"
echo "-------------------------------------"
cat > services/kokoro/Dockerfile << 'DOCKERFILE'
FROM python:3.11-slim

WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service
COPY server.py .

# Expose port
EXPOSE 8091

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8091/health || exit 1

# Run server
CMD ["python", "server.py"]
DOCKERFILE
echo "✅ Kokoro Dockerfile updated"

echo ""
echo "3️⃣ Adding procps to canary Dockerfile (for pgrep)"
echo "---------------------------------------------------"
cat > governance/executive/Dockerfile.canary << 'DOCKERFILE'
# Athena Canary Controller
# Monitors router metrics and triggers auto-rollback on breach

FROM python:3.11-slim

# Install curl and procps for health checks
RUN apt-get update && apt-get install -y curl procps && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    requests>=2.31.0 \
    prometheus-client>=0.19.0

# Copy application
COPY . /app/governance/executive/

# No port exposure (background service)

# Run canary controller
CMD ["python", "/app/governance/executive/canary_controller.py"]
DOCKERFILE
echo "✅ Canary Dockerfile updated"

echo ""
echo "4️⃣ Fixing OTEL Collector health check (use curl instead of wget)"
echo "------------------------------------------------------------------"
# OTEL collector is a pre-built image, we need to change health check in docker-compose.yml
echo "Will update docker-compose.yml to use curl instead of wget..."

echo ""
echo "======================================="
echo "✅ All Dockerfiles updated"
echo ""
echo "Next: Rebuild and restart services"

