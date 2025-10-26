FROM python:3.11-slim

WORKDIR /app

# Install dependencies including curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY agi_core/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy AGI Core and infra
COPY agi_core/ /app/agi_core/
COPY infra/ /app/infra/

# Create sandbox directory
RUN mkdir -p /app/sandbox

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

EXPOSE 9112

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:9112/health || exit 1

CMD ["python", "-u", "agi_core/remediator.py"]
