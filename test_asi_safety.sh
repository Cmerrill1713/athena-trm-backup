#!/bin/bash

echo "🧪 TESTING ASI SAFETY FRAMEWORK"
echo "================================"
echo ""

echo "1️⃣ Testing Phase 2 - Judicial Enforcement"
echo "-------------------------------------------"

# Test adjudication of a minor violation
echo "Testing MINOR violation..."
curl -s -X POST http://localhost:8096/v2/judicial/adjudicate \
  -H "Content-Type: application/json" \
  -d '{
    "event_id":"test-minor-001",
    "instance_id":"athena-router",
    "actor_id":"agent-router-001",
    "article":"I",
    "severity":0.15,
    "confidence":0.85,
    "classification":"minor_policy_drift"
  }' | jq '.'

echo ""
echo "Testing MAJOR violation..."
curl -s -X POST http://localhost:8096/v2/judicial/adjudicate \
  -H "Content-Type: application/json" \
  -d '{
    "event_id":"test-major-001",
    "instance_id":"athena-uai",
    "actor_id":"agent-uai-001",
    "article":"II",
    "severity":0.65,
    "confidence":0.90,
    "classification":"major_constitutional_violation"
  }' | jq '.'

echo ""
echo "Testing CRITICAL violation (should trigger TRIBUNAL)..."
curl -s -X POST http://localhost:8096/v2/judicial/adjudicate \
  -H "Content-Type: application/json" \
  -d '{
    "event_id":"test-critical-001",
    "instance_id":"athena-autonomous",
    "actor_id":"agent-autonomous-001",
    "article":"II",
    "severity":0.95,
    "confidence":0.98,
    "classification":"critical_safety_violation"
  }' | jq '.'

echo ""
echo "2️⃣ Testing Phase 3 - Federation Gateway"
echo "-------------------------------------------"

echo "Testing federation status..."
curl -s http://localhost:8097/federation/status | jq '.' 2>/dev/null || echo "(Federation endpoints may differ)"

echo ""
echo "✅ ASI SAFETY FRAMEWORK TEST COMPLETE"

