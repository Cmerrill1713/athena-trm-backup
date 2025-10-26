#!/bin/bash
# Test Athena's Learning System

echo "🧪 =========================================="
echo "🧪 TESTING ATHENA'S LEARNING SYSTEM"
echo "🧪 =========================================="

# Check if learning service is running
echo ""
echo "1️⃣ Checking Learning Service Health..."
health=$(curl -s http://localhost:8098/health)
echo "Response: $health"

if echo "$health" | grep -q "healthy"; then
    echo "✅ Learning service is healthy"
else
    echo "❌ Learning service not responding"
    exit 1
fi

# Test feedback analysis
echo ""
echo "2️⃣ Testing Feedback Analysis Agent..."
feedback_result=$(curl -s -X POST "http://localhost:8098/v1/feedback/analyze?hours=24")
echo "$feedback_result" | jq -r '.status, .feedback_count'

# Test router learning
echo ""
echo "3️⃣ Testing Router Learning Agent..."
router_result=$(curl -s -X POST "http://localhost:8098/v1/router/learn?hours=24")
echo "$router_result" | jq -r '.agent, .status'

# Trigger complete learning cycle
echo ""
echo "4️⃣ Running Complete Learning Cycle..."
echo "   (This orchestrates all agents in parallel)"

cycle_result=$(curl -s -X POST "http://localhost:8098/v1/learning/run")
echo ""
echo "   Cycle Results:"
echo "$cycle_result" | jq '{
    cycle_id: .cycle_id,
    duration: .duration_seconds,
    agents: .agents_executed,
    approved: .approved,
    verdict: .safety_review.verdict
}'

# Check learning history
echo ""
echo "5️⃣ Checking Learning History..."
history=$(curl -s http://localhost:8098/v1/learning/history)
total_cycles=$(echo "$history" | jq -r '.total_cycles')
echo "   Total learning cycles: $total_cycles"

echo ""
echo "🎯 =========================================="
echo "🎯 ATHENA'S LEARNING SYSTEM TEST COMPLETE"
echo "🎯 =========================================="
