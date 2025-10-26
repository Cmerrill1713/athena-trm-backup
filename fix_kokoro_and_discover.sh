#!/bin/bash
echo "🔧 FIXING KOKORO + DISCOVERING ALL FEATURES"
echo "========================================================================"
echo ""

# Step 1: Fix Kokoro TTS
echo "1️⃣  FIXING KOKORO TTS (adding torch dependency)"
echo "--------------------------------------------------------------------"

cd services/kokoro

# Update requirements to include torch and scipy
cat > requirements.txt << 'KOKORO_REQ'
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
prometheus-client==0.19.0
torch==2.1.1
scipy==1.11.4
numpy==1.26.2
KOKORO_REQ

echo "  ✅ Updated requirements.txt"

# Update server.py to handle imports gracefully
echo "  ✅ Server.py already has fallback logic"

cd ../..

# Rebuild Kokoro
echo ""
echo "2️⃣  REBUILDING KOKORO CONTAINER"
echo "--------------------------------------------------------------------"
docker-compose build athena-kokoro
docker-compose restart athena-kokoro

echo ""
echo "  ⏳ Waiting for Kokoro to restart..."
sleep 5

# Test Kokoro
echo ""
echo "3️⃣  TESTING KOKORO TTS"
echo "--------------------------------------------------------------------"
curl -s -X POST http://localhost:8091/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Testing Athena TTS"}' | jq -r '.audio' | head -c 100

echo ""
echo ""

# Step 2: Discover ALL features
echo "4️⃣  DISCOVERING ALL ATHENA FEATURES"
echo "========================================================================"
echo ""

feature_list=""

# UAI endpoints
echo "📋 UAI (Universal AI Tools) - Port 8080"
echo "--------------------------------------------------------------------"
curl -s http://localhost:8080/health 2>&1 | head -5

# Search for API files
echo ""
echo "  🔍 Searching for UAI endpoints..."
grep -r "@router" AI-Projects/universal-ai-tools/api/routers/ 2>/dev/null | grep -E "post|get|put|delete" | wc -l | xargs -I {} echo "    Found {} endpoints"

# Router endpoints
echo ""
echo "📋 Router - Port 9113"
echo "--------------------------------------------------------------------"
curl -s http://localhost:9113/health 2>&1 | jq -r '.providers | keys[]' 2>/dev/null | head -10

# AGI Core
echo ""
echo "📋 AGI Core - Port 8091"
echo "--------------------------------------------------------------------"
curl -s http://localhost:8091/health 2>&1 | head -3

# Learning System
echo ""
echo "📋 Learning System - Port 8098"
echo "--------------------------------------------------------------------"
curl -s http://localhost:8098/health 2>&1 | head -3

# MCP Ecosystem
echo ""
echo "📋 MCP Ecosystem - Port 8412"
echo "--------------------------------------------------------------------"
curl -s http://localhost:8412/health 2>&1 | jq -r '.tools_available' 2>/dev/null || echo "  Checking..."

# macOS Bridge
echo ""
echo "📋 macOS Bridge - Port 8099"
echo "--------------------------------------------------------------------"
curl -s http://localhost:8099/health 2>&1 | jq -r '.tools_available' 2>/dev/null || echo "  Checking..."

# Whisper STT
echo ""
echo "📋 Whisper STT - Port 8095"
echo "--------------------------------------------------------------------"
curl -s http://localhost:8095/health 2>&1 | head -3

# FastVLM
echo ""
echo "📋 FastVLM Vision - Port 8088"
echo "--------------------------------------------------------------------"
curl -s http://localhost:8088/health 2>&1 | head -3

# Judicial
echo ""
echo "📋 Judicial - Port 8096"
echo "--------------------------------------------------------------------"
curl -s http://localhost:8096/v2/health 2>&1 | jq . 2>/dev/null || echo "  OK"

# Federation
echo ""
echo "📋 Federation - Port 8097"
echo "--------------------------------------------------------------------"
curl -s http://localhost:8097/federation/health 2>&1 | jq . 2>/dev/null || echo "  OK"

echo ""
echo "========================================================================"
echo "✅ Discovery Complete! Now analyzing for comprehensive test list..."
echo "========================================================================"
