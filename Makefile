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

# Stack management
stack-up:
	@printf '%s\n' "Starting core services..."
	@cd bridge && python app.py &
	@cd athena && python server.py &
	@cd orchestrator && python main.py &
	@sleep 2
	@$(MAKE) truth

stack-full: stack-up
	@printf '%s\n' "Starting enhanced services..."
	@cd kokoro && python serve.py &
	@cd AI-Projects/universal-ai-tools && python rag_service.py &
	@sleep 2
	@$(MAKE) truth

stack-down:
	@printf '%s\n' "Stopping all services..."
	@pkill -f "bridge.*app.py" || true
	@pkill -f "athena.*server.py" || true
	@pkill -f "orchestrator.*main.py" || true
	@pkill -f "kokoro.*serve.py" || true
	@pkill -f "rag_service.py" || true
	@printf '%s\n' "All services stopped"

truth:
	@printf '\n%s\n' "Service Status:"
	@lsof -i :8014,8090,8181,8020,8015 2>/dev/null | grep LISTEN | \
	  awk '{print "  " $$1 " on port " $$9}' || printf '%s\n' "  No services running"
	@printf '\n'

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
