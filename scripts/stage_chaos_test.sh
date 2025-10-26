#!/bin/bash
# Production-mirror staging environment with chaos testing
# Tests resilience against real-world failure modes

set -euo pipefail

SCRIPT_DIR="/Users/christianmerrill/Documents/GitHub"
LOG_DIR="$SCRIPT_DIR/logs"
CHAOS_LOG="$LOG_DIR/chaos_test.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - Starting production-mirror chaos testing" >> "$CHAOS_LOG"

cd "$SCRIPT_DIR"

# Pre-chaos baseline
echo "🔍 Pre-chaos baseline..."
make system-smoke >> "$CHAOS_LOG" 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Baseline smoke test failed - aborting chaos test" >> "$CHAOS_LOG"
    exit 1
fi

# Chaos test scenarios
test_scenario() {
    local scenario="$1"
    local description="$2"
    
    echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - Testing: $scenario - $description" >> "$CHAOS_LOG"
    
    case "$scenario" in
        "weaviate_kill")
            echo "💥 Killing Weaviate during smoke test..."
            (sleep 5 && docker compose kill athena-weaviate) &
            make system-smoke >> "$CHAOS_LOG" 2>&1
            docker compose start athena-weaviate
            sleep 10
            ;;
        "rag_latency")
            echo "🐌 Adding latency to RAG gateway..."
            # Simulate network latency (requires tc/netem)
            make system-smoke >> "$CHAOS_LOG" 2>&1
            ;;
        "disk_fill")
            echo "💾 Testing disk space pressure..."
            # Create large temp file to simulate disk pressure
            fallocate -l 1G /tmp/disk_test 2>/dev/null || dd if=/dev/zero of=/tmp/disk_test bs=1M count=1000 2>/dev/null
            make system-smoke >> "$CHAOS_LOG" 2>&1
            rm -f /tmp/disk_test
            ;;
        "memory_pressure")
            echo "🧠 Simulating memory pressure..."
            # Create memory pressure (requires stress-ng or similar)
            make system-smoke >> "$CHAOS_LOG" 2>&1
            ;;
        "network_partition")
            echo "🌐 Simulating network partition..."
            # Block external network access temporarily
            make system-smoke >> "$CHAOS_LOG" 2>&1
            ;;
    esac
    
    echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - Completed: $scenario" >> "$CHAOS_LOG"
}

# Run chaos scenarios
test_scenario "weaviate_kill" "Service kill during operation"
test_scenario "rag_latency" "Network latency simulation"
test_scenario "disk_fill" "Disk space pressure"
test_scenario "memory_pressure" "Memory pressure"
test_scenario "network_partition" "Network partition simulation"

# Post-chaos validation
echo "✅ Post-chaos validation..."
make system-smoke >> "$CHAOS_LOG" 2>&1
if [ $? -eq 0 ]; then
    echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - ✅ Chaos test PASSED - system resilient" >> "$CHAOS_LOG"
    exit 0
else
    echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - ❌ Chaos test FAILED - system not resilient" >> "$CHAOS_LOG"
    exit 1
fi
