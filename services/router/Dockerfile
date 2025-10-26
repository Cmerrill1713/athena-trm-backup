# Athena Router - Local-first model routing
# Port 9113 | MLX → Ollama → MCP-Browser → Cloud (governed)

FROM python:3.11-slim

WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . /app/

# Expose router port
EXPOSE 9113

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:9113/health || exit 1

# Run router
CMD ["python", "app.py"]

