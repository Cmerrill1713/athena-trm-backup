#!/bin/bash
# Start the full AI Republic stack with 20+ services

set -e

echo "🚀 Starting AI Republic Full Stack (20+ containers)"
echo "=================================================="

# Create logs directory
mkdir -p logs

# Start core services
echo "🏗️  Starting core services..."
ATH_TOKEN=supersecret nohup python -m uvicorn athena.api:app --host 127.0.0.1 --port 8090 > logs/athena.out 2>&1 &
UAT_TOKEN=supersecret UAT_AUTO_SEED=1 nohup python -m uvicorn uat.api:app --host 127.0.0.1 --port 8181 > logs/uat.out 2>&1 &
UAT_TOKEN=supersecret ATH_TOKEN=supersecret UAT_BASE=http://127.0.0.1:8181 ATHENA_BASE=http://127.0.0.1:8090 PYTHONPATH=.. nohup python -m uvicorn adapter:app --host 0.0.0.0 --port 8014 > logs/bridge.out 2>&1 &

# Start additional Python services
echo "🤖 Starting additional Python services..."
# Start MCP servers
nohup python athena_mcp_server.py > logs/athena_mcp.out 2>&1 &
nohup python mcp_server.py > logs/mcp_server.out 2>&1 &

# Start other services
nohup python athena_scheduler.py > logs/athena_scheduler.out 2>&1 &
nohup python behavioral_learning.py > logs/behavioral_learning.out 2>&1 &
nohup python calendar_monitor.py > logs/calendar_monitor.out 2>&1 &

# Start Docker containers for more services
echo "🐳 Starting Docker containers..."

# Start Redis instances
docker run -d --name redis-cache -p 6379:6379 redis:7-alpine
docker run -d --name redis-session -p 6380:6379 redis:7-alpine
docker run -d --name redis-queue -p 6381:6379 redis:7-alpine

# Start PostgreSQL databases
docker run -d --name postgres-main -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=ai_republic -p 5432:5432 postgres:15-alpine
docker run -d --name postgres-analytics -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=analytics -p 5433:5432 postgres:15-alpine

# Start Weaviate
docker run -d --name weaviate-vector -p 8095:8080 -p 50052:50051 semitechnologies/weaviate:1.27.1

# Start monitoring stack
echo "📊 Starting monitoring services..."
docker run -d --name prometheus -p 9090:9090 prom/prometheus
docker run -d --name grafana -p 3001:3000 grafana/grafana
docker run -d --name alertmanager -p 9093:9093 prom/alertmanager

# Start additional infrastructure
docker run -d --name nginx-proxy -p 80:80 -p 443:443 nginx:alpine
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management-alpine
docker run -d --name elasticsearch -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" elasticsearch:8.11.0
docker run -d --name kibana -p 5601:5601 -e "ELASTICSEARCH_HOSTS=http://elasticsearch:9200" kibana:8.11.0

# Start AI/ML services
docker run -d --name ollama -p 11434:11434 ollama/ollama
docker run -d --name chroma -p 8000:8000 chromadb/chroma

# Start more services
docker run -d --name traefik -p 8080:8080 -p 80:80 -p 443:443 traefik:v2.10
docker run -d --name consul -p 8500:8500 -p 8600:8600/udp consul:1.15
docker run -d --name vault -p 8200:8200 vault:1.13

echo "✅ Full stack startup complete!"
echo "📊 Services running:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -v CONTAINER
echo ""
echo "🔍 Check status with: bash scripts/truth.sh"
echo "📝 View logs in: logs/ directory"
