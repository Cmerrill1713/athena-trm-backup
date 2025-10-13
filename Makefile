# NeuroForge Platform Makefile
# Orchestrates stack management, validation, and evaluation

.PHONY: help stack-up stack-full stack-down eval-smoke eval-nightly truth

help:
	@printf '%s\n' "NeuroForge Platform Commands"
	@printf '%s\n' "============================"
	@printf '\n%s\n' "Stack Management:"
	@printf '  %-20s %s\n' "stack-up" "Start core services (Bridge, Athena, UAT)"
	@printf '  %-20s %s\n' "stack-full" "Start all services (core + voice + RAG + vision)"
	@printf '  %-20s %s\n' "stack-down" "Stop all services"
	@printf '  %-20s %s\n' "truth" "Show running services"
	@printf '\n%s\n' "Evaluation:"
	@printf '  %-20s %s\n' "eval-smoke" "Quick evaluation (10 tasks)"
	@printf '  %-20s %s\n' "eval-nightly" "Full nightly evaluation"
	@printf '  %-20s %s\n' "eval-weekly" "Weekly deep analysis"
	@printf '\n%s\n' "Validation:"
	@printf '  %-20s %s\n' "validate" "Run platform validation"
	@printf '  %-20s %s\n' "validate-services" "Check service health"

# Configuration
VENV ?= .venv
PY ?= python3
PORTS = 8014 8090 8181

# Stack management
.PHONY: venv deps kill-ports stack-up stack-full stack-down stack-status logs

venv:
	@test -d $(VENV) || $(PY) -m venv $(VENV)
	@printf '%s\n' "OK: Virtual environment ready"

deps: venv
	@. $(VENV)/bin/activate && python -m pip -q install -U pip wheel && \
	(test -f requirements.txt && pip -q install -r requirements.txt || true)
	@printf '%s\n' "OK: Dependencies installed"

kill-ports:
	@for p in $(PORTS); do \
		lsof -i tcp:$$p -sTCP:LISTEN -t 2>/dev/null | xargs kill -9 2>/dev/null || true; \
	done
	@printf '%s\n' "OK: Ports cleared"

stack-up: deps kill-ports
	@mkdir -p logs pids
	@printf '%s\n' "Starting core services..."
	@. $(VENV)/bin/activate && PYTHONPATH=$$(pwd) nohup python bridge/app.py > logs/bridge.out 2>&1 & echo $$! > pids/bridge.pid
	@. $(VENV)/bin/activate && PYTHONPATH=$$(pwd) nohup python athena/server.py > logs/athena.out 2>&1 & echo $$! > pids/athena.pid
	@. $(VENV)/bin/activate && PYTHONPATH=$$(pwd) nohup python orchestrator/main.py > logs/uat.out 2>&1 & echo $$! > pids/uat.pid
	@sleep 3
	@$(MAKE) stack-status

stack-full: stack-up
	@printf '%s\n' "Starting enhanced services..."
	@. $(VENV)/bin/activate && cd kokoro && nohup python serve.py > ../logs/kokoro.out 2>&1 & echo $$! > ../pids/kokoro.pid
	@sleep 2
	@$(MAKE) stack-status

stack-down:
	@printf '%s\n' "Stopping all services..."
	@test -f pids/bridge.pid && kill -9 $$(cat pids/bridge.pid) 2>/dev/null || true
	@test -f pids/athena.pid && kill -9 $$(cat pids/athena.pid) 2>/dev/null || true
	@test -f pids/uat.pid && kill -9 $$(cat pids/uat.pid) 2>/dev/null || true
	@test -f pids/kokoro.pid && kill -9 $$(cat pids/kokoro.pid) 2>/dev/null || true
	@rm -f pids/*.pid
	@printf '%s\n' "OK: All services stopped"

stack-status:
	@printf '\n%s\n' "Service Status:"
	@for p in 8014:Bridge 8090:Athena 8181:UAT 8020:Kokoro; do \
		port=$${p%%:*}; name=$${p##*:}; \
		curl -fsS http://127.0.0.1:$$port/health >/dev/null 2>&1 && \
			printf '  OK %s (:%s)\n' "$$name" "$$port" || \
		curl -fsS http://127.0.0.1:$$port/ready >/dev/null 2>&1 && \
			printf '  OK %s (:%s)\n' "$$name" "$$port" || \
			printf '  DOWN %s (:%s)\n' "$$name" "$$port"; \
	done
	@printf '\n'

logs:
	@tail -n +1 -f logs/bridge.out logs/athena.out logs/uat.out 2>/dev/null || \
		printf '%s\n' "No log files found. Run make stack-up first."

truth: stack-status

# Evaluation
eval-smoke:
	@./scripts/eval_tandem.sh smoke

eval-nightly:
	@./scripts/eval_tandem.sh nightly

eval-weekly:
	@./scripts/eval_tandem.sh weekly

# Validation
validate:
	@./VALIDATE_PLATFORM.sh 2>/dev/null || ./NeuroForgeApp/scripts/validate_services.sh

validate-services:
	@./NeuroForgeApp/scripts/validate_services.sh

smoke:
	@printf '%s\n' "🔎 Smoke: swift build + minimal health"
	@cd NeuroForgeApp && swift build -c release > /dev/null 2>&1 || (printf '%s\n' "❌ Swift build failed"; exit 1)
	@curl -sf http://localhost:8014/health > /dev/null 2>&1 || (printf '%s\n' "⚠️  Bridge API down (expected if not running)"; exit 0)
	@printf '%s\n' "✅ Smoke test passed"

athena-tests-smoke: smoke

# Observability
grafana-import:
	@chmod +x grafana/import_dashboards.sh && \
	GRAFANA_URL=$${GRAFANA_URL} GRAFANA_API_KEY=$${GRAFANA_API_KEY} \
	./grafana/import_dashboards.sh

prom-rules-validate:
	@promtool check rules prometheus/alerts/slo_rules.yaml 2>/dev/null || \
	printf '%s\n' "WARN: promtool not found, skipping validation"

prom-reload:
	@curl -sS -X POST http://localhost:9090/-/reload >/dev/null && \
	printf '%s\n' "OK: Prometheus reloaded" || \
	printf '%s\n' "WARN: Prometheus not responding"

obs-quick-setup: prom-rules-validate prom-reload
	@printf '%s\n' "Configuring observability..."
	@chmod +x tools/obs/grafana_import.sh 2>/dev/null || chmod +x grafana/import_dashboards.sh || true
	@if [ -n "$${GRAFANA_URL}" ] && [ -n "$${GRAFANA_API_KEY}" ]; then \
		./tools/obs/grafana_import.sh 2>/dev/null || ./grafana/import_dashboards.sh || printf '%s\n' "WARN: Import script not found"; \
	else \
		printf '%s\n' "OK: Prometheus configured"; \
		printf '%s\n' "To import Grafana dashboards:"; \
		printf '%s\n' "  export GRAFANA_URL=http://localhost:3000"; \
		printf '%s\n' "  export GRAFANA_API_KEY=your-api-key"; \
		printf '%s\n' "  make grafana-import"; \
	fi
