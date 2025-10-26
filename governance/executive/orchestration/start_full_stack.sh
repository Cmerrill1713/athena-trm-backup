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

# Start additional AI services
echo "🤖 Starting AI services..."
cd AI-Projects/universal-ai-tools
# Start knowledge services
nohup python knowledge_sync_service.py > ../../../logs/knowledge_sync.out 2>&1 &
nohup python knowledge_context_service.py > ../../../logs/knowledge_context.out 2>&1 &
nohup python knowledge_gateway_service.py > ../../../logs/knowledge_gateway.out 2>&1 &
nohup python rag_service.py > ../../../logs/rag_service.out 2>&1 &
nohup python vision_rag_service.py > ../../../logs/vision_rag.out 2>&1 &

# Start evolutionary and optimization services
nohup python evolutionary_service.py > ../../../logs/evolutionary.out 2>&1 &
nohup python god_tier_agentic_system.py > ../../../logs/god_tier.out 2>&1 &
nohup python advanced_agentic_test.py > ../../../logs/advanced_agentic.out 2>&1 &

# Start MCP services
nohup python athena_mcp_server.py > ../../../logs/athena_mcp.out 2>&1 &
nohup python mcp_server.py > ../../../logs/mcp_server.out 2>&1 &

# Start dashboard and monitoring
nohup python dashboard.py > ../../../logs/dashboard.out 2>&1 &
cd ../../..

# Start additional services
echo "🔧 Starting additional services..."
# Start FastVLM if available
if [ -f "fastvlm/ml-fastvlm/llava/serve/model_worker.py" ]; then
    cd fastvlm/ml-fastvlm/llava/serve
    nohup python model_worker.py --host 0.0.0.0 --port 8811 > ../../../../logs/fastvlm.out 2>&1 &
    cd ../../../..
fi

# Start Redis for caching
docker run -d --name redis-cache -p 6379:6379 redis:7-alpine

# Start PostgreSQL for data
docker run -d --name postgres-db -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=ai_republic -p 5432:5432 postgres:15-alpine

# Start Weaviate for vector storage
docker run -d --name weaviate-vector -p 8095:8080 -p 50052:50051 semitechnologies/weaviate:1.27.1

# Start monitoring stack
echo "📊 Starting monitoring services..."
docker run -d --name prometheus -p 9090:9090 -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml prom/prometheus
docker run -d --name grafana -p 3001:3000 grafana/grafana
docker run -d --name alertmanager -p 9093:9093 prom/alertmanager

# Start additional AI tools
echo "🛠️  Starting additional AI tools..."
cd AI-Projects/universal-ai-tools
# Start more services
nohup python autonomous-project/autonomous_system.py > ../../../logs/autonomous.out 2>&1 &
nohup python autonomous-project/learning_system.py > ../../../logs/learning.out 2>&1 &
nohup python autonomous-project/evolution_engine.py > ../../../logs/evolution.out 2>&1 &
cd ../../..

echo "✅ Full stack startup complete!"
echo "📊 Services started:"
echo "   Core: Athena (8090), UAT (8181), Bridge (8014)"
echo "   AI: Knowledge, RAG, Vision, Evolutionary, MCP"
echo "   Data: Redis (6379), PostgreSQL (5432), Weaviate (8095)"
echo "   Monitoring: Prometheus (9090), Grafana (3001), AlertManager (9093)"
echo ""
echo "🔍 Check status with: bash scripts/truth.sh"
echo "📝 View logs in: logs/ directory"

