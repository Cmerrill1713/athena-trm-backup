#!/bin/bash
# Complete real-world validation checklist
# Safe production validation with exact commands and monitoring

set -euo pipefail

SCRIPT_DIR="/Users/christianmerrill/Documents/GitHub"
LOG_DIR="$SCRIPT_DIR/logs"
CHECKLIST_LOG="$LOG_DIR/validation_checklist.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - Starting real-world validation checklist" >> "$CHECKLIST_LOG"

cd "$SCRIPT_DIR"

# Phase 0: Freeze & baselines
run_phase0() {
    echo "🏷️ Phase 0: Freeze & baselines..." >> "$CHECKLIST_LOG"
    
    echo "1. Setting up preconditions..."
    make phase0-preconditions >> "$CHECKLIST_LOG" 2>&1
    
    echo "2. Quick green check..."
    make ops-status >> "$CHECKLIST_LOG" 2>&1
    
    echo "3. Opening health dashboard..."
    # Note: grafana-open would need to be implemented
    echo "   Open Grafana dashboard manually: http://localhost:3000" >> "$CHECKLIST_LOG"
    
    echo "✅ Phase 0 completed" >> "$CHECKLIST_LOG"
}

# Phase 1: Shadow real traffic
run_phase1() {
    echo "🔍 Phase 1: Shadow real traffic (no user impact)..." >> "$CHECKLIST_LOG"
    
    echo "1. Starting shadow validation gates..."
    make shadow-validation-gates >> "$CHECKLIST_LOG" 2>&1 &
    local shadow_pid=$!
    
    echo "2. Starting shadow traffic mirroring..."
    make traffic-shadow-start >> "$CHECKLIST_LOG" 2>&1 &
    local mirror_pid=$!
    
    echo "3. Monitoring shadow traffic stats..."
    for i in {1..24}; do  # Monitor for 2 hours (24 * 5min intervals)
        echo "   Checking shadow stats (iteration $i/24)..."
        make traffic-shadow-stats >> "$CHECKLIST_LOG" 2>&1
        
        # Check gates
        local mismatch_rate=$(grep "Output mismatch rate" "$LOG_DIR/shadow_validation_gates.log" 2>/dev/null | tail -1 | awk '{print $4}' | sed 's/%//' || echo "0")
        local latency_delta=$(grep "P95 latency delta" "$LOG_DIR/shadow_validation_gates.log" 2>/dev/null | tail -1 | awk '{print $4}' | sed 's/%//' || echo "0")
        local error_delta=$(grep "Error rate delta" "$LOG_DIR/shadow_validation_gates.log" 2>/dev/null | tail -1 | awk '{print $4}' | sed 's/%//' || echo "0")
        
        # Check gate breaches
        if (( $(echo "$mismatch_rate > 0.1" | bc -l) )); then
            echo "❌ Gate breach: Output mismatch ${mismatch_rate}% > 0.1%" >> "$CHECKLIST_LOG"
            kill $shadow_pid $mirror_pid 2>/dev/null || true
            make real-world-validation-rollback >> "$CHECKLIST_LOG" 2>&1
            return 1
        fi
        
        if (( $(echo "$latency_delta > 10" | bc -l) )); then
            echo "❌ Gate breach: P95 latency delta ${latency_delta}% > 10%" >> "$CHECKLIST_LOG"
            kill $shadow_pid $mirror_pid 2>/dev/null || true
            make real-world-validation-rollback >> "$CHECKLIST_LOG" 2>&1
            return 1
        fi
        
        if (( $(echo "$error_delta > 0.3" | bc -l) )); then
            echo "❌ Gate breach: Error rate delta ${error_delta}% > 0.3%" >> "$CHECKLIST_LOG"
            kill $shadow_pid $mirror_pid 2>/dev/null || true
            make real-world-validation-rollback >> "$CHECKLIST_LOG" 2>&1
            return 1
        fi
        
        echo "   ✅ Gates passing: mismatch=${mismatch_rate}%, latency=${latency_delta}%, error=${error_delta}%" >> "$CHECKLIST_LOG"
        sleep 300  # 5 minutes
    done
    
    echo "✅ Phase 1 completed: Shadow validation passed" >> "$CHECKLIST_LOG"
    return 0
}

# Phase 2: Tiny canary
run_phase2() {
    echo "🚦 Phase 2: Tiny canary (real users, tiny blast radius)..." >> "$CHECKLIST_LOG"
    
    echo "1. Deploying 1% canary..."
    make canary-deploy >> "$CHECKLIST_LOG" 2>&1
    
    echo "2. Monitoring canary status..."
    for step in 1 5 10; do
        echo "   Promoting to ${step}% canary..."
        
        # Deploy at new percentage
        ./scripts/canary_by_risk.sh $step 60 low deploy >> "$CHECKLIST_LOG" 2>&1
        
        # Monitor for 30 minutes at each step
        for i in {1..6}; do  # 6 * 5min = 30min
            echo "     Monitoring ${step}% canary (iteration $i/6)..."
            make canary-status >> "$CHECKLIST_LOG" 2>&1
            
            # Check promotion gates
            local error_rate=$(curl -s "http://localhost:9093/metrics" | grep 'agi_requests_total{outcome="error"}' | awk '{print $2}' 2>/dev/null || echo "0")
            local p95_latency=$(curl -s "http://localhost:9093/metrics" | grep 'agi_request_duration_ms_bucket' | awk '{print $2}' | tail -1 2>/dev/null || echo "0")
            
            # Check gate breaches
            if (( $(echo "$error_rate > 0.5" | bc -l) )); then
                echo "❌ Gate breach: Error rate ${error_rate}% > 0.5%" >> "$CHECKLIST_LOG"
                make canary-rollback >> "$CHECKLIST_LOG" 2>&1
                return 1
            fi
            
            if (( $(echo "$p95_latency > 2000" | bc -l) )); then
                echo "❌ Gate breach: P95 latency ${p95_latency}ms > 2000ms" >> "$CHECKLIST_LOG"
                make canary-rollback >> "$CHECKLIST_LOG" 2>&1
                return 1
            fi
            
            echo "     ✅ Gates passing: error=${error_rate}%, latency=${p95_latency}ms" >> "$CHECKLIST_LOG"
            sleep 300  # 5 minutes
        done
        
        echo "   ✅ ${step}% canary stable for 30 minutes" >> "$CHECKLIST_LOG"
    done
    
    echo "✅ Phase 2 completed: Canary deployment successful" >> "$CHECKLIST_LOG"
    return 0
}

# Phase 3: Expand safely
run_phase3() {
    echo "📈 Phase 3: Expand safely (only if gates stay green)..." >> "$CHECKLIST_LOG"
    
    echo "1. Starting safe expansion..."
    make prod-rollout >> "$CHECKLIST_LOG" 2>&1
    
    echo "2. Monitoring rollout status..."
    make prod-rollout-status >> "$CHECKLIST_LOG" 2>&1
    
    echo "✅ Phase 3 completed: Safe expansion successful" >> "$CHECKLIST_LOG"
    return 0
}

# Smoke probes
run_smoke_probes() {
    echo "🔍 Running smoke probes..." >> "$CHECKLIST_LOG"
    
    echo "1. Health & inventory:"
    curl -s http://localhost:8000/health | jq >> "$CHECKLIST_LOG" 2>&1
    curl -s http://localhost:8000/tools | jq '.[].name' >> "$CHECKLIST_LOG" 2>&1
    curl -s http://localhost:8000/trm/policy | jq '.stats' >> "$CHECKLIST_LOG" 2>&1
    
    echo "2. RAG sanity:"
    curl -s http://localhost:8087/query -H 'Content-Type: application/json' \
        -d '{"query":"Where is the router MCP provider configured?","top_k":8}' | \
        jq '.hits|length' >> "$CHECKLIST_LOG" 2>&1
    
    echo "3. LLM-agnostic router → UAI path:"
    curl -s http://localhost:8080/v1/chat/completions -H 'Content-Type: application/json' \
        -d '{"model":"auto","messages":[{"role":"user","content":"Say hello in 3 words"}]}' | \
        jq '.choices[0].message' >> "$CHECKLIST_LOG" 2>&1
    
    echo "4. End-to-end AGI exec:"
    curl -s http://localhost:8000/api/execute -H 'Content-Type: application/json' \
        -d '{"objective":"Where are agent experts wired in the codebase? show file paths","tools":[],"max_steps":6,"flags":{"adaptive_trm":true}}' | \
        jq '.trace[-5:]' >> "$CHECKLIST_LOG" 2>&1
    
    echo "✅ Smoke probes completed" >> "$CHECKLIST_LOG"
}

# Evidence pack
create_evidence_pack() {
    echo "📦 Creating evidence pack..." >> "$CHECKLIST_LOG"
    
    local evidence_dir="evidence_pack_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$evidence_dir"
    
    echo "1. Shadow comparison report..."
    cp "$LOG_DIR/shadow_validation_gates.log" "$evidence_dir/" 2>/dev/null || true
    cp "$LOG_DIR/shadow_mismatches.log" "$evidence_dir/" 2>/dev/null || true
    
    echo "2. Canary SLO snapshot..."
    make canary-status > "$evidence_dir/canary_slo_snapshot.txt" 2>&1
    
    echo "3. TRM policy stats..."
    curl -s http://localhost:8000/trm/policy | jq > "$evidence_dir/trm_policy_stats.json" 2>/dev/null || true
    
    echo "4. RAG metrics..."
    curl -s http://localhost:9093/metrics | grep -E "(rag_|trm_)" > "$evidence_dir/rag_metrics.txt" 2>/dev/null || true
    
    echo "5. Router model distribution..."
    curl -s http://localhost:9113/health | jq '.providers' > "$evidence_dir/router_distribution.json" 2>/dev/null || true
    
    echo "✅ Evidence pack created: $evidence_dir" >> "$CHECKLIST_LOG"
}

# Main execution
case "${1:-run}" in
    "run")
        echo "🚀 Running complete real-world validation checklist..."
        
        # Phase 0: Freeze & baselines
        run_phase0
        
        # Phase 1: Shadow real traffic
        if ! run_phase1; then
            echo "❌ Validation failed at Phase 1" >> "$CHECKLIST_LOG"
            exit 1
        fi
        
        # Phase 2: Tiny canary
        if ! run_phase2; then
            echo "❌ Validation failed at Phase 2" >> "$CHECKLIST_LOG"
            exit 1
        fi
        
        # Phase 3: Expand safely
        if ! run_phase3; then
            echo "❌ Validation failed at Phase 3" >> "$CHECKLIST_LOG"
            exit 1
        fi
        
        # Smoke probes
        run_smoke_probes
        
        # Evidence pack
        create_evidence_pack
        
        echo "🎉 Real-world validation checklist completed successfully!" >> "$CHECKLIST_LOG"
        ;;
    "smoke-probes")
        run_smoke_probes
        ;;
    "evidence-pack")
        create_evidence_pack
        ;;
    "status")
        echo "📊 Validation checklist status:"
        echo "=== Recent Checklist Logs ==="
        tail -20 "$CHECKLIST_LOG" 2>/dev/null || echo "No checklist logs yet"
        echo ""
        echo "=== Current System Status ==="
        make ops-status
        echo ""
        echo "=== Shadow Status ==="
        make traffic-shadow-stats
        echo ""
        echo "=== Canary Status ==="
        make canary-status
        ;;
    *)
        echo "Usage: $0 [run|smoke-probes|evidence-pack|status]"
        echo "Example: $0 run  # Run complete validation checklist"
        ;;
esac
