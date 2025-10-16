FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir redis

# Copy AGI Core and infra
COPY agi_core/ /app/agi_core/
COPY infra/ /app/infra/

# Create sandbox directory
RUN mkdir -p /app/sandbox

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

EXPOSE 9112

CMD ["python", "-u", "agi_core/remediator.py"]
