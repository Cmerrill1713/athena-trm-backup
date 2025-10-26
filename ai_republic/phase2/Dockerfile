FROM python:3.11-slim

WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    fastapi==0.109.0 \
    uvicorn[standard]==0.27.0 \
    pyyaml==6.0.1 \
    pydantic==2.5.0

# Copy all phase2 files
COPY . .

# Create state directories
RUN mkdir -p /app/phase2_state /app/logs

EXPOSE 8096

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8096/v2/health || exit 1

CMD ["python", "-m", "uvicorn", "phase2_api:app", "--host", "0.0.0.0", "--port", "8096"]
