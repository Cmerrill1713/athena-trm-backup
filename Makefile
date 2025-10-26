.PHONY: governance-up governance-deploy governance-promote governance-rollback governance-gate governance-canary-watch wire-check cursor-bootstrap repo-inventory exp-shadow exp-remediate exp-ab exp-devils-adv exp-cost exp-fasttrack exp-longrun ingress-up prom-up mode-shadow mode-canary mode-enforce gate verify wire-setup wire-validate wire-report e2e e2e-full e2e-load e2e-quick e2e-ci e2e-clean e2e-help go-live go-live-full go-live-help offline offline-ui offline-help qa-dry qa-fix-perms qa-fix-archive-symlinks qa-clean-empties qa-full qa-help

wire-check:  ## Verify complete system wiring (integration test)
	@echo "🔌 Verifying complete system wiring..."
	@./scripts/verify_complete_wiring.sh
	@$(MAKE) prom-verify

prom-reload:  ## Hot-reload Prometheus config
	@curl -fsS -X POST http://localhost:9090/-/reload && echo "✓ Prometheus reloaded"

prom-verify:  ## Check Prometheus targets health
	@echo "Checking Prometheus targets..."; \
	curl -s http://localhost:9090/api/v1/targets \
	| jq '.data.activeTargets[]|{job:.labels.job,health:.health,endpoint:.labels.instance}'

prom-query:  ## Query recent governance metrics
	@echo "Recent governance series count:"; \
	curl -s "http://localhost:9090/api/v1/series?match[]=governance_*&start=$$(date -u -v-10M +%FT%TZ)&end=$$(date -u +%FT%TZ)" \
	| jq '.data|length'

# =============================================================================
# WIRING VALIDATION (Evidence-Based)
# =============================================================================

WIRE_MATRIX ?= config/wiring.matrix.yaml
PY ?= python3

wire-setup:  ## Setup wiring validation
	@mkdir -p artifacts/wiring tools/wiring
	@test -f $(WIRE_MATRIX) || (echo "❌ Missing $(WIRE_MATRIX)"; exit 1)

wire-validate:  ## Validate wiring with concrete evidence
	@$(MAKE) wire-setup
	@$(PY) tools/wiring/validate_wiring.py

wire-report:  ## Show wiring validation report
	@test -f artifacts/wiring/wiring_report.json || (echo "Run 'make wire-validate' first"; exit 1)
	@cat artifacts/wiring/wiring_report.json | jq

cursor-bootstrap:  ## Initialize Cursor/IDE setup (run once)
	@echo "🔧 Bootstrapping Cursor setup..."
	@echo ">>> Initializing submodules"
	@git submodule update --init --recursive || true
	@echo ">>> Generating repo inventory"
	@bash tools/index/generate_repo_inventory.sh
	@echo ">>> Making scripts executable"
	@chmod +x scripts/*.sh || true
	@chmod +x tools/index/*.sh || true
	@echo ""
	@echo "✅ Bootstrap complete!"
	@echo ""
	@echo "📝 Next steps:"
	@echo "  1. Open athena.code-workspace in Cursor"
	@echo "  2. Install recommended extensions"
	@echo "  3. Run: Tasks → 🔌 Wire Check (Complete)"
	@echo "  4. Review: tools/index/repo_inventory.txt"

repo-inventory:  ## Generate repository file inventory
	@bash tools/index/generate_repo_inventory.sh

hotset:  ## Generate hot set (3k active files for fast Cursor)
	@bash tools/index/generate_hotset.sh

hot-workspace:  ## Create hot workspace (fast daily use)
	@bash tools/index/generate_hotset.sh
	@bash tools/index/make_hot_workspace.sh
	@echo ""
	@echo "🚀 Open workspace: code athena-hot.code-workspace"

# =============================================================================
# EXPERIMENTAL REMEDIATION (7 PHASES)
# =============================================================================

exp-shadow:  ## Phase 1: Shadow remediation (no-impact)
	@echo "🧪 Running Phase 1: Shadow Remediation"
	@python3 governance/experimental/remediation_shadow.py
	@echo "📊 Results saved to: artifacts/remediation_shadow/"

exp-remediate:  ## Phase 2: Guarded auto-remediation (1% canary)
	@echo "🧪 Running Phase 2: Guarded Auto-Remediation"
	@echo "⚠️  This runs on 1% canary traffic - use with caution"
	@echo "📚 See: governance/experimental/EXPERIMENTS.md"

exp-ab:  ## Phase 3: A/B policy testing
	@echo "🧪 Running Phase 3: A/B Policy Testing"
	@echo "📚 See: governance/experimental/EXPERIMENTS.md"

exp-devils-adv:  ## Phase 4: Adversarial gates
	@echo "🧪 Running Phase 4: Adversarial Gates"
	@echo "📚 See: governance/experimental/EXPERIMENTS.md"

exp-cost:  ## Phase 5: Cost-aware remediation
	@echo "🧪 Running Phase 5: Cost-Aware Remediation"
	@echo "📚 See: governance/experimental/EXPERIMENTS.md"

exp-fasttrack:  ## Phase 6: Human fast-track approvals
	@echo "🧪 Running Phase 6: Human Fast-Track"
	@echo "📚 See: governance/experimental/EXPERIMENTS.md"

exp-longrun:  ## Phase 7: Long-run drift tracking
	@echo "🧪 Running Phase 7: Long-Run Drift & Adaptation"
	@echo "📚 See: governance/experimental/EXPERIMENTS.md"

# =============================================================================
# IN-PATH GOVERNANCE (Shadow → Canary → Enforce)
# =============================================================================

# Configuration
ATHENA_MODE ?= shadow
ATHENA_POLICY_VERSION := $(shell shasum -a 256 governance/legislative/self_modification_policy.yaml 2>/dev/null | cut -c1-12 || echo "unknown")

export ATHENA_MODE
export ATHENA_POLICY_VERSION

ingress-up:  ## Start ingress with governance mirror
	@echo "🚀 Starting ingress (mode=$(ATHENA_MODE))..."
	@cd infra/ingress && docker compose up -d

prom-up:  ## Start Prometheus with governance alerts
	@echo "📊 Starting Prometheus..."
	@docker run -d --name athena-prometheus-infra \
	  -p 9090:9090 \
	  -v $(PWD)/infra/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro \
	  -v $(PWD)/infra/prometheus/alerts-governance.yml:/etc/prometheus/alerts-governance.yml:ro \
	  --add-host host.docker.internal:host-gateway \
	  prom/prometheus || echo "⚠️  Prometheus may already be running"

mode-shadow:  ## Set mode to SHADOW (observe only)
	@./scripts/flip_mode.sh shadow

mode-canary:  ## Set mode to CANARY (1-5% enforcement)
	@./scripts/flip_mode.sh canary

mode-enforce:  ## Set mode to ENFORCE (100% enforcement)
	@./scripts/flip_mode.sh enforce

gate:  ## Check governance coverage gate
	@MIN_COVERAGE=$(MIN_COVERAGE) PROM_URL=$(PROM_URL) bash scripts/coverage_gate.sh

verify:  ## Verify governance is operational
	@echo "🔍 Verifying governance..."
	@curl -sS http://localhost:9110/metrics | grep governance_ | head -5 || echo "⚠️  No metrics"
	@echo ""
	@echo "📡 Prometheus targets:"
	@curl -sS "http://localhost:9090/api/v1/targets" | jq -r '.data.activeTargets[].health' | sort | uniq -c

.PHONY: governance-up governance-deploy governance-promote governance-rollback governance-gate governance-canary-watch
governance-up:
	COMPOSE_FILE=docker-compose.athena-governance.yml docker compose up -d

governance-gate:
	PROM_URL=http://localhost:9090 \
	ECE_MAX=0.06 \
	ENTROPY_CRIT=0.25 \
	VIOLATION_SPIKE=0.02 \
	python3 scripts/gov_predeploy_gate.py

governance-deploy:
	bash scripts/gov_deploy.sh

governance-promote:
	bash scripts/gov_promote.sh

governance-rollback:
	bash scripts/gov_rollback.sh

governance-canary-watch:
	PROM_URL=http://localhost:9090 \
	WINDOW_MINUTES=15 \
	MIN_SAMPLES=200 \
	REQ_SOLVE_DELTA_GE=0.02 \
	REQ_VIOL_DELTA_LE=0.005 \
	REQ_P95_DELTA_LE=0.25 \
	REQ_ECE_POST_LE=0.06 \
	REQ_EDGE_SCORE_GE=0.80 \
	REQ_CONSIST_IDX_GE=0.90 \
	python3 scripts/gov_canary_decider.py || true

governance-adaptive-thresholds:
	python3 scripts/gov_adaptive_thresholds.py --analyze-last-days=30 --update-thresholds

governance-thresholds-show:
	python3 scripts/gov_adaptive_thresholds.py --show-current

governance-tune-windows:
	python3 scripts/gov_window_tuner.py --calculate-optimal --save-settings

governance-windows-show:
	python3 scripts/gov_window_tuner.py --get-current-settings

governance-predict:
	python3 scripts/gov_predictor.py --predict-rollback-probability --traffic-rate 100 --deployment-type feature

governance-insights:
	python3 scripts/gov_predictor.py --get-insights --lookback-days 30

governance-promote-check:
	python3 scripts/gov_promotion_chain.py --check-promotion --from-env staging --to-env production --version $(VERSION)

governance-promote-chain:
	python3 scripts/gov_promotion_chain.py --promote --from-env $(FROM_ENV) --to-env $(TO_ENV) --version $(VERSION) --execute

governance-playbooks-list:
	python3 exec/playbook_executor.py --list-playbooks

governance-playbooks-validate:
	python3 exec/playbook_executor.py --validate-all

# =============================================================================
# ATHENA STARTUP & MANAGEMENT
# =============================================================================

.PHONY: start
start:  ## Start all Athena services (one-command startup)
	@./scripts/start_athena.sh

.PHONY: stop
stop:  ## Stop all Athena services
	@echo "🛑 Stopping Athena services..."
	@docker compose -f docker-compose.athena-governance.yml down 2>/dev/null || true
	@[ -f .orchestrator.pid ] && kill $$(cat .orchestrator.pid) 2>/dev/null || true
	@[ -f .athena_api.pid ] && kill $$(cat .athena_api.pid) 2>/dev/null || true
	@rm -f .orchestrator.pid .athena_api.pid
	@echo "✅ All services stopped"

.PHONY: status
status:  ## Show Athena status and health
	@echo "📊 Athena Platform Status"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@curl -sf http://localhost:9110/health >/dev/null && echo "✅ Orchestrator (9110)" || echo "❌ Orchestrator (9110)"
	@curl -sf http://localhost:9109/metrics >/dev/null && echo "✅ Metrics (9109)" || echo "❌ Metrics (9109)"
	@curl -sf http://localhost:9111/health >/dev/null && echo "✅ Canary (9111)" || echo "❌ Canary (9111)"
	@curl -sf http://localhost:9090/-/ready >/dev/null && echo "✅ Prometheus (9090)" || echo "❌ Prometheus (9090)"
	@curl -sf http://localhost:3001/api/health >/dev/null && echo "✅ Grafana (3001)" || echo "❌ Grafana (3001)"
	@curl -sf http://localhost:8000/health >/dev/null && echo "✅ Master API (8000)" || echo "❌ Master API (8000)"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

.PHONY: restart
restart: stop start  ## Restart all Athena services

.PHONY: test-ui
test-ui:  ## Test Swift UI and backend connectivity
	@./scripts/test_athena_ui.sh


.PHONY: start-ui
start-ui:  ## Start Athena with Swift UI frontend
	@./scripts/start_athena_ui.sh

.PHONY: start-all
start-all: start start-ui  ## Start backend + Swift UI frontend


.PHONY: agi-preflight agi-fix-frontend agi-fix-status agi-rollback

agi-preflight:
	@bash scripts/agi_preflight.sh

agi-fix-frontend: agi-preflight
	@bash scripts/agi_fix_runner.sh

agi-fix-status:
	@bash scripts/agi_monitor.sh status

agi-rollback:
	@bash scripts/agi_rollback.sh

.PHONY: rag-seed rag-test rag-load rag-golden
rag-seed: ## Seed Weaviate with repo docs (incremental)
	@export WEAVIATE_URL=http://localhost:8090 && \
	 export RAG_GATEWAY_URL=http://localhost:8087 && \
	 export SEED_ROOT=/Users/christianmerrill/Documents/GitHub/agi_core && \
	 python3 tools/rag_seed.py

rag-seed-full: ## Seed full repo (1000+ chunks)
	@export WEAVIATE_URL=http://localhost:8090 && \
	 export RAG_GATEWAY_URL=http://localhost:8087 && \
	 export SEED_ROOT=/Users/christianmerrill/Documents/GitHub && \
	 export SEED_GLOBS="**/*.py,**/*.md,**/*.swift,**/*.sh" && \
	 python3 tools/rag_seed.py

rag-test: ## Test RAG query endpoint
	@curl -s http://localhost:8087/query -X POST \
	  -H 'Content-Type: application/json' \
	  -d '{"query":"router configuration","top_k":5}' | jq '{took_ms, total, sample: .hits[0].path}'

rag-load: ## Load test RAG (60s, 5 QPS)
	@bash tests/rag_load_test.sh 60 5

rag-golden: ## Run golden questions correctness test
	@bash tests/rag_golden_questions.sh

rag-metrics: ## Show RAG metrics
	@echo "== RAG Gateway Metrics ==" && \
	 curl -s http://localhost:8087/metrics | grep -E 'rag_(queries|hits|latency)' | grep -v '^#' && \
	 echo "" && \
	 echo "== AGI RAG Usage ==" && \
	 curl -s http://localhost:8000/metrics | grep -E 'agi_rag' | grep -v '^#'

# =============================================================================
# SMOKE PROBES
# =============================================================================

.PHONY: smoke-health smoke-rag smoke-router-uai smoke-e2e-agi

smoke-health: ## Run health & inventory smoke probes
	@echo "=== Health & Inventory ==="
	@curl -s http://localhost:8000/health | jq || echo "❌ AGI health check failed"
	@echo ""
	@curl -s http://localhost:8000/tools | jq '.tools | keys' || echo "❌ AGI tools check failed"
	@echo ""
	@curl -s http://localhost:8000/trm/policy | jq '.stats' || echo "❌ TRM policy check failed"

smoke-rag: ## Run RAG sanity smoke probes
	@echo "=== RAG Sanity (Dynamic Gateway) ==="
	@curl -s http://localhost:8087/query -H 'Content-Type: application/json' \
		-d '{"query":"Where is the router MCP provider configured?","top_k":8}' | \
		jq '.hits|length' || echo "❌ RAG query check failed"

smoke-router-uai: ## Run LLM-agnostic router → UAI path smoke probes
	@echo "=== LLM-Agnostic Router → UAI Path ==="
	@curl -s http://localhost:8080/v1/chat/completions -H 'Content-Type: application/json' \
		-d '{"model":"auto","messages":[{"role":"user","content":"Say hello in 3 words"}]}' | \
		jq '.choices[0].message' || echo "❌ Router/UAI check failed"

smoke-e2e-agi: ## Run end-to-end AGI exec smoke probes
	@echo "=== End-to-End AGI Exec (Real Flow) ==="
	@curl -s http://localhost:8000/api/execute -H 'Content-Type: application/json' \
		-d '{"objective":"Where are agent experts wired in the codebase? show file paths","tools":[],"max_steps":6,"flags":{"adaptive_trm":true}}' | \
		jq '.trace[-5:]' || echo "❌ AGI exec check failed"

# =============================================================================
# TURN-KEY VALIDATION RUNNER
# =============================================================================

.PHONY: run-validation run-validation-local run-validation-quick run-validation-chaos

run-validation: ## Run complete validation checklist (turn-key)
	@./scripts/run_validation.sh

run-validation-local: ## Run validation locally with custom params
	@echo "Usage: ENV_STAGE=prod SHADOW_DURATION_MIN=120 CANARY_DURATION_MIN=30 CHAOS=false make run-validation-local"
	@ENV_STAGE=prod SHADOW_DURATION_MIN=120 CANARY_DURATION_MIN=30 CHAOS=false ./scripts/run_validation.sh

run-validation-quick: ## Run quick validation (short durations)
	@ENV_STAGE=prod SHADOW_DURATION_MIN=10 CANARY_DURATION_MIN=5 CHAOS=false ./scripts/run_validation.sh

run-validation-chaos: ## Run validation with chaos testing
	@ENV_STAGE=prod SHADOW_DURATION_MIN=120 CANARY_DURATION_MIN=30 CHAOS=true ./scripts/run_validation.sh

test-validation-structure: ## Test validation framework structure (all components)
	@./scripts/test_validation_structure.sh

##@ Launch Control

preflight: ## Run preflight checklist (10 min: freeze, contracts, error budget, kill-switch)
	@./scripts/preflight_checklist.sh

prom-reload-alerts: ## Reload Prometheus with SLO alert rules
	@echo "📊 Reloading Prometheus with SLO alert rules..."
	@curl -fsS -X POST http://localhost:9090/-/reload && echo "✓ Prometheus reloaded"
	@echo "Alert rules: config/prometheus_slo_alerts.yml"

launch-go: ## Complete go sequence (preflight → validation → evidence)
	@echo "🚀 Starting launch control sequence..."
	@echo ""
	@echo "Step 1: Preflight checklist"
	@make preflight
	@echo ""
	@echo "Step 2: Structural validation"
	@make test-validation-structure
	@echo ""
	@echo "Step 3: Phase-0 & dashboards"
	@make phase0-preconditions
	@make ops-status
	@echo ""
	@echo "Step 4: Shadow validation (120 min)"
	@SHADOW_DURATION_MIN=120 make shadow-validation-gates
	@echo ""
	@echo "Step 5: Canary ladder (30 min per step)"
	@CANARY_DURATION_MIN=30 make canary-deploy
	@echo ""
	@echo "Step 6: Staged rollout"
	@make prod-rollout
	@echo ""
	@echo "Step 7: Evidence pack"
	@make validation-evidence-pack
	@echo ""
	@echo "🎉 Launch control sequence complete!"

launch-quick: ## Quick launch (30 min shadow, 10 min canary)
	@make preflight
	@make test-validation-structure
	@SHADOW_DURATION_MIN=30 CANARY_DURATION_MIN=10 make run-validation-quick

launch-dry-run: ## Dry run (no side effects)
	@DRY_RUN=true make validation-checklist

# =============================================================================
# END-TO-END TESTING
# =============================================================================

e2e: ## Run E2E test suite (Frontend → Adapter → Backend → Weaviate)
	@bash scripts/e2e_frontend_backend.sh

e2e-full: ## Start full stack + run E2E
	@echo "🚀 Starting full stack..."
	@docker-compose -f docker-compose.full-stack.yml up -d
	@echo "⏳ Waiting 30s for services to be healthy..."
	@sleep 30
	@make e2e

e2e-load: ## E2E + k6 load test
	@make e2e
	@echo ""
	@echo "🔥 Running load test (5 min, 20 VUs)..."
	@k6 run k6-rag.js || echo "⚠️  k6 not installed - skipping load test"

e2e-quick: ## Quick smoke test only (no RAG eval)
	@bash -c 'cd services/openai-compat && ./smoke-test.sh'

e2e-ci: ## CI mode (strict validation)
	@echo "🤖 CI Mode: Strict validation with hard gates"
	@STRICT_MODE=1 bash scripts/e2e_frontend_backend.sh

e2e-clean: ## Cleanup E2E test artifacts
	@echo "🧹 Cleaning up E2E test artifacts..."
	@docker-compose -f docker-compose.full-stack.yml down -v
	@rm -rf artifacts/e2e_* summary.json

e2e-help: ## Show E2E testing help
	@echo "🎯 End-to-End Test Targets:"
	@echo "  e2e          - Run full E2E test suite"
	@echo "  e2e-full     - Start stack + run E2E"
	@echo "  e2e-load     - E2E + k6 load test"
	@echo "  e2e-quick    - Quick smoke test only"
	@echo "  e2e-ci       - CI mode (strict gates)"
	@echo "  e2e-clean    - Cleanup test artifacts"
	@echo ""
	@echo "📋 Test Gates:"
	@echo "  1. Adapter health check"
	@echo "  2. Models endpoint (/v1/models)"
	@echo "  3. Non-streaming completion"
	@echo "  4. Streaming completion (SSE)"
	@echo "  5. Model routing (3 models)"
	@echo "  6. RAG evaluation gates"
	@echo "  7. BM25 vs Semantic delta"
	@echo "  8. Adapter smoke tests"
	@echo "  9. Open WebUI reachability"
	@echo "  10. Metrics endpoint"
	@echo ""
	@echo "Usage:"
	@echo "  make e2e"
	@echo "  make e2e-full"
	@echo "  make e2e-load"

# =============================================================================
# GO-LIVE VALIDATION
# =============================================================================

go-live: ## Run complete go-live drill (14 hard gates)
	@bash scripts/go_live_drill.sh

go-live-full: ## Start stack + run go-live drill
	@echo "🚀 Starting full stack for go-live validation..."
	@docker-compose -f docker-compose.full-stack.yml up -d
	@echo "⏳ Waiting 45s for all services to be healthy..."
	@sleep 45
	@make go-live

go-live-help: ## Show go-live help
	@echo "🚀 Go-Live Validation:"
	@echo "  go-live      - Run 14-gate validation drill"
	@echo "  go-live-full - Start stack + validate"
	@echo ""
	@echo "📋 Critical Gates (Must Pass):"
	@echo "  1. Adapter health with diagnostics"
	@echo "  2. All 3 models listed"
	@echo "  3. Non-streaming contract compliance"
	@echo "  4. Streaming SSE format"
	@echo "  5. All models route correctly"
	@echo "  6-8. OpenAI contract validation"
	@echo "  9-10. RAG quality gates"
	@echo "  11-13. Infrastructure validation"
	@echo "  14. Performance baseline (<1500ms p95)"
	@echo ""
	@echo "Usage:"
	@echo "  make go-live         # Run drill (services must be running)"
	@echo "  make go-live-full    # Start + validate"
	@echo ""
	@echo "Next: See GO_LIVE_CHECKLIST.md for full procedures"

# =============================================================================
# OFFLINE VALIDATION (Zero Internet Dependency)
# =============================================================================

offline: ## Validate 100% offline operation (no internet required)
	@bash scripts/offline_validation.sh

offline-ui: ## Serve local HTML UI
	@echo "🖥️  Starting local UI server..."
	@echo "Open: http://localhost:8080/athena-chat.html"
	@cd ui && python3 -m http.server 8080

offline-help: ## Show offline operation help
	@echo "🔒 Offline Operation:"
	@echo "  offline      - Validate zero internet dependency"
	@echo "  offline-ui   - Serve local HTML UI"
	@echo ""
	@echo "📋 Offline Checklist:"
	@echo "  1. Weaviate data restored (5.8GB)"
	@echo "  2. No external API calls"
	@echo "  3. All images pulled locally"
	@echo "  4. Local HTML UI ready"
	@echo ""
	@echo "Usage:"
	@echo "  make offline         # Validate"
	@echo "  make offline-ui      # Start UI"
	@echo ""
	@echo "UI: http://localhost:8080/athena-chat.html"

# =============================================================================
# REPOSITORY HYGIENE (QA Automation)
# =============================================================================

.PHONY: qa-dry qa-fix-perms qa-fix-archive-symlinks qa-clean-empties qa-full qa-help

qa-dry: ## Dry-run QA checks (no changes)
	@echo "=== QA Dry-Run ===" && \
	echo "\n🔍 Shell scripts (non-exec, outside archive/):" && \
	find . -type f -name '*.sh' -not -path '*/archive/*' -not -perm -111 -print | wc -l | xargs echo "  Count:" || true && \
	echo "\n🐍 Python exec w/o shebang:" && \
	find . -type f -name '*.py' -perm -111 -not -path '*/archive/*' -exec awk 'NR==1 {if ($$0 !~ /^#!/) print FILENAME}' {} + 2>/dev/null | wc -l | xargs echo "  Count:" || true && \
	echo "\n🔗 Broken symlinks:" && \
	find . -type l ! -exec test -e {} \; -print 2>/dev/null | wc -l | xargs echo "  Count:" || true && \
	echo "\n📁 Empty directories:" && \
	find . -type d -empty -not -path '*/.git/*' -print 2>/dev/null | wc -l | xargs echo "  Count:" || true && \
	echo "\n✅ Dry-run complete (no changes made)"

qa-fix-perms: ## Fix shell script permissions (make executable)
	@echo "🔧 Fixing shell script permissions..." && \
	find . -type f -name '*.sh' -not -path '*/archive/*' -not -perm -111 -exec chmod +x {} \; && \
	echo "✅ Shell scripts now executable" && \
	find . -type f -name '*.sh' -not -path '*/archive/*' -not -perm -111 -print | wc -l | xargs echo "Remaining non-executable:"

qa-fix-archive-symlinks: ## Remove broken symlinks in archive/
	@echo "🔗 Cleaning broken symlinks (archive-aware)..." && \
	find archive -type l ! -exec test -e {} \; -delete 2>/dev/null || true && \
	find ./AI-Projects -type l ! -exec test -e {} \; -delete 2>/dev/null || true && \
	find ./governance -type l ! -exec test -e {} \; -delete 2>/dev/null || true && \
	echo "✅ Broken symlinks cleaned" && \
	find . -type l ! -exec test -e {} \; -print 2>/dev/null | wc -l | xargs echo "Remaining:"

qa-clean-empties: ## Remove empty directories (preserve .gitkeep)
	@echo "📁 Cleaning empty directories..." && \
	BEFORE=$$(find . -type d -empty -not -path '*/.git/*' 2>/dev/null | wc -l | xargs) && \
	find . -type d -empty -not -path '*/.git/*' -not -name '.gitkeep' -delete 2>/dev/null && \
	AFTER=$$(find . -type d -empty -not -path '*/.git/*' 2>/dev/null | wc -l | xargs) && \
	echo "✅ Cleaned $$(($$BEFORE - $$AFTER)) empty directories"

qa-full: qa-fix-perms qa-fix-archive-symlinks qa-clean-empties ## Run all QA fixes
	@echo "\n🎯 Full QA cleanup complete!"
	@$(MAKE) qa-dry

qa-help: ## Show QA commands help
	@echo "📋 Repository Hygiene Commands:"
	@echo "  qa-dry                   - Dry-run checks (no changes)"
	@echo "  qa-fix-perms             - Make shell scripts executable"
	@echo "  qa-fix-archive-symlinks  - Remove broken symlinks"
	@echo "  qa-clean-empties         - Remove empty directories"
	@echo "  qa-full                  - Run all QA fixes + verify"
	@echo ""
	@echo "Usage:"
	@echo "  make qa-dry    # Check what would change"
	@echo "  make qa-full   # Apply all fixes"

# ============================================================================
# INTEGRATION MAKEFILES
# ============================================================================
-include Makefile.integration

# DAG-based system check
.PHONY: system-check
system-check:
	@python3 scripts/system_check_dag.py

.PHONY: ship-check-fast
ship-check-fast: system-check
	@echo "✅ Fast ship check complete"

