# Production Bridge Adapter - Tier 4
FROM python:3.11-slim

LABEL maintainer="Stack Orchestration Team"
LABEL service="bridge"
LABEL tier="adapter"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user (security best practice)
RUN useradd -m -u 1000 bridge && \
    mkdir -p /app && \
    chown -R bridge:bridge /app

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir \
        prometheus-client \
        prometheus-fastapi-instrumentator

# Copy application code
COPY --chown=bridge:bridge . .

# Switch to non-root user
USER bridge

# Expose port
EXPOSE 8014

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8014/health || exit 1

# Graceful shutdown timeout
STOPSIGNAL SIGTERM
ENV GRACEFUL_TIMEOUT=10

# Run application
CMD ["python3", "-m", "uvicorn", "adapter:app", "--host", "0.0.0.0", "--port", "8014", "--workers", "2"]
