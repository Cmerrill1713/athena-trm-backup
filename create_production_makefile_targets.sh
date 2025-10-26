#!/bin/bash
echo "⚙️  CREATING PRODUCTION MAKEFILE TARGETS"
echo "========================================================================"
echo ""

# Append to existing Makefile or create new targets file
cat > Makefile.production << 'MAKEFILE_TARGETS'
# Athena Production Makefile Targets
# Auto-generated production workflow

.PHONY: capability-registry gateway-denylist-deprecated ship-check canary-start canary-watch canary-promote canary-rollback metrics-snapshot

# ============================================================================
# 0) CATALOG REALITY
# ============================================================================

capability-registry:  ## Generate capability registry (CSV/JSON)
	@echo "📋 Generating capability registry..."
	@python3 generate_capability_registry.py
	@echo "✅ Registry: capability_registry.csv"

# ============================================================================
# 1) LOCK DOWN PUBLIC SURFACE
# ============================================================================

gateway-denylist-deprecated:  ## Block deprecated endpoints
	@echo "🚫 Generating gateway denylist..."
	@python3 create_gateway_denylist.py
	@echo "✅ Denylist: gateway_denylist.json"
	@echo "⚠️  Apply to gateway/nginx to activate"

# ============================================================================
# 2) HARD GATES (Contract + Perf)
# ============================================================================

ship-check:  ## Run all promotion gates before deploy
	@echo "🎯 Running ship-check gates..."
	@echo ""
	@echo "1. Contract tests (OpenAPI)..."
	@python3 test_final_comprehensive.py || exit 1
	@echo "✅ Contract tests passed"
	@echo ""
	@echo "2. Performance gates..."
	@./check_performance_gates.sh || exit 1
	@echo "✅ Performance gates passed"
	@echo ""
	@echo "3. RAG quality gates..."
	@./check_rag_gates.sh || exit 1
	@echo "✅ RAG gates passed"
	@echo ""
	@echo "🎉 ALL GATES PASSED - Ready to ship!"

# ============================================================================
# 3) CANARY DEPLOYMENT
# ============================================================================

canary-start:  ## Start canary at 5%
	@echo "🐤 Starting canary deployment (5%)..."
	@curl -X POST http://localhost:9113/canary/start -d '{"percentage": 5}'
	@echo "✅ Canary started at 5%"

canary-watch:  ## Watch canary metrics (run in separate terminal)
	@echo "👀 Watching canary metrics..."
	@watch -n 2 'curl -s http://localhost:9113/canary | jq .'

canary-promote:  ## Promote canary to next level
	@echo "⬆️  Promoting canary..."
	@curl -X POST http://localhost:9113/canary/promote
	@echo "✅ Canary promoted"

canary-rollback:  ## Emergency rollback
	@echo "🔙 ROLLING BACK CANARY!"
	@curl -X POST http://localhost:9113/canary/rollback
	@echo "✅ Rolled back to stable"

# ============================================================================
# 4) BASELINE SNAPSHOT
# ============================================================================

metrics-snapshot:  ## Capture baseline metrics
	@echo "📸 Capturing metrics snapshot..."
	@mkdir -p metrics/baselines
	@curl -s http://localhost:9113/metrics > metrics/baselines/router_$(date +%Y%m%d_%H%M%S).txt
	@curl -s http://localhost:8080/metrics > metrics/baselines/uai_$(date +%Y%m%d_%H%M%S).txt
	@curl -s http://localhost:8098/metrics > metrics/baselines/learning_$(date +%Y%m%d_%H%M%S).txt
	@echo "✅ Snapshot saved to metrics/baselines/"

# ============================================================================
# VALIDATION
# ============================================================================

validate-all:  ## Full system validation
	@echo "🔍 Running full system validation..."
	@python3 test_complete_expanded.py
	@echo "✅ Validation complete!"

# ============================================================================
# HELP
# ============================================================================

help-production:  ## Show production workflow
	@echo "🚀 ATHENA PRODUCTION WORKFLOW"
	@echo ""
	@echo "Pre-deploy:"
	@echo "  1. make capability-registry         - Catalog all features"
	@echo "  2. make gateway-denylist-deprecated - Block stale endpoints"
	@echo "  3. make ship-check                  - Run all gates"
	@echo ""
	@echo "Canary deploy:"
	@echo "  4. make canary-start    - Start at 5%"
	@echo "  5. make canary-watch    - Monitor (in separate terminal)"
	@echo "  6. make canary-promote  - Promote to 25%, 50%, 100%"
	@echo "  7. make metrics-snapshot - Save baseline"
	@echo ""
	@echo "Emergency:"
	@echo "  make canary-rollback - Instant rollback"

MAKEFILE_TARGETS

echo "✅ Created Makefile.production with all targets"
echo ""
echo "To use, add to main Makefile:"
echo "  include Makefile.production"
echo ""
echo "Or run directly:"
echo "  make -f Makefile.production help-production"

# Show help
make -f Makefile.production help-production

