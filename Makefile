.PHONY: governance-up governance-deploy governance-promote governance-rollback governance-gate governance-canary-watch wire-check cursor-bootstrap repo-inventory exp-shadow exp-remediate exp-ab exp-devils-adv exp-cost exp-fasttrack exp-longrun ingress-up prom-up mode-shadow mode-canary mode-enforce gate verify wire-setup wire-validate wire-report

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

