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
