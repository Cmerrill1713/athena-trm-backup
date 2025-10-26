FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (curl for health checks)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    asyncpg==0.29.0 \
    httpx==0.25.2 \
    fastapi==0.104.1 \
    uvicorn==0.24.0

# Copy learning agents
COPY feedback_analyzer.py .
COPY router_learning_agent.py .
COPY central_learning_coordinator.py .
COPY api.py .

EXPOSE 8098

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8098/health')" || exit 1

# Run API
CMD ["python", "-u", "api.py"]
