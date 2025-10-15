FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY agi_core/requirements.txt /app/agi_core/requirements.txt
COPY common/requirements.txt /app/common/requirements.txt 2>/dev/null || echo "fastapi>=0.104.0\nuvicorn>=0.24.0" > /app/common/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/agi_core/requirements.txt
RUN pip install --no-cache-dir -r /app/common/requirements.txt

# Copy application code
COPY common/ /app/common/
COPY agi_core/ /app/agi_core/

# Create state directories
RUN mkdir -p /app/state/agi /app/experts

# Expose port
EXPOSE 8100

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8100/health || exit 1

# Run the service
CMD ["python", "-m", "agi_core.agi_service"]

