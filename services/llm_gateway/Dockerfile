FROM python:3.11-slim

WORKDIR /app

COPY app.py /app/app.py

RUN pip install --no-cache-dir fastapi uvicorn httpx prometheus-client

ENV PORT=8015
ENV OLLAMA_URL=http://host.docker.internal:11434
ENV MODEL=qwen2.5:0.5b

EXPOSE 8015

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8015", "--no-access-log"]

