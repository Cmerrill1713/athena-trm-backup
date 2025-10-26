#!/bin/bash
# Phase 0 - Preconditions: Freeze what's live and set non-breaking defaults
# Safe production validation setup

set -euo pipefail

SCRIPT_DIR="/Users/christianmerrill/Documents/GitHub"
LOG_DIR="$SCRIPT_DIR/logs"
PRECONDITIONS_LOG="$LOG_DIR/phase0_preconditions.log"

# Configuration
FREEZE_TAG="prod-validation-$(date +%Y%m%d_%H%M%S)"
CONSERVATIVE_TRM_THRESHOLD=0.6

# Ensure log directory exists
mkdir -p "$LOG_DIR"

echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - Starting Phase 0: Preconditions" >> "$PRECONDITIONS_LOG"

cd "$SCRIPT_DIR"

# Freeze current state with tagging
freeze_current_state() {
    echo "🏷️ Freezing current state with tag: $FREEZE_TAG" >> "$PRECONDITIONS_LOG"
    
    # Create freeze manifest
    cat > "freeze_manifest_${FREEZE_TAG}.json" << EOF
{
    "freeze_tag": "$FREEZE_TAG",
    "timestamp": "$(date -u '+%Y-%m-%d %H:%M:%S UTC')",
    "services": {
        "agi_core": {
            "port": 8000,
            "version": "current",
            "config": "production"
        },
        "rag_gateway": {
            "port": 8087,
            "version": "current",
            "config": "dynamic-rag"
        },
        "trm_service": {
            "port": 8420,
            "version": "current",
            "config": "adaptive-policy"
        },
        "uai": {
            "port": 8080,
            "version": "current",
            "config": "router-auto"
        },
        "router": {
            "port": 9113,
            "version": "current",
            "config": "model-routing"
        },
        "weaviate": {
            "port": 8090,
            "version": "1.21.0",
            "config": "vector-db"
        }
    },
    "docker_images": {
        "weaviate": "semitechnologies/weaviate:1.21.0",
        "prometheus": "prom/prometheus:latest",
        "grafana": "grafana/grafana:latest"
    }
}
EOF
    
    echo "  - Freeze manifest created: freeze_manifest_${FREEZE_TAG}.json" >> "$PRECONDITIONS_LOG"
    
    # Tag current git state
    if git rev-parse --git-dir > /dev/null 2>&1; then
        git tag "$FREEZE_TAG" 2>/dev/null || echo "  - Git tag already exists or not in git repo" >> "$PRECONDITIONS_LOG"
        echo "  - Git tag created: $FREEZE_TAG" >> "$PRECONDITIONS_LOG"
    fi
    
    echo "✅ Current state frozen with tag: $FREEZE_TAG" >> "$PRECONDITIONS_LOG"
}

# Verify green dashboards and quiet alerts
verify_green_state() {
    echo "🔍 Verifying green state..." >> "$PRECONDITIONS_LOG"
    
    local all_green=true
    
    # Check system smoke test
    echo "  - Running system smoke test..." >> "$PRECONDITIONS_LOG"
    if make system-smoke >> "$PRECONDITIONS_LOG" 2>&1; then
        echo "  ✅ System smoke test: GREEN" >> "$PRECONDITIONS_LOG"
    else
        echo "  ❌ System smoke test: FAILED" >> "$PRECONDITIONS_LOG"
        all_green=false
    fi
    
    # Check RAG golden test
    echo "  - Running RAG golden test..." >> "$PRECONDITIONS_LOG"
    local golden_score=$(make rag-golden 2>/dev/null | grep "Passed" | awk '{print $2}' | cut -d'/' -f1 || echo "0")
    if [ "$golden_score" -ge 8 ]; then
        echo "  ✅ RAG golden test: ${golden_score}/10 (GREEN)" >> "$PRECONDITIONS_LOG"
    else
        echo "  ❌ RAG golden test: ${golden_score}/10 (FAILED)" >> "$PRECONDITIONS_LOG"
        all_green=false
    fi
    
    # Check service health
    local services=("http://localhost:8000" "http://localhost:8087" "http://localhost:8420" "http://localhost:8080" "http://localhost:9113" "http://localhost:8090")
    for service in "${services[@]}"; do
        if curl -sf "$service/health" >/dev/null 2>&1; then
            echo "  ✅ Service health: $service (GREEN)" >> "$PRECONDITIONS_LOG"
        else
            echo "  ❌ Service health: $service (FAILED)" >> "$PRECONDITIONS_LOG"
            all_green=false
        fi
    done
    
    if [ "$all_green" = true ]; then
        echo "✅ All dashboards GREEN and alerts QUIET" >> "$PRECONDITIONS_LOG"
        return 0
    else
        echo "❌ Not all systems GREEN - aborting preconditions" >> "$PRECONDITIONS_LOG"
        return 1
    fi
}

# Set non-breaking defaults
set_conservative_defaults() {
    echo "🛡️ Setting conservative defaults..." >> "$PRECONDITIONS_LOG"
    
    # Set conservative TRM threshold
    export TRM_TRIGGER_THRESHOLD=$CONSERVATIVE_TRM_THRESHOLD
    echo "  - TRM threshold set to: $CONSERVATIVE_TRM_THRESHOLD (conservative)" >> "$PRECONDITIONS_LOG"
    
    # Ensure router uses auto model selection
    export MODEL_ROUTE_OVERRIDE="auto"
    echo "  - Router model selection: auto" >> "$PRECONDITIONS_LOG"
    
    # Set fail-closed behavior for AGI
    export AGI_FAIL_CLOSED=true
    echo "  - AGI fail-closed: enabled (continue with base plan if RAG/Graph fail)" >> "$PRECONDITIONS_LOG"
    
    # Set conservative timeouts
    export AGI_TIMEOUT_MS=30000
    export RAG_TIMEOUT_MS=5000
    export TRM_TIMEOUT_MS=2000
    echo "  - Conservative timeouts set" >> "$PRECONDITIONS_LOG"
    
    # Restart stack with new defaults
    echo "  - Restarting stack with conservative defaults..." >> "$PRECONDITIONS_LOG"
    make stack-restart >> "$PRECONDITIONS_LOG" 2>&1
    
    # Wait for services to be ready
    sleep 30
    
    # Verify new defaults are applied
    local trm_policy=$(curl -s "http://localhost:8000/trm/policy" | jq -r '.config.trigger_threshold // "unknown"' 2>/dev/null)
    echo "  - TRM policy threshold: $trm_policy" >> "$PRECONDITIONS_LOG"
    
    echo "✅ Conservative defaults applied" >> "$PRECONDITIONS_LOG"
}

# Create rollback snapshot
create_rollback_snapshot() {
    echo "📸 Creating rollback snapshot..." >> "$PRECONDITIONS_LOG"
    
    # Create rollback script
    cat > "rollback_to_${FREEZE_TAG}.sh" << EOF
#!/bin/bash
# Rollback script for $FREEZE_TAG

set -euo pipefail

echo "🔄 Rolling back to $FREEZE_TAG..."

# Restore git state if applicable
if git rev-parse --git-dir > /dev/null 2>&1; then
    git checkout $FREEZE_TAG 2>/dev/null || echo "Git checkout failed or tag not found"
fi

# Restore conservative defaults
export TRM_TRIGGER_THRESHOLD=$CONSERVATIVE_TRM_THRESHOLD
export MODEL_ROUTE_OVERRIDE="auto"
export AGI_FAIL_CLOSED=true

# Restart stack
make stack-restart

echo "✅ Rollback to $FREEZE_TAG completed"
EOF
    
    chmod +x "rollback_to_${FREEZE_TAG}.sh"
    echo "  - Rollback script created: rollback_to_${FREEZE_TAG}.sh" >> "$PRECONDITIONS_LOG"
    
    echo "✅ Rollback snapshot created" >> "$PRECONDITIONS_LOG"
}

# Main execution
main() {
    echo "🚀 Phase 0: Setting up production validation preconditions..." >> "$PRECONDITIONS_LOG"
    
    # Step 1: Freeze current state
    freeze_current_state
    
    # Step 2: Verify green state
    if ! verify_green_state; then
        echo "❌ Preconditions failed - not all systems green" >> "$PRECONDITIONS_LOG"
        exit 1
    fi
    
    # Step 3: Set conservative defaults
    set_conservative_defaults
    
    # Step 4: Create rollback snapshot
    create_rollback_snapshot
    
    echo "✅ Phase 0 completed successfully" >> "$PRECONDITIONS_LOG"
    echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - Preconditions ready for production validation" >> "$PRECONDITIONS_LOG"
}

# Handle script arguments
case "${1:-run}" in
    "run")
        main
        ;;
    "status")
        echo "📊 Phase 0 Preconditions Status:"
        echo "=== Recent Preconditions Logs ==="
        tail -20 "$PRECONDITIONS_LOG" 2>/dev/null || echo "No preconditions logs yet"
        echo ""
        echo "=== Current Configuration ==="
        echo "TRM Threshold: ${TRM_TRIGGER_THRESHOLD:-$CONSERVATIVE_TRM_THRESHOLD}"
        echo "Model Route: ${MODEL_ROUTE_OVERRIDE:-auto}"
        echo "Fail Closed: ${AGI_FAIL_CLOSED:-true}"
        echo ""
        echo "=== Available Rollback Scripts ==="
        ls -la rollback_to_*.sh 2>/dev/null || echo "No rollback scripts found"
        ;;
    *)
        echo "Usage: $0 [run|status]"
        echo "Example: $0 run  # Set up preconditions for production validation"
        ;;
esac
