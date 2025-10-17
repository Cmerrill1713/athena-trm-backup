# Athena Evolutionary API
# Port 8014

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    fastapi>=0.104.0 \
    uvicorn[standard]>=0.24.0 \
    prometheus-client>=0.19.0

# Copy application
COPY app.py /app/

# Expose port
EXPOSE 8014

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8014/health || exit 1

# Run server
CMD ["python", "app.py"]

