#!/bin/bash
# CI/CD hooks for production pipeline integration
# Post-deploy validation, automated testing, and rollback triggers

set -euo pipefail

SCRIPT_DIR="/Users/christianmerrill/Documents/GitHub"
LOG_DIR="$SCRIPT_DIR/logs"
CICD_LOG="$LOG_DIR/cicd_hooks.log"

# Configuration
DEPLOYMENT_ID=${1:-"$(date +%Y%m%d_%H%M%S)"}
HOOK_TYPE=${2:-"post-deploy"}
ENVIRONMENT=${3:-"production"}

# Ensure log directory exists
mkdir -p "$LOG_DIR"

echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') - CI/CD Hook: $HOOK_TYPE for deployment $DEPLOYMENT_ID" >> "$CICD_LOG"

cd "$SCRIPT_DIR"

# Post-deploy validation
post_deploy_validation() {
    echo "🔍 Running post-deploy validation..." >> "$CICD_LOG"
    
    # 1. System smoke test
    echo "  - Running system smoke test..." >> "$CICD_LOG"
    if ! make system-smoke >> "$CICD_LOG" 2>&1; then
        echo "❌ System smoke test failed" >> "$CICD_LOG"
        return 1
    fi
    
    # 2. RAG golden test
    echo "  - Running RAG golden test..." >> "$CICD_LOG"
    if ! make rag-golden >> "$CICD_LOG" 2>&1; then
        echo "❌ RAG golden test failed" >> "$CICD_LOG"
        return 1
    fi
    
    # 3. TRM policy validation
    echo "  - Validating TRM policy..." >> "$CICD_LOG"
    local trm_status=$(curl -s "http://localhost:8000/trm/policy" | jq -r '.status' 2>/dev/null || echo "error")
    if [ "$trm_status" != "ok" ]; then
        echo "❌ TRM policy validation failed" >> "$CICD_LOG"
        return 1
    fi
    
    # 4. Human validation spot check
    echo "  - Running human validation spot check..." >> "$CICD_LOG"
    if ! ./scripts/human_validation.sh 10 spot_check >> "$CICD_LOG" 2>&1; then
        echo "❌ Human validation failed" >> "$CICD_LOG"
        return 1
    fi
    
    echo "✅ Post-deploy validation passed" >> "$CICD_LOG"
    return 0
}

# Pre-deploy checks
pre_deploy_checks() {
    echo "🔍 Running pre-deploy checks..." >> "$CICD_LOG"
    
    # 1. Environment validation
    echo "  - Validating environment..." >> "$CICD_LOG"
    if [ "$ENVIRONMENT" = "production" ]; then
        # Check if staging passed
        if ! curl -sf "http://localhost:8001/health" >/dev/null 2>&1; then
            echo "❌ Staging environment not ready" >> "$CICD_LOG"
            return 1
        fi
    fi
    
    # 2. Dependency checks
    echo "  - Checking dependencies..." >> "$CICD_LOG"
    local deps=("http://localhost:8000" "http://localhost:8087" "http://localhost:8420" "http://localhost:8090")
    for dep in "${deps[@]}"; do
        if ! curl -sf "$dep/health" >/dev/null 2>&1; then
            echo "❌ Dependency $dep not ready" >> "$CICD_LOG"
            return 1
        fi
    done
    
    # 3. Resource checks
    echo "  - Checking system resources..." >> "$CICD_LOG"
    local disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 90 ]; then
        echo "❌ Disk usage too high: ${disk_usage}%" >> "$CICD_LOG"
        return 1
    fi
    
    echo "✅ Pre-deploy checks passed" >> "$CICD_LOG"
    return 0
}

# Automated rollback trigger
trigger_rollback() {
    local reason="$1"
    
    echo "🚨 Triggering automated rollback: $reason" >> "$CICD_LOG"
    
    # 1. Immediate kill switches
    echo "  - Activating kill switches..." >> "$CICD_LOG"
    export TRM_TRIGGER_THRESHOLD=1.0
    export MODEL_ROUTE_OVERRIDE="fast-only"
    
    # 2. Rollback deployment
    echo "  - Rolling back deployment..." >> "$CICD_LOG"
    make prod-rollback >> "$CICD_LOG" 2>&1
    
    # 3. Validate rollback
    echo "  - Validating rollback..." >> "$CICD_LOG"
    sleep 30  # Wait for rollback to complete
    
    if ! make system-smoke >> "$CICD_LOG" 2>&1; then
        echo "❌ Rollback validation failed" >> "$CICD_LOG"
        # Alert operations team
        echo "🚨 CRITICAL: Rollback validation failed for deployment $DEPLOYMENT_ID" >> "$CICD_LOG"
        return 1
    fi
    
    echo "✅ Rollback completed successfully" >> "$CICD_LOG"
    return 0
}

# Shadow traffic validation
shadow_validation() {
    echo "🔍 Running shadow traffic validation..." >> "$CICD_LOG"
    
    # Start shadow traffic for 30 minutes
    echo "  - Starting shadow traffic..." >> "$CICD_LOG"
    timeout 1800 ./scripts/traffic_shadow.sh 5 start 30 >> "$CICD_LOG" 2>&1 &
    local shadow_pid=$!
    
    # Wait for shadow to complete
    wait $shadow_pid
    local shadow_exit_code=$?
    
    if [ $shadow_exit_code -eq 0 ]; then
        echo "✅ Shadow traffic validation passed" >> "$CICD_LOG"
        return 0
    else
        echo "❌ Shadow traffic validation failed" >> "$CICD_LOG"
        return 1
    fi
}

# Canary promotion check
canary_promotion_check() {
    local canary_percentage="$1"
    
    echo "🚦 Checking canary promotion eligibility at ${canary_percentage}%..." >> "$CICD_LOG"
    
    # Check SLOs
    local error_rate=$(curl -s "http://localhost:9093/metrics" | grep 'agi_requests_total{outcome="error"}' | awk '{print $2}' 2>/dev/null || echo "0")
    local p95_latency=$(curl -s "http://localhost:9093/metrics" | grep 'agi_request_duration_ms_bucket' | awk '{print $2}' | tail -1 2>/dev/null || echo "0")
    
    # SLO thresholds
    if (( $(echo "$error_rate > 2.0" | bc -l) )); then
        echo "❌ Error rate too high: ${error_rate}%" >> "$CICD_LOG"
        return 1
    fi
    
    if (( $(echo "$p95_latency > 2000" | bc -l) )); then
        echo "❌ Latency too high: ${p95_latency}ms" >> "$CICD_LOG"
        return 1
    fi
    
    # Check golden test score
    local golden_score=$(make rag-golden 2>/dev/null | grep "Passed" | awk '{print $2}' | cut -d'/' -f1 || echo "0")
    if [ "$golden_score" -lt 8 ]; then
        echo "❌ Golden test score too low: ${golden_score}/10" >> "$CICD_LOG"
        return 1
    fi
    
    echo "✅ Canary promotion check passed" >> "$CICD_LOG"
    return 0
}

# Main hook execution
case "$HOOK_TYPE" in
    "pre-deploy")
        pre_deploy_checks
        ;;
    "post-deploy")
        post_deploy_validation
        ;;
    "shadow-validation")
        shadow_validation
        ;;
    "canary-promotion")
        canary_promotion_check "${4:-10}"
        ;;
    "rollback")
        trigger_rollback "${4:-"automated"}"
        ;;
    "full-pipeline")
        echo "🚀 Running full CI/CD pipeline..." >> "$CICD_LOG"
        pre_deploy_checks || exit 1
        post_deploy_validation || trigger_rollback "post-deploy validation failed"
        shadow_validation || trigger_rollback "shadow validation failed"
        echo "✅ Full CI/CD pipeline completed" >> "$CICD_LOG"
        ;;
    *)
        echo "Usage: $0 <deployment_id> <hook_type> [environment] [additional_params]"
        echo "Hook types: pre-deploy, post-deploy, shadow-validation, canary-promotion, rollback, full-pipeline"
        echo "Example: $0 20241218_143022 post-deploy production"
        ;;
esac
