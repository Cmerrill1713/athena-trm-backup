#!/bin/bash
set -euo pipefail

# ============================================================================
# ATHENA VALIDATE & RECOVER
# Complete health check with auto-recovery
# Run at boot or nightly to ensure system stability
# ============================================================================

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
LOG_FILE="artifacts/validation_$(date +%Y%m%d_%H%M%S).log"
SNAPSHOT_DIR="artifacts/snapshots"
RECOVERY_MODE="${RECOVERY_MODE:-auto}"  # auto, manual, none

# Initialize
mkdir -p artifacts "$SNAPSHOT_DIR"
exec > >(tee -a "$LOG_FILE") 2>&1

echo -e "${BLUE}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 ATHENA VALIDATE & RECOVER"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${NC}"
echo "Timestamp: $(date)"
echo "Recovery mode: $RECOVERY_MODE"
echo "Log file: $LOG_FILE"
echo ""

ISSUES_FOUND=0
ISSUES_FIXED=0

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

check_and_recover() {
    local check_name="$1"
    local check_command="$2"
    local recovery_command="${3:-}"
    
    echo -e "${BLUE}Checking: ${check_name}${NC}"
    
    if eval "$check_command" >/dev/null 2>&1; then
        echo -e "${GREEN}  ✅ PASS${NC}"
        return 0
    else
        echo -e "${YELLOW}  ⚠️  FAIL${NC}"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
        
        if [ -n "$recovery_command" ] && [ "$RECOVERY_MODE" = "auto" ]; then
            echo -e "${YELLOW}  🔧 Auto-recovering...${NC}"
            if eval "$recovery_command"; then
                echo -e "${GREEN}  ✅ RECOVERED${NC}"
                ISSUES_FIXED=$((ISSUES_FIXED + 1))
                return 0
            else
                echo -e "${RED}  ❌ Recovery failed${NC}"
                return 1
            fi
        else
            if [ -n "$recovery_command" ]; then
                echo -e "${YELLOW}  💡 Manual fix: ${recovery_command}${NC}"
            fi
            return 1
        fi
    fi
}

# ============================================================================
# 1. DOCKER & ENVIRONMENT
# ============================================================================

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  Docker & Environment"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check_and_recover \
    "Docker daemon" \
    "docker version" \
    "open -a Docker && sleep 30"

check_and_recover \
    "Environment variables" \
    "[ \"\$ATHENA_NO_CLOUD\" = \"1\" ]" \
    "export ATHENA_NO_CLOUD=1 && export ATHENA_ENV=production"

check_and_recover \
    "Required directories" \
    "[ -d volumes/weaviate_data ] && [ -d artifacts ]" \
    "mkdir -p volumes/weaviate_data volumes/ollama artifacts seeds"

# ============================================================================
# 2. CORE SERVICES
# ============================================================================

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  Core Services"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check_and_recover \
    "Weaviate health" \
    "curl -sf http://127.0.0.1:8090/v1/.well-known/ready | jq -e '.status == \"ok\"'" \
    "docker-compose restart athena-weaviate && sleep 20"

check_and_recover \
    "Router health" \
    "curl -sf http://127.0.0.1:9113/health" \
    "docker-compose restart athena-router && sleep 10"

check_and_recover \
    "UAI health" \
    "curl -sf http://127.0.0.1:8080/health" \
    "docker-compose restart uai && sleep 10"

check_and_recover \
    "Prometheus health" \
    "curl -sf http://127.0.0.1:9090/-/healthy" \
    "docker-compose restart athena-prometheus && sleep 10"

# ============================================================================
# 3. KNOWLEDGE BASE
# ============================================================================

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  Knowledge Base"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

DOC_COUNT=$(curl -sf http://127.0.0.1:8090/v1/graphql \
  -H 'Content-Type: application/json' \
  -d '{"query":"{ Aggregate { DocsV2 { meta { count } } } }"}' 2>/dev/null | jq -r '.data.Aggregate.DocsV2[0].meta.count // 0')

echo "DocsV2 count: $DOC_COUNT"

check_and_recover \
    "Knowledge corpus populated" \
    "[ \"$DOC_COUNT\" -gt 0 ]" \
    "echo 'Restore volumes/weaviate_data from backup' && false"  # Manual recovery needed

# ============================================================================
# 4. END-TO-END FUNCTIONALITY
# ============================================================================

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  End-to-End Functionality"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check_and_recover \
    "RAG chat completion" \
    "curl -sf http://127.0.0.1:8080/v1/chat/completions \
        -H 'Content-Type: application/json' \
        -d '{\"model\":\"athena-chat\",\"messages\":[{\"role\":\"user\",\"content\":\"What is TRM?\"}],\"stream\":false}' \
        | jq -e '.choices[0].message.content | length > 10'" \
    "docker-compose restart uai athena-router && sleep 15"

# ============================================================================
# 5. COPILOT (DEV DAEMON)
# ============================================================================

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5️⃣  Copilot (Dev Daemon)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if docker ps | grep -q athena-devd; then
    check_and_recover \
        "Dev daemon health" \
        "curl -sf http://127.0.0.1:8765/healthz | jq -e '.status == \"healthy\"'" \
        "docker-compose restart athena-devd && sleep 10"
else
    echo -e "${YELLOW}  ⚠️  Dev daemon not running (optional service)${NC}"
fi

# ============================================================================
# 6. OBSERVABILITY
# ============================================================================

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6️⃣  Observability"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if docker ps | grep -q athena-prometheus; then
    check_and_recover \
        "Prometheus scraping" \
        "curl -sf 'http://127.0.0.1:9090/api/v1/targets' | jq -e '.data.activeTargets | length > 0'" \
        "docker-compose restart athena-prometheus && sleep 10"
else
    echo -e "${YELLOW}  ⚠️  Prometheus not running${NC}"
fi

# ============================================================================
# 7. DRIFT DETECTION
# ============================================================================

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "7️⃣  Drift Detection"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Compare current doc count against baseline
BASELINE_FILE="$SNAPSHOT_DIR/baseline_doc_count.txt"
if [ -f "$BASELINE_FILE" ]; then
    BASELINE_COUNT=$(cat "$BASELINE_FILE")
    DRIFT_PCT=$(echo "scale=2; ($DOC_COUNT - $BASELINE_COUNT) / $BASELINE_COUNT * 100" | bc 2>/dev/null || echo "0")
    
    echo "Current docs: $DOC_COUNT"
    echo "Baseline docs: $BASELINE_COUNT"
    echo "Drift: ${DRIFT_PCT}%"
    
    if [ "${DRIFT_PCT%.*}" -gt 10 ]; then
        echo -e "${YELLOW}  ⚠️  Significant drift detected (>${DRIFT_PCT}%)${NC}"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
    else
        echo -e "${GREEN}  ✅ Minimal drift (<10%)${NC}"
    fi
else
    echo "No baseline found. Creating baseline now..."
    echo "$DOC_COUNT" > "$BASELINE_FILE"
    echo -e "${GREEN}  ✅ Baseline created: $DOC_COUNT docs${NC}"
fi

# ============================================================================
# SUMMARY
# ============================================================================

echo ""
echo -e "${BLUE}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 VALIDATION SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${NC}"
echo ""
echo "Issues found: $ISSUES_FOUND"
echo "Issues auto-fixed: $ISSUES_FIXED"
echo "Unresolved: $((ISSUES_FOUND - ISSUES_FIXED))"
echo ""

# Save results for alert system
cat > artifacts/validation_latest.json << RESULTS
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "issues_found": $ISSUES_FOUND,
  "issues_fixed": $ISSUES_FIXED,
  "doc_count": ${DOC_COUNT:-0},
  "drift_pct": 0
}
RESULTS

if [ $ISSUES_FOUND -eq 0 ]; then
    echo -e "${GREEN}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🎉 ALL SYSTEMS HEALTHY! 🎉"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${NC}"
    echo ""
    echo "Athena is running perfectly!"
    echo "Log saved to: $LOG_FILE"
    echo ""
    
    # Send success alert
    if [ -x "scripts/alert_system.sh" ]; then
        ./scripts/alert_system.sh
    fi
    
    exit 0
elif [ $ISSUES_FIXED -eq $ISSUES_FOUND ]; then
    echo -e "${GREEN}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔧 ALL ISSUES AUTO-RECOVERED! 🔧"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${NC}"
    echo ""
    echo "Found $ISSUES_FOUND issues and fixed them all!"
    echo "System is now healthy."
    echo ""
    
    # Send recovery alert
    if [ -x "scripts/alert_system.sh" ]; then
        ./scripts/alert_system.sh
    fi
    
    exit 0
else
    echo -e "${YELLOW}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "⚠️  MANUAL INTERVENTION NEEDED ⚠️"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${NC}"
    echo ""
    echo "Found $ISSUES_FOUND issues, fixed $ISSUES_FIXED"
    echo "Please review log: $LOG_FILE"
    echo ""
    
    # Send failure alert
    if [ -x "scripts/alert_system.sh" ]; then
        ./scripts/alert_system.sh
    fi
    
    exit 1
fi

