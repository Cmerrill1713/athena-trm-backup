.PHONY: governance-up governance-deploy governance-promote governance-rollback governance-gate governance-canary-watch wire-check cursor-bootstrap repo-inventory exp-shadow exp-remediate exp-ab exp-devils-adv exp-cost exp-fasttrack exp-longrun

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
	@python governance/experimental/remediation_shadow.py
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
