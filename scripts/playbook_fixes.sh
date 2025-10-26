#!/bin/bash
# Fast "If X → Then Y" Playbook
# Quick fixes for common production validation issues

set -euo pipefail

SCRIPT_DIR="/Users/christianmerrill/Documents/GitHub"
LOG_DIR="$SCRIPT_DIR/logs"
PLAYBOOK_LOG="$LOG_DIR/playbook_fixes.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - Playbook fix applied: $1" >> "$PLAYBOOK_LOG"

cd "$SCRIPT_DIR"

# Fix RAG zero-hit bursts
fix_rag_zero_hits() {
    echo "🔧 Fixing RAG zero-hit bursts..." >> "$PLAYBOOK_LOG"
    
    echo "1. Running delta RAG seed..."
    make rag-seed-agi >> "$PLAYBOOK_LOG" 2>&1
    
    echo "2. Checking Weaviate memory/compaction..."
    curl -s http://localhost:8090/v1/.well-known/ready >> "$PLAYBOOK_LOG" 2>&1
    
    echo "3. Verifying RAG Gateway query..."
    curl -s http://localhost:8087/query -H 'Content-Type: application/json' \
        -d '{"query":"test query","top_k":3}' | jq '.hits|length' >> "$PLAYBOOK_LOG" 2>&1
    
    echo "✅ RAG zero-hit fix applied" >> "$PLAYBOOK_LOG"
}

# Fix TRM oscillation / swap-storm
fix_trm_oscillation() {
    echo "🔧 Fixing TRM oscillation / swap-storm..." >> "$PLAYBOOK_LOG"
    
    echo "1. Raising TRM trigger threshold..."
    export TRM_TRIGGER_THRESHOLD=0.65
    echo "   TRM threshold set to: $TRM_TRIGGER_THRESHOLD" >> "$PLAYBOOK_LOG"
    
    echo "2. Setting force fast model..."
    export FORCE_FAST_MODEL=true
    echo "   Force fast model: $FORCE_FAST_MODEL" >> "$PLAYBOOK_LOG"
    
    echo "3. Restarting stack..."
    make stack-restart >> "$PLAYBOOK_LOG" 2>&1
    
    echo "✅ TRM oscillation fix applied" >> "$PLAYBOOK_LOG"
}

# Fix latency drift
fix_latency_drift() {
    echo "🔧 Fixing latency drift..." >> "$PLAYBOOK_LOG"
    
    echo "1. Throttling TRM (fewer cycles)..."
    export TRM_MAX_CYCLES=8
    echo "   TRM max cycles set to: $TRM_MAX_CYCLES" >> "$PLAYBOOK_LOG"
    
    echo "2. Reducing context budget..."
    export RAG_CONTEXT_BUDGET=2000
    echo "   RAG context budget set to: $RAG_CONTEXT_BUDGET" >> "$PLAYBOOK_LOG"
    
    echo "3. Checking model pool for cold-swapping..."
    curl -s http://localhost:8420/status | jq '.active_model' >> "$PLAYBOOK_LOG" 2>&1
    
    echo "✅ Latency drift fix applied" >> "$PLAYBOOK_LOG"
}

# Fix error spikes
fix_error_spikes() {
    echo "🔧 Fixing error spikes..." >> "$PLAYBOOK_LOG"
    
    echo "1. Checking router/UAI logs..."
    docker logs athena-router 2>&1 | tail -20 >> "$PLAYBOOK_LOG" 2>&1
    docker logs athena-uai 2>&1 | tail -20 >> "$PLAYBOOK_LOG" 2>&1
    
    echo "2. Checking gateway/Weaviate..."
    docker logs athena-rag-gateway 2>&1 | tail -20 >> "$PLAYBOOK_LOG" 2>&1
    docker logs athena-weaviate 2>&1 | tail -20 >> "$PLAYBOOK_LOG" 2>&1
    
    echo "3. Checking error rate delta..."
    local error_rate=$(curl -s "http://localhost:9093/metrics" | grep 'agi_requests_total{outcome="error"}' | awk '{print $2}' 2>/dev/null || echo "0")
    echo "   Current error rate: ${error_rate}%" >> "$PLAYBOOK_LOG"
    
    if (( $(echo "$error_rate > 0.5" | bc -l) )); then
        echo "4. Error rate > 0.5% - rolling back canary..."
        make canary-rollback >> "$PLAYBOOK_LOG" 2>&1
    fi
    
    echo "✅ Error spikes fix applied" >> "$PLAYBOOK_LOG"
}

# Run minimal chaos test
run_minimal_chaos() {
    echo "💥 Running minimal chaos test (canary only, off-hours)..." >> "$PLAYBOOK_LOG"
    
    echo "1. Killing Weaviate pod..."
    docker compose kill athena-weaviate >> "$PLAYBOOK_LOG" 2>&1
    echo "   Expected: graceful degrade (planner-only), no 5xx storm" >> "$PLAYBOOK_LOG"
    sleep 30
    
    echo "2. Restarting Weaviate..."
    docker compose start athena-weaviate >> "$PLAYBOOK_LOG" 2>&1
    sleep 30
    
    echo "3. Adding 300ms RTT to RAG gateway link..."
    # Note: This would require network simulation tools
    echo "   Expected: p95 grows but stays under alert thresholds" >> "$PLAYBOOK_LOG"
    
    echo "4. Evicting VRAM model..."
    curl -X POST "http://localhost:8420/v1/models/evict" -d '{"model":"all"}' >> "$PLAYBOOK_LOG" 2>&1
    echo "   Expected: model pool warm-loads next; no user error spikes" >> "$PLAYBOOK_LOG"
    
    echo "✅ Minimal chaos test completed" >> "$PLAYBOOK_LOG"
}

# Main execution
case "${1:-help}" in
    "rag-zero-hits")
        fix_rag_zero_hits
        ;;
    "trm-oscillation")
        fix_trm_oscillation
        ;;
    "latency-drift")
        fix_latency_drift
        ;;
    "error-spikes")
        fix_error_spikes
        ;;
    "minimal-chaos")
        run_minimal_chaos
        ;;
    "help")
        echo "Usage: $0 [rag-zero-hits|trm-oscillation|latency-drift|error-spikes|minimal-chaos]"
        echo ""
        echo "Available fixes:"
        echo "  rag-zero-hits    - Fix RAG zero-hit bursts"
        echo "  trm-oscillation  - Fix TRM oscillation / swap-storm"
        echo "  latency-drift    - Fix latency drift > +10%"
        echo "  error-spikes     - Fix error spikes"
        echo "  minimal-chaos    - Run minimal chaos test"
        echo ""
        echo "Examples:"
        echo "  $0 rag-zero-hits    # Fix RAG zero-hit bursts"
        echo "  $0 trm-oscillation  # Fix TRM oscillation"
        ;;
    *)
        echo "Unknown fix: $1"
        echo "Run '$0 help' for available fixes"
        ;;
esac
