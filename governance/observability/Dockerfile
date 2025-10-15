# Governance Metrics Exporter
FROM alpine:3.18

# Install runtime dependencies
RUN apk add --no-cache ca-certificates curl python3 py3-pip

# Create non-root user
RUN addgroup -g 1001 -S governance && \
    adduser -u 1001 -S governance -G governance

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt && \
    pip3 install --no-cache-dir prometheus-client

# Copy application code
COPY --chown=governance:governance . .

# Create necessary directories
RUN mkdir -p /var/log/governance && \
    chown -R governance:governance /app /var/log/governance

# Switch to non-root user
USER governance

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the exporter
CMD ["python3", "governance_metrics_exporter.py"]
