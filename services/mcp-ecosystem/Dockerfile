# MCP Ecosystem - Python tool backend
# Port 8412

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    fastapi>=0.104.0 \
    uvicorn[standard]>=0.24.0 \
    pydantic>=2.4.0

# Copy application
COPY app.py /app/

# Expose port
EXPOSE 8412

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8412/health || exit 1

# Run server
CMD ["python", "app.py"]

