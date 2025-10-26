#!/bin/bash

echo "🤖 Deploying Autonomous Features A-F + TRM Integration"
echo "======================================================="
echo ""

# Step 1: Re-embed knowledge base with new TRM training guide
echo "1️⃣ Embedding new TRM training documentation..."
python3 embed_knowledge_base.py
echo ""

# Step 2: Add autonomous orchestrator to docker-compose
echo "2️⃣ Adding Autonomous Orchestrator service..."
cat >> docker-compose.yml << 'DOCKERCOMPOSE'

  # ===========================================================================
  # AUTONOMOUS ORCHESTRATOR (Port 9114) - Self-Improvement Coordination
  # ===========================================================================

  autonomous-orchestrator:
    build:
      context: ./services/autonomous-orchestrator
      dockerfile: Dockerfile
    container_name: athena-autonomous
    restart: unless-stopped
    ports:
      - "127.0.0.1:9114:9114"
    environment:
      - PYTHONUNBUFFERED=1
      - PORT=9114
    volumes:
      - ./services/autonomous-orchestrator:/app:ro
      - ./state/trm:/app/state/trm:rw
      - ./knowledge_base:/knowledge_base:ro
      - ./embed_knowledge_base.py:/app/embed_knowledge_base.py:ro
    networks:
      - athena-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9114/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    labels:
      - "athena.service=autonomous-orchestrator"
      - "athena.port=9114"
      - "athena.layer=autonomous"
DOCKERCOMPOSE

echo "✅ Service definition added"
echo ""

# Step 3: Build and start autonomous orchestrator
echo "3️⃣ Building Autonomous Orchestrator..."
docker-compose build autonomous-orchestrator

echo ""
echo "4️⃣ Starting Autonomous Orchestrator..."
docker-compose up -d autonomous-orchestrator

echo ""
echo "5️⃣ Waiting for service to be healthy..."
sleep 5

# Step 6: Test autonomous orchestrator
echo "6️⃣ Testing Autonomous Orchestrator..."
curl -s http://localhost:9114/health | jq '.'

echo ""
echo "7️⃣ Getting Autonomous System Status..."
curl -s http://localhost:9114/status | jq '.'

echo ""
echo "======================================================="
echo "✅ Autonomous Features Deployment Complete!"
echo ""
echo "Available endpoints:"
echo "  • http://localhost:9114/health - Health check"
echo "  • http://localhost:9114/status - System status"
echo "  • http://localhost:9114/prompt/evolve - Prompt evolution"
echo "  • http://localhost:9114/trm/decide - TRM routing decision"
echo "  • http://localhost:9114/feedback - Record learning feedback"
echo "  • http://localhost:9114/autonomous/enable-all - Enable all features"
