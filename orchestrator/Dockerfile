FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app.py .
COPY __main__.py .

# Create directories
RUN mkdir -p /app/state /app/artifacts/ledger /app/schemas /app/exec /app/infra

# Health check
HEALTHCHECK --interval=30s --timeout=3s --retries=5 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()"

# Expose port
EXPOSE 8000

# Run
ENV ORCH_PORT=8000
CMD ["python3", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
