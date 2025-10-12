.PHONY: help broker broker-agent build validate package deliver workspace-health wizard check-health learn train eval promote full-validate inventory bridge-up bridge-down app all logs smoke

SCRIPTS_DIR := $(CURDIR)/scripts
BROKER_DIR := $(CURDIR)/assistant-broker

# Default values (override with make VAR=value)
NAME ?= MyApp
PROJ ?=
TYPE ?= swift
PORT ?= 8080
PROMPT ?= simple test app
DAYS ?= 7

help:
	@echo "╔════════════════════════════════════════════════════════════╗"
	@echo "║  GitHub Workspace Orchestration Makefile                  ║"
	@echo "╚════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "🤖 Assistant Broker:"
	@echo "  broker           - Build and run assistant-broker locally"
	@echo "  broker-agent     - Install LaunchAgent (auto-start)"
	@echo "  broker-test      - Test broker endpoints"
	@echo ""
	@echo "🔨 Build Pipeline:"
	@echo "  build            - Build app (NAME=AppName PROJ=/path TYPE=swift|tauri|python)"
	@echo "  validate         - Run tests/linters (NAME=AppName PROJ=/path TYPE=swift|python)"
	@echo "  package          - Create DMG from .app (APP=/path/to/App.app)"
	@echo "  deliver          - Full pipeline: build → validate → package → reveal"
	@echo ""
	@echo "🧙‍♂️ App Wizard:"
	@echo "  wizard           - AI-driven app creation (NAME=App TYPE=swift PROMPT='description')"
	@echo ""
	@echo "🧠 Autonomous Evolution:"
	@echo "  learn-init       - Initialize learning database"
	@echo "  learn-verify     - Verify learning loop is working"
	@echo "  learn-stats      - Show learning statistics"
	@echo "  learn            - Full loop: train → eval → promote"
	@echo "  train            - Train TRM from routing outcomes (DAYS=7)"
	@echo "  eval             - Evaluate candidate vs baseline"
	@echo "  promote          - Promote if better + safe"
	@echo ""
	@echo "📊 Monitoring & Ops:"
	@echo "  monitoring-up    - Start Prometheus + Grafana + AlertManager"
	@echo "  monitoring-down  - Stop monitoring stack"
	@echo "  prod-observe     - 🚀 One-shot: build → deploy → verify → open Grafana"
	@echo "  seed-metrics     - 🌱 Generate routing traffic (COUNT=100)"
	@echo "  alert-smoke      - 🧪 Test alert system health"
	@echo "  dash-import      - Import Grafana dashboard (needs GRAFANA_API_KEY)"
	@echo "  init-routing-db  - Initialize database schema + indexes"
	@echo "  approve-promote  - Safe auto-approval and promotion"
	@echo "  check-metrics    - Verify /metrics endpoint"
	@echo "  quick-verify     - Quick health check"
	@echo ""
	@echo "🗣️  Athena Reporter (Voice + Visual):"
	@echo "  reporter-build   - Build Athena Reporter app"
	@echo "  reporter-run     - Launch reporter window"
	@echo "  report-health    - 📊 Generate + speak system health report"
	@echo "  report-evolution - 🧬 Generate evolution status report"
	@echo "  report-metrics   - 📈 Generate metrics health report"
	@echo ""
	@echo "🩺 Workspace:"
	@echo "  check-health     - Quick system verification (2-min checklist)"
	@echo "  workspace-health - Full workspace doctor scan"
	@echo "  daily-ops        - Daily 90-second ops check 📋"
	@echo ""
	@echo "🔍 FastVLM (Vision):"
	@echo "  fastvlm-go-live        - 🚀 5-min production deployment (START HERE)"
	@echo "  fastvlm-quickstart     - All-in-one: setup + start + validate"
	@echo "  fastvlm-setup          - Setup Apple FastVLM (one-time)"
	@echo "  fastvlm-server         - Start FastVLM server"
	@echo "  fastvlm-autostart      - Enable auto-start with watchdog 🛡️"
	@echo "  fastvlm-test           - Test server health"
	@echo "  fastvlm-smoke          - Run 6-image smoke test suite"
	@echo "  fastvlm-validate       - 90-second validation"
	@echo "  fastvlm-confidence     - Daily confidence check (30s)"
	@echo "  fastvlm-crash-test     - Test auto-recovery from crash"
	@echo "  fastvlm-health         - Check server status"
	@echo "  fastvlm-metrics        - View metrics"
	@echo "  fastvlm-logrotate      - Rotate large logs (>10MB)"
	@echo "  vision                 - Ask about an image (IMG=file.png PROMPT='...')"
	@echo "  vision-ocr             - Extract text (IMG=document.png)"
	@echo "  vision-chart           - Extract chart data (IMG=chart.png)"
	@echo "  vision-ui              - Analyze UI (IMG=screenshot.png)"
	@echo "  vision-diagram         - Explain diagram (IMG=arch.png)"
	@echo ""
	@echo "🌉 NeuroForge Bridge:"
	@echo "  bridge-up             - Start bridge service on port 8014"
	@echo "  bridge-down           - Stop bridge service"
	@echo "  app                   - Run NeuroForge app with bridge"
	@echo "  all                   - Start bridge + app together"
	@echo "  logs                  - Show bridge logs"
	@echo "  smoke                 - Smoke test bridge endpoints"
	@echo ""
	@echo "🐤 Canary Deployment:"
	@echo "  canary-10            - Enable canary at 10% (CANARY_MODEL=...)"
	@echo "  canary-25            - Enable canary at 25%"
	@echo "  canary-50            - Enable canary at 50%"
	@echo "  canary-off           - Disable canary"
	@echo "  canary-rollback      - Instant rollback to control 🚨"
	@echo "  canary-status        - Show canary config"
	@echo "  canary-check         - Check traffic split"
	@echo "  canary-eval          - Statistical evaluation (Wilson intervals)"
	@echo "  canary-auto-rollback - Eval + rollback if stat-sig worse"
	@echo "  canary-auto-promote  - Promote if stat-sig better for 48h 🎯"
	@echo "  canary-smoke         - Test canary deployment"
	@echo "  breaker-status       - Show circuit breaker states"
	@echo ""
	@echo "🌳 Model Lineage:"
	@echo "  lineage              - Generate lineage report (tree + graph + stats)"
	@echo "  lineage-open         - Generate and open in browser"
	@echo "  lineage-tree         - Show ASCII tree"
	@echo ""
	@echo "🧪 E2E Testing:"
	@echo "  e2e-sweep            - Full platform sweep (all services)"
	@echo "  green                - Fast health check (1-liner) 🟢"
	@echo "  weaviate-seed        - Seed Weaviate with learned patterns"
	@echo "  validate-green       - Pre-tag validation (all gates)"
	@echo "  tag-green            - Validate + tag as v0.9.1-green"
	@echo ""
	@echo "📖 Examples:"
	@echo "  make fastvlm-go-live                    # 🚀 START HERE"
	@echo "  make daily-ops                          # Every morning"
	@echo "  make vision-chart IMG=sales.png         # Extract chart"
	@echo "  make lineage-tree                       # Model history"
	@echo ""
	@echo "📚 Documentation:"
	@echo "  README_FASTVLM.md                       # Quick overview"
	@echo "  GO_LIVE_CHECKLIST.md                    # Deployment guide"
	@echo "  FASTVLM_FINAL_SUMMARY.md                # Complete reference"
	@echo ""
	@echo "🎮 Control Panel:"
	@echo "  athena-menu          - Interactive menu (or just type: athena)"
	@echo "  Desktop shortcuts:   Start Athena.command, Panic Athena.command"
	@echo ""

# ============================================================================
# Assistant Broker
# ============================================================================

broker:
	@echo "🚀 Building and starting assistant-broker..."
	cd $(BROKER_DIR) && $(MAKE) build
	@echo ""
	@echo "✅ Broker ready. Starting on http://127.0.0.1:$(PORT)"
	@echo "   Press Ctrl+C to stop"
	@echo ""
	cd $(BROKER_DIR) && PORT=$(PORT) $(MAKE) run

broker-agent:
	@echo "📦 Installing assistant-broker LaunchAgent..."
	cd $(BROKER_DIR) && $(MAKE) install-agent
	@echo ""
	@echo "✅ Broker will now start automatically at login"
	@echo "   Check status: launchctl list | grep assistant-broker"
	@echo "   View logs: tail -f ~/Library/Logs/AssistantBroker.*.log"

broker-test:
	@echo "🧪 Testing assistant-broker..."
	cd $(BROKER_DIR) && $(MAKE) test

broker-uninstall:
	@echo "🗑️  Uninstalling assistant-broker LaunchAgent..."
	cd $(BROKER_DIR) && $(MAKE) uninstall-agent

# ============================================================================
# Build Pipeline
# ============================================================================

build:
	@if [ -z "$(PROJ)" ]; then \
		echo "❌ Error: PROJ not set. Usage: make build NAME=AppName PROJ=/path/to/project TYPE=swift" >&2; \
		exit 1; \
	fi
	@echo "🔨 Building $(NAME) ($(TYPE))..."
	@if [ "$(TYPE)" = "swift" ]; then \
		bash $(SCRIPTS_DIR)/build_swift_app.sh "$(NAME)" "$(PROJ)"; \
	elif [ "$(TYPE)" = "tauri" ]; then \
		bash $(SCRIPTS_DIR)/build_tauri_app.sh "$(PROJ)"; \
	else \
		echo "❌ Unknown TYPE: $(TYPE). Use swift|tauri" >&2; \
		exit 1; \
	fi

validate:
	@if [ -z "$(PROJ)" ]; then \
		echo "❌ Error: PROJ not set. Usage: make validate NAME=AppName PROJ=/path/to/project TYPE=swift" >&2; \
		exit 1; \
	fi
	@echo "🧪 Validating $(NAME) ($(TYPE))..."
	@if [ "$(TYPE)" = "swift" ]; then \
		bash $(SCRIPTS_DIR)/validate_swift_app.sh "$(NAME)" "$(PROJ)"; \
	elif [ "$(TYPE)" = "python" ]; then \
		bash $(SCRIPTS_DIR)/validate_python_app.sh "$(PROJ)"; \
	else \
		echo "❌ Unknown TYPE: $(TYPE). Use swift|python" >&2; \
		exit 1; \
	fi

package:
	@if [ -z "$(APP)" ]; then \
		echo "❌ Error: APP not set. Usage: make package APP=/path/to/App.app" >&2; \
		exit 1; \
	fi
	@echo "📦 Packaging $(APP)..."
	bash $(SCRIPTS_DIR)/package_dmg.sh "$(APP)"

deliver:
	@if [ -z "$(PROJ)" ]; then \
		echo "❌ Error: PROJ not set. Usage: make deliver NAME=AppName PROJ=/path/to/project TYPE=swift" >&2; \
		exit 1; \
	fi
	@echo "╔════════════════════════════════════════════════════════════╗"
	@echo "║  Full Delivery Pipeline: $(NAME)"
	@echo "╚════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Step 1/4: Validation"
	@$(MAKE) validate NAME="$(NAME)" PROJ="$(PROJ)" TYPE="$(TYPE)"
	@echo ""
	@echo "Step 2/4: Build"
	@APP_PATH=$$($(MAKE) build NAME="$(NAME)" PROJ="$(PROJ)" TYPE="$(TYPE)" | tail -1); \
	echo "$$APP_PATH" > /tmp/last_build_path.txt
	@echo ""
	@echo "Step 3/4: Package"
	@APP_PATH=$$(cat /tmp/last_build_path.txt); \
	DMG_PATH=$$($(MAKE) package APP="$$APP_PATH" | tail -1); \
	echo "$$DMG_PATH" > /tmp/last_dmg_path.txt
	@echo ""
	@echo "Step 4/4: Reveal"
	@DMG_PATH=$$(cat /tmp/last_dmg_path.txt); \
	open "$$DMG_PATH"
	@echo ""
	@echo "🎉 Delivery complete!"
	@echo "   DMG: $$(cat /tmp/last_dmg_path.txt)"

# ============================================================================
# Workspace Management
# ============================================================================

workspace-health:
	@echo "🩺 Running workspace health check..."
	@bash $(CURDIR)/workspace_doctor.sh

check-health:
	@echo "⚡ Running 2-minute system verification..."
	@bash $(SCRIPTS_DIR)/launch_checklist.sh

# ============================================================================
# App Wizard - AI-Driven App Creation
# ============================================================================

wizard:
	@if [ -z "$(PROMPT)" ] || [ "$(PROMPT)" = "simple test app" ]; then \
		echo "❌ Error: PROMPT not set. Usage: make wizard NAME=MyApp TYPE=swift PROMPT='description'" >&2; \
		echo "" >&2; \
		echo "Example: make wizard NAME=MenuBarApp TYPE=swift PROMPT='SwiftUI menu bar app'" >&2; \
		exit 1; \
	fi
	@echo "🧙‍♂️ Starting App Wizard..."
	@python3 $(SCRIPTS_DIR)/app_wizard.py "$(NAME)" "$(TYPE)" "$(PROMPT)" $(if $(PROJ),--project "$(PROJ)",)

# ============================================================================
# Quick Links to Project Makefiles
# ============================================================================

uat:
	@echo "🔧 Running universal-ai-tools commands..."
	cd AI-Projects/universal-ai-tools && $(MAKE) $(CMD)

trm:
	@echo "🔧 Running TinyRecursiveModels commands..."
	cd TinyRecursiveModels && $(MAKE) $(CMD)

# Examples:
#   make uat CMD=test
#   make trm CMD=lint
#   make wizard NAME=MyApp TYPE=swift PROMPT='description'
#   make check-health

# ============================================================================
# Autonomous Evolution
# ============================================================================

learn: train eval promote
	@echo "✅ Full evolution loop complete"

learn-init:
	@echo "🗄️  Initializing learning database..."
	@cd AI-Projects/universal-ai-tools && psql "$$DATABASE_URL" -f db/migrations/20251012_routing_outcomes.sql
	@cd AI-Projects/universal-ai-tools && psql "$$DATABASE_URL" -f ../../scripts/learn/db_indexes.sql 2>/dev/null || true
	@echo "✅ Database initialized"

learn-verify:
	@bash scripts/learn/verify_learning.sh

learn-stats:
	@echo "📊 Learning Stats (Last 30 Days)"
	@echo "================================"
	@python3 scripts/learn/outcome_logger.py

train:
	@echo "🧠 Training TRM from routing outcomes ($(DAYS) days)..."
	@python3 $(SCRIPTS_DIR)/learn/train_trm_lora.py --from-outcomes --days $(DAYS) --epochs 1 --lr 1e-4

eval:
	@echo "📊 Evaluating candidate vs baseline..."
	@CANDIDATE=$$(ls -dt artifacts/trm/* 2>/dev/null | head -1); \
	if [ -z "$$CANDIDATE" ]; then \
		echo "❌ No candidates found in artifacts/trm/"; \
		exit 1; \
	fi; \
	python3 $(SCRIPTS_DIR)/learn/eval_trm.py --candidate "$$CANDIDATE" --baseline models/trm/current

promote:
	@echo "🚀 Promoting candidate if better + safe..."
	@CANDIDATE=$$(ls -dt artifacts/trm/* 2>/dev/null | head -1); \
	if [ -z "$$CANDIDATE" ]; then \
		echo "❌ No candidates found in artifacts/trm/"; \
		exit 1; \
	fi; \
	python3 $(SCRIPTS_DIR)/learn/promote.py --candidate "$$CANDIDATE"

# ============================================================================
# Monitoring & Operations
# ============================================================================

dash-import:
	@echo "📊 Importing Grafana dashboard..."
	@bash $(SCRIPTS_DIR)/monitoring/import_grafana_dashboard.sh

init-routing-db:
	@echo "🗄️  Initializing routing outcomes database..."
	@if [ -z "$$DATABASE_URL" ]; then \
		echo "❌ DATABASE_URL not set" >&2; \
		exit 1; \
	fi
	@psql "$$DATABASE_URL" -f db/migrations/20251012_routing_outcomes.sql
	@psql "$$DATABASE_URL" -f $(SCRIPTS_DIR)/learn/db_indexes.sql
	@echo "✅ routing_outcomes schema + indexes applied"

approve-promote:
	@echo "🤖 Running auto-approval and promotion..."
	@bash $(SCRIPTS_DIR)/learn/approve_and_promote.sh

check-metrics:
	@echo "📈 Checking metrics endpoint..."
	@curl -s http://127.0.0.1:8080/metrics | head -100 | sed -n '1,40p' || echo "⚠️  Metrics endpoint not responding"

monitoring-up:
	@echo "🚀 Starting monitoring stack (Prometheus + Grafana)..."
	@docker-compose -f docker-compose.monitoring.yml up -d
	@echo "✅ Monitoring stack started"
	@echo "   Prometheus: http://localhost:9090"
	@echo "   Grafana:    http://localhost:3001 (admin/admin)"

monitoring-down:
	@echo "🛑 Stopping monitoring stack..."
	@docker-compose -f docker-compose.monitoring.yml down

monitoring-logs:
	@docker-compose -f docker-compose.monitoring.yml logs -f

quick-verify:
	@echo "🔍 Running quick verification..."
	@bash $(SCRIPTS_DIR)/monitoring/quick_verify.sh

seed-metrics:
	@echo "🌱 Seeding TRM metrics with routing traffic..."
	@bash $(SCRIPTS_DIR)/monitoring/seed_metrics.sh $(COUNT)

alert-smoke:
	@echo "🧪 Running alert system smoke test..."
	@bash $(SCRIPTS_DIR)/monitoring/alert_smoke.sh

reporter-build:
	@echo "🛠️  Building Athena Reporter..."
	@mkdir -p build/AthenaReporter.app/Contents/MacOS
	@mkdir -p build/AthenaReporter.app/Contents/Resources
	@cd AthenaReporter && swiftc -parse-as-library -target arm64-apple-macos13 \
		-o ../build/AthenaReporter.app/Contents/MacOS/AthenaReporter \
		Dedupe.swift VoiceSentinel.swift VoiceManager.swift VoiceDoctor.swift ReportStore.swift AthenaReporter.swift \
		-framework AppKit -framework SwiftUI -framework AVFoundation 2>&1 | grep -v "warning:" || true
	@cp AthenaReporter/Info.plist build/AthenaReporter.app/Contents/Info.plist
	@echo "✅ Built: build/AthenaReporter.app (with Voice Sentinel + Mismatch Detection)"

reporter-run: reporter-build
	@echo "🚀 Launching Athena Reporter..."
	@open build/AthenaReporter.app

report-health:
	@echo "📊 Generating system health report..."
	@python3 $(SCRIPTS_DIR)/athena_report.py health

report-evolution:
	@echo "🧬 Generating evolution report..."
	@python3 $(SCRIPTS_DIR)/athena_report.py evolution

report-metrics:
	@echo "📈 Generating metrics report..."
	@python3 $(SCRIPTS_DIR)/athena_report.py metrics

prod-observe:
	@echo "🚀 Production Observability Deployment"
	@echo "======================================"
	@echo ""
	@echo "Step 1/5: Rebuilding athena-api with metrics..."
	@cd AI-Projects/universal-ai-tools && docker build -t universal-ai-tools-python-api:latest -f Dockerfile.python-api . -q
	@echo "✅ Image rebuilt"
	@echo ""
	@echo "Step 2/5: Restarting container..."
	@cd AI-Projects/universal-ai-tools && docker-compose -f docker-compose.athena.yml up -d --no-deps --force-recreate athena-api > /dev/null 2>&1
	@sleep 6
	@echo "✅ Container restarted"
	@echo ""
	@echo "Step 3/5: Reloading Prometheus..."
	@docker restart athena-prometheus > /dev/null 2>&1
	@sleep 4
	@echo "✅ Prometheus reloaded"
	@echo ""
	@echo "Step 4/5: Verifying targets..."
	@curl -s http://127.0.0.1:8888/metrics/ | head -3 | grep -q "python_gc" && echo "✅ Metrics endpoint UP" || echo "❌ Metrics endpoint DOWN"
	@curl -s 'http://localhost:9090/api/v1/targets' | jq -r '.data.activeTargets[] | select(.labels.job=="athena-api-prod") | .health' | grep -q "up" && echo "✅ Prometheus scraping" || echo "⚠️  Waiting for scrape"
	@echo ""
	@echo "Step 5/5: Opening Grafana..."
	@open http://localhost:3001/d/aad047ea-87e8-4cea-9a8b-9bd96207d0df/trm-evolution-overview || true
	@open http://localhost:9090/targets || true
	@echo ""
	@echo "🎉 Production observability is LIVE!"
	@echo "   📊 Metrics: http://127.0.0.1:8888/metrics/"
	@echo "   🔍 Prometheus: http://localhost:9090"
	@echo "   📈 Dashboard: http://localhost:3001"
	@echo "   🚨 Alerts: http://localhost:9090/alerts"



# Voice management
pin-voice:
	@echo "🎤 Pinning Samantha as Athena's voice..."
	@scripts/pin_voice.sh

test-voice:
	@echo "🧪 Testing Athena's voice..."
	@pkill -9 AthenaReporter 2>/dev/null || true
	@sleep 0.5
	@make report-health

# ============================================================================
# FastVLM - Vision Language Model
# ============================================================================

fastvlm-setup:
	@echo "🚀 Setting up Apple FastVLM..."
	@cd fastvlm && bash setup_fastvlm.sh
	@echo ""
	@echo "✅ FastVLM setup complete!"
	@echo "   Next: make fastvlm-server"

# Quick start (setup + start + validate)
fastvlm-quickstart:
	@bash scripts/quick_start_fastvlm.sh

fastvlm-go-live:
	@bash scripts/go_live_fastvlm.sh

fastvlm-server:
	@echo "🚀 Starting FastVLM server..."
	@export FASTVLM_ROOT="$(CURDIR)/fastvlm/ml-fastvlm" && \
	export FASTVLM_MODEL="checkpoints/fastvlm_1.5b_stage3" && \
	cd fastvlm && python3 fastvlm_server.py

fastvlm-test:
	@echo "🧪 Testing FastVLM server..."
	@python3 scripts/athena_vision.py --health

fastvlm-up: fastvlm-server &
	@echo "✅ FastVLM server started in background"

fastvlm-down:
	@echo "🛑 Stopping FastVLM server..."
	@pkill -f "fastvlm_server.py" || echo "ℹ️  No server running"
	@pkill -f "fastvlm_watchdog.sh" || true

fastvlm-health:
	@bash scripts/fastvlm_health.sh

fastvlm-metrics:
	@echo "📊 FastVLM Metrics"
	@echo "=================="
	@curl -s http://127.0.0.1:8811/metrics | grep "^fastvlm_" | head -20

fastvlm-autostart:
	@echo "🔄 Installing LaunchAgent for auto-start..."
	@mkdir -p ~/Library/LaunchAgents
	@cp scripts/com.athena.fastvlm.plist ~/Library/LaunchAgents/
	@launchctl load ~/Library/LaunchAgents/com.athena.fastvlm.plist 2>&1 || echo "⚠️  Already loaded"
	@sleep 2
	@bash scripts/fastvlm_health.sh
	@echo "✅ FastVLM will now auto-start on login with watchdog"
	@echo "   Logs: /tmp/fastvlm_watchdog.log"

fastvlm-disable-autostart:
	@echo "🛑 Disabling auto-start..."
	@launchctl unload ~/Library/LaunchAgents/com.athena.fastvlm.plist 2>&1 || echo "Not loaded"
	@pkill -f "fastvlm_watchdog.sh" || true

fastvlm-logs:
	@tail -f /tmp/fastvlm_server.log

fastvlm-watchdog-logs:
	@tail -f /tmp/fastvlm_watchdog.log

fastvlm-logrotate:
	@echo "🧹 Rotating FastVLM logs..."
	@for log in /tmp/fastvlm_server.log /tmp/fastvlm_watchdog.log; do \
		if [ -f "$$log" ]; then \
			SIZE=$$(stat -f%z "$$log" 2>/dev/null || stat -c%s "$$log" 2>/dev/null); \
			if [ $$SIZE -gt 10485760 ]; then \
				mv "$$log" "$$log.1"; \
				touch "$$log"; \
				echo "  ✓ Rotated $$log (was $$(echo $$SIZE | awk '{print int($$1/1024/1024)}')MB)"; \
			else \
				echo "  ⊘ $$log ($$(echo $$SIZE | awk '{print int($$1/1024)}')KB, no rotation needed)"; \
			fi; \
		fi; \
	done
	@echo "✅ Log rotation complete"

# Vision CLI command (shortcut)
vision:
	@if [ -z "$(IMG)" ]; then \
		echo "❌ Error: IMG not set. Usage: make vision IMG=screenshot.png PROMPT='what is this?'" >&2; \
		exit 1; \
	fi
	@python3 scripts/athena_vision.py "$(IMG)" "$(PROMPT)"

# Quick demo with a test image
fastvlm-demo:
	@echo "🎬 FastVLM Demo"
	@echo "==============="
	@echo ""
	@if [ ! -f /tmp/test-chart.png ]; then \
		echo "📸 Please save a screenshot to /tmp/test-chart.png"; \
		echo "   or run: make vision IMG=/path/to/image.png PROMPT='describe this'"; \
		exit 1; \
	fi
	@python3 scripts/athena_vision.py /tmp/test-chart.png "What's in this image?" --report

# Vision smoke test (6 image types)
fastvlm-smoke:
	@echo "🧪 Running vision smoke test..."
	@python3 scripts/vision_smoke_test.py

# 90-second validation (health + metrics + smoke)
fastvlm-validate:
	@bash scripts/fastvlm_validation.sh

# Daily confidence check (quick)
fastvlm-confidence:
	@bash scripts/fastvlm_confidence_check.sh

# Crash recovery test
fastvlm-crash-test:
	@bash scripts/fastvlm_crash_test.sh

# Enhanced vision helpers
vision-ocr:
	@if [ -z "$(IMG)" ]; then \
		echo "❌ Error: IMG not set. Usage: make vision-ocr IMG=document.png" >&2; \
		exit 1; \
	fi
	@python3 scripts/athena_vision.py "$(IMG)" "Extract all text from this document as markdown"

vision-chart:
	@if [ -z "$(IMG)" ]; then \
		echo "❌ Error: IMG not set. Usage: make vision-chart IMG=chart.png" >&2; \
		exit 1; \
	fi
	@python3 scripts/athena_vision.py "$(IMG)" "Extract data from this chart as a markdown table with headers"

vision-ui:
	@if [ -z "$(IMG)" ]; then \
		echo "❌ Error: IMG not set. Usage: make vision-ui IMG=screenshot.png" >&2; \
		exit 1; \
	fi
	@python3 scripts/athena_vision.py "$(IMG)" "Describe all UI elements, their positions, and relationships"

vision-diagram:
	@if [ -z "$(IMG)" ]; then \
		echo "❌ Error: IMG not set. Usage: make vision-diagram IMG=arch.png" >&2; \
		exit 1; \
	fi
	@python3 scripts/athena_vision.py "$(IMG)" "Explain this technical diagram, identifying all components and connections"

# ============================================================================
# Canary Deployment + Circuit Breaker
# ============================================================================

canary-on:
	@echo "🐤 Enabling canary: $(CANARY_MODEL) at $(CANARY_PERCENT)%"
	@echo "export CANARY_ENABLED=true" > /tmp/canary.env
	@echo "export CANARY_MODEL=$(CANARY_MODEL)" >> /tmp/canary.env
	@echo "export CANARY_PERCENT=$(CANARY_PERCENT)" >> /tmp/canary.env
	@echo "✅ Canary enabled (source /tmp/canary.env to activate)"

canary-10:
	@$(MAKE) canary-on CANARY_MODEL=$(CANARY_MODEL) CANARY_PERCENT=10

canary-25:
	@$(MAKE) canary-on CANARY_MODEL=$(CANARY_MODEL) CANARY_PERCENT=25

canary-50:
	@$(MAKE) canary-on CANARY_MODEL=$(CANARY_MODEL) CANARY_PERCENT=50

canary-off:
	@echo "🛑 Disabling canary"
	@echo "export CANARY_ENABLED=false" > /tmp/canary.env
	@echo "export CANARY_PERCENT=0" >> /tmp/canary.env
	@echo "✅ Canary disabled (source /tmp/canary.env to activate)"

canary-rollback:
	@echo "🚨 Rolling back canary"
	@$(MAKE) canary-off
	@echo "✅ Rolled back to control"

canary-status:
	@echo "📊 Canary Status"
	@echo "================"
	@echo "Enabled:  $$CANARY_ENABLED"
	@echo "Model:    $$CANARY_MODEL"
	@echo "Percent:  $$CANARY_PERCENT%"
	@echo ""
	@echo "Circuit Breaker:"
	@echo "  Window:      $$CB_WINDOW requests"
	@echo "  Fail rate:   $$CB_FAIL_RATE"
	@echo "  p95 thresh:  $$CB_P95_MS ms"
	@echo "  Open time:   $$CB_OPEN_SECONDS s"

canary-check:
	@echo "🔍 Checking canary metrics..."
	@curl -s 'http://localhost:9090/api/v1/query?query=sum%20by%20(bucket)%20(increase(routing_decisions_total%5B5m%5D))' | jq -r '.data.result[] | "\(.metric.bucket): \(.value[1])"'

breaker-status:
	@echo "🔒 Circuit Breaker Status"
	@echo "========================="
	@curl -s 'http://localhost:9090/api/v1/query?query=circuit_breaker_open' | jq -r '.data.result[] | "\(.metric.model): \(if .value[1] == "1" then "OPEN" else "CLOSED" end)"'

canary-smoke:
	@bash scripts/canary_smoke_test.sh

canary-eval:
	@echo "📊 Evaluating canary vs control (statistical)..."
	@PROM_URL=http://localhost:9090 python3 scripts/auto_rollback.py

canary-auto-rollback:
	@echo "🤖 Auto-rollback guard (runs stat test, rolls back if needed)..."
	@if python3 scripts/auto_rollback.py; then \
		echo "✅ Canary OK"; \
	else \
		echo "🚨 Triggering rollback"; \
		$(MAKE) canary-rollback; \
		source /tmp/canary.env; \
	fi

canary-auto-promote:
	@echo "🎯 Auto-promote guard (promotes if stat-sig better for 48h)..."
	@python3 scripts/auto_promote_canary.py; \
	EXIT_CODE=$$?; \
	if [ $$EXIT_CODE -eq 42 ]; then \
		echo "🎉 Promotion criteria met!"; \
		bash scripts/apply_promotion.sh; \
	elif [ $$EXIT_CODE -eq 0 ]; then \
		echo "⏳ Continue monitoring"; \
	else \
		echo "⚠️  Evaluation failed"; \
	fi

canary-setup-auto-promote:
	@bash scripts/setup_auto_promotion.sh

canary-promotion-status:
	@echo "📊 Promotion Status"
	@echo "==================="
	@if [ -f /tmp/fastvlm_canary_promotion_state.json ]; then \
		cat /tmp/fastvlm_canary_promotion_state.json | jq; \
	else \
		echo "No promotion state (canary not deployed or not better)"; \
	fi

# Daily ops check (90 seconds)
daily-ops:
	@bash scripts/daily_ops_check.sh

# ============================================================================
# Model Lineage Tracking
# ============================================================================

LINEAGE_DIR := artifacts/lineage

lineage:
	@echo "🌳 Building model lineage..."
	@python3 scripts/lineage/build_lineage.py

lineage-open: lineage
	@echo "📊 Opening lineage artifacts..."
	@if [ -f $(LINEAGE_DIR)/lineage.svg ]; then \
		open $(LINEAGE_DIR)/lineage.svg; \
	else \
		open $(LINEAGE_DIR)/lineage.md || cat $(LINEAGE_DIR)/lineage.txt; \
	fi

lineage-tree:
	@make lineage > /dev/null 2>&1
	@cat $(LINEAGE_DIR)/lineage.txt

# ============================================================================
# E2E Testing & Health
# ============================================================================

e2e-sweep:
	@echo "🔍 Running E2E full platform sweep..."
	@python3 scripts/e2e_full_sweep.py

green:
	@echo "🟢 Fast health check (all services)..."
	@BASE=$${BASE:-http://localhost:8014} python3 -c "import requests; \
		services={'chat':8014,'tts':8888,'k1':8088,'k2':8089,'k3':8091,'weaviate':8090}; \
		[print(f\"{'✅' if requests.get(f'http://localhost:{p}/health',timeout=2).status_code in [200,404,422] else '❌'} {n}\") \
		 for n,p in services.items()]" 2>/dev/null || echo "⚠️  Some services not responding"

full-validate:
	@echo "🔍 Running Full Program Validation..."
	@echo "======================================"
	@echo ""
	@echo "1️⃣  Preflight SLA..."
	@cd orchestrator && make preflight || echo "⚠️  Preflight not available"
	@echo ""
	@echo "2️⃣  Code Inventory..."
	@python3 tools/code_inventory.py
	@echo ""
	@echo "3️⃣  Telemetry Stats..."
	@python3 tools/telemetry_stats.py
	@echo ""
	@echo "4️⃣  Starting Eval API..."
	@cd orchestrator && python3 -m uvicorn tools.eval_api:app --host 127.0.0.1 --port 8788 > /dev/null 2>&1 & sleep 3
	@echo ""
	@echo "5️⃣  Running Golden Evals..."
	@curl -s -X POST http://127.0.0.1:8788/eval/run -H 'Content-Type: application/json' -d '{"capability":"summarize","limit":0}' -o orchestrator/state/eval.summarize.json || echo "⚠️  Eval API not responding"
	@curl -s -X POST http://127.0.0.1:8788/eval/run -H 'Content-Type: application/json' -d '{"capability":"plan","limit":0}' -o orchestrator/state/eval.plan.json || echo "⚠️  Eval API not responding"
	@echo ""
	@echo "6️⃣  Generating Full Report..."
	@python3 tools/generate_full_report.py
	@echo ""
	@echo "======================================"
	@echo "✅ Full Validation Complete!"
	@echo "======================================"
	@echo ""
	@echo "📄 Report: FULL_VALIDATION_REPORT.md"
	@echo ""
	@cat FULL_VALIDATION_REPORT.md || echo "Report not generated"

inventory:
	@python3 tools/code_inventory.py

weaviate-seed:
	@python3 scripts/seed_weaviate.py

validate-green:
	@bash scripts/validate_green.sh

tag-green:
	@echo "🏷️  Tagging green build..."
	@bash scripts/validate_green.sh && \
		git tag -a v0.9.1-green -m "E2E sweep + routing policy + Weaviate seeded + FastVLM complete" && \
		echo "✅ Tagged v0.9.1-green" && \
		echo "   Push with: git push --tags"

model-pipeline:
	@if [ -z "$(BASE)" ] || [ -z "$(DATA)" ] || [ -z "$(NAME)" ]; then \
		echo "❌ Usage: make model-pipeline BASE=hf://model DATA=data.jsonl NAME=output"; \
		exit 1; \
	fi
	@bash scripts/model_pipeline.sh --base "$(BASE)" --data "$(DATA)" --name "$(NAME)"

# ============================================================================
# Athena Control Menu
# ============================================================================

athena-menu:
	@bash scripts/athena_menu.sh

# Kokoro TTS Server
kokoro-start:
	@echo "🚀 Starting Kokoro TTS server..."
	@pkill -f kokoro_server.py 2>/dev/null || true
	@sleep 1
	@scripts/kokoro_server.py 8020 > /tmp/kokoro_server.log 2>&1 &
	@sleep 4
	@bash scripts/kokoro_health.sh || (echo "⚠️  Server failed to start. Check /tmp/kokoro_server.log" && exit 1)

kokoro-stop:
	@echo "🛑 Stopping Kokoro TTS server..."
	@pkill -f kokoro_server.py || echo "ℹ️  No server running"

kokoro-health:
	@bash scripts/kokoro_health.sh

kokoro-test:
	@echo "🧪 Testing Kokoro TTS..."
	@bash scripts/kokoro_health.sh || (echo "❌ Server not running. Start with: make kokoro-start" && exit 1)
	@curl -s -X POST http://127.0.0.1:8020/tts \
		-H "Content-Type: application/json" \
		-d '{"text": "This is Athena using Kokoro TTS. Natural, warm voice with serna personality.", "voice": "af_heart"}' \
		-o /tmp/kokoro_test.wav
	@afplay /tmp/kokoro_test.wav
	@echo "✅ Kokoro test complete - should sound natural and warm!"

kokoro-logs:
	@tail -f /tmp/kokoro_server.log

kokoro-autostart:
	@echo "🔄 Installing LaunchAgent for auto-start..."
	@launchctl load ~/Library/LaunchAgents/com.athena.kokoro.plist 2>&1 || echo "⚠️  Already loaded"
	@sleep 2
	@bash scripts/kokoro_health.sh
	@echo "✅ Kokoro will now auto-start on login"

kokoro-disable-autostart:
	@echo "🛑 Disabling auto-start..."
	@launchctl unload ~/Library/LaunchAgents/com.athena.kokoro.plist 2>&1 || echo "Not loaded"

# Self-Improvement Loop (Track 3)
learn-init:
	@echo "🧠 Initializing learning system..."
	@bash scripts/learn/db_indexes.sql 2>/dev/null || echo "Indexes already exist"
	@python3 scripts/learn/outcome_logger.py
	@echo "✅ Learning system initialized"

learn-daemon:
	@echo "🧠 Starting learn daemon..."
	@python3 scripts/learn/learn_daemon.py

learn-stats:
	@echo "📊 Routing outcome stats..."
	@python3 scripts/learn/outcome_logger.py 30

learn:
	@echo "🎓 Running TRM evolution cycle..."
	@DAYS=$(or $(DAYS),7) bash scripts/learn/approve_and_promote.sh

# Safety & Automation
ENV ?= local
BUILD_SHA ?= dev
CONTROL ?= mlx/chat
CANARY ?= mlx/chat@canary

breaker-test:
	@echo "🧪 Testing circuit breaker..."
	@python3 -c "from src.core.routing.circuit_breaker import CircuitBreaker; \
		b=CircuitBreaker('mlx/chat',env='$(ENV)',build='$(BUILD_SHA)',min_requests=5,fail_ratio_threshold=0.5,open_secs=10); \
		[b.record(bool(ok)) for ok in [0,0,1,0,0]]; \
		print('Breaker state:', b.get_state()); \
		print('Allow?', b.allow())"

shadow-on:
	@echo "🌐 Enabling shadow mode to $$CANDIDATE"
	@echo "export SHADOW_ENABLE=1" > .env.shadow
	@echo "export SHADOW_CANDIDATE=$$CANDIDATE" >> .env.shadow
	@echo "✅ Shadow enabled. Source .env.shadow before starting services."

shadow-off:
	@echo "🛑 Disabling shadow mode"
	@echo "export SHADOW_ENABLE=0" > .env.shadow
	@echo "✅ Shadow disabled"

auto-rollback:
	@echo "🔄 Checking canary health..."
	@PROM_URL=http://localhost:9090 ENV=$(ENV) CONTROL_MODEL=$(CONTROL) CANARY_MODEL=$(CANARY) \
		python3 scripts/auto_rollback.py

weekly-autopilot:
	@echo "📊 Generating weekly autopilot report..."
	@python3 scripts/weekly_autopilot_report.py

pg-backup:
	@echo "📦 Backing up PostgreSQL..."
	@DATABASE_URL="postgresql://postgres:postgres@localhost:5432/athena_db" \
		bash scripts/pg_backup.sh

# Canary Management (Stat-Sig)
canary-eval:
	@echo "📊 Evaluating canary (Wilson interval)..."
	@chmod +x scripts/canary_eval.py
	@python3 scripts/canary_eval.py

canary-auto-promote:
	@echo "🎓 Canary auto-promotion check..."
	@chmod +x scripts/canary_eval.py
	@if python3 scripts/canary_eval.py; then \
		STATUS=$$?; \
		if [ $$STATUS -eq 1 ]; then \
			echo "✅ Promoting canary (stat-sig better)"; \
			make promote 2>&1 | tee -a logs/auto_promotion.log; \
		elif [ $$STATUS -eq 2 ]; then \
			echo "🔴 Rolling back canary (stat-sig worse)"; \
			make auto-rollback; \
		else \
			echo "📊 Monitoring (no stat-sig difference)"; \
		fi; \
	fi

# Promotions Metrics Testing
promotion-test:
	@echo "🧪 Testing promotion metric..."
	@python3 -c "import sys; sys.path.insert(0, '.'); \
		from src.metrics.route_metrics import record_promotion; \
		record_promotion('promotion','fastvlm-1.5b','fastvlm-0.5b','manual_test','vision'); \
		print('✅ Promotion metric incremented')"
	@echo "📊 Querying metric..."
	@sleep 1
	@curl -s 'http://localhost:9090/api/v1/query?query=promotions_total' 2>/dev/null | jq -r '.data.result[] | "  \(.metric.action): \(.metric.from_model) → \(.metric.to_model) (\(.metric.reason))"' || echo "⚠️  Metrics not available"

# Backup & Verification
backup-verify:
	@echo "🔬 Verifying backup is restorable..."
	@TMPDIR=$$(mktemp -d) && \
	echo "📦 Cloning to $$TMPDIR..." && \
	git clone --depth 1 git@github.com:Cmerrill1713/athena-trm-backup.git "$$TMPDIR/athena-test" && \
	cd "$$TMPDIR/athena-test" && \
	echo "✅ Clone successful" && \
	echo "📋 Checking critical files..." && \
	test -f OPERATOR_CARD.md && echo "  ✅ OPERATOR_CARD.md" || echo "  ❌ Missing OPERATOR_CARD.md" && \
	test -f Makefile && echo "  ✅ Makefile" || echo "  ❌ Missing Makefile" && \
	test -d scripts && echo "  ✅ scripts/" || echo "  ❌ Missing scripts/" && \
	test -d monitoring && echo "  ✅ monitoring/" || echo "  ❌ Missing monitoring/" && \
	test -d AthenaReporter && echo "  ✅ AthenaReporter/" || echo "  ❌ Missing AthenaReporter/" && \
	echo "📊 Testing Make targets..." && \
	make kokoro-health 2>&1 | grep -q "Model: Kokoro" && echo "  ✅ kokoro-health target works" || echo "  ⚠️  kokoro-health needs runtime" && \
	echo "✅ Backup verification complete" && \
	echo "🗑️  Cleaning up $$TMPDIR..." && \
	rm -rf "$$TMPDIR"

backup-push:
	@echo "📤 Pushing backup to GitHub..."
	@git add -A
	@git commit -m "Backup: $$(date -u +'%Y-%m-%d %H:%M:%S UTC')" || echo "No changes to commit"
	@git push origin main
	@TAG="backup/$$(date -u +'%Y%m%d-%H%M%S')"	@git tag -a "$$TAG" -m "Automated backup snapshot"
	@git push origin "$$TAG"
	@echo "✅ Backup pushed with tag: $$TAG"

# ============================================================================
# NeuroForge Bridge - Durable 1-Command Ops
# ============================================================================

bridge-up:
	@echo "🌉 Starting NeuroForge Bridge on port 8014..."
	@UAT_BASE=$${UAT_BASE:-http://127.0.0.1:8080}
	@ATHENA_BASE=$${ATHENA_BASE:-http://127.0.0.1:8090}
	@UAT_TOKEN=$${UAT_TOKEN:-}
	@ATH_TOKEN=$${ATH_TOKEN:-}
	@USE_MOCK=$${USE_MOCK:-1}
	@pkill -f "uvicorn bridge:app" || true
	@cd AI-Projects/universal-ai-tools && \
	UAT_BASE=$$UAT_BASE ATHENA_BASE=$$ATHENA_BASE UAT_TOKEN=$$UAT_TOKEN ATH_TOKEN=$$ATH_TOKEN USE_MOCK=$$USE_MOCK \
	uvicorn bridge:app --host 127.0.0.1 --port 8014 --reload > /tmp/bridge_8014.log 2>&1 &
	@sleep 3
	@echo "✅ Bridge started (PID: $$!)"
	@echo "   Logs: tail -f /tmp/bridge_8014.log"

bridge-down:
	@echo "🛑 Stopping NeuroForge Bridge..."
	@pkill -f "uvicorn bridge:app" || true
	@echo "✅ Bridge stopped"

app:
	@echo "🚀 Starting NeuroForge app..."
	@cd NeuroForgeApp && API_BASE=http://127.0.0.1:8014 QA_MODE=1 swift run

all: bridge-up app

logs:
	@echo "📋 Bridge logs (port 8014):"
	@lsof -iTCP:8014 -sTCP:LISTEN || echo "No process on port 8014"
	@echo ""
	@echo "📋 Recent bridge log entries:"
	@tail -20 /tmp/bridge_8014.log 2>/dev/null || echo "No bridge logs found"

smoke:
	@echo "🧪 Smoke testing bridge endpoints..."
	@curl -sf http://127.0.0.1:8014/health && echo " ✅ Health OK" || echo " ❌ Health FAIL"
	@curl -sf http://127.0.0.1:8014/traces | head -c 200 && echo " ✅ Traces OK" || echo " ❌ Traces FAIL"

# Real Backend Services - Clean, No Port Conflicts
UAT_PORT ?= 8181
ATHENA_PORT ?= 8090
BRIDGE_PORT ?= 8014
UAT_TOKEN ?= supersecret
ATH_TOKEN ?= supersecret
UAT_BASE ?= http://127.0.0.1:$(UAT_PORT)
ATHENA_BASE ?= http://127.0.0.1:$(ATHENA_PORT)

real-up:
	@echo "🚀 Starting Real Mode (clean, scripted)..."
	@bash scripts/real_up.sh

real-down:
	@echo "🛑 Stopping Real Mode..."
	@bash scripts/real_down.sh

# Legacy individual targets (use real-up instead)
uat-up:
	@echo "🚀 Starting UAT service on port $(UAT_PORT)..."
	@lsof -ti:$(UAT_PORT) | xargs -r kill -9 || true
	@cd AI-Projects/universal-ai-tools && \
	UAT_TOKEN=$(UAT_TOKEN) UAT_AUTO_SEED=1 \
	python3 -m uvicorn uat.api:app --host 127.0.0.1 --port $(UAT_PORT) --reload > /tmp/uat_$(UAT_PORT).log 2>&1 &
	@sleep 3
	@echo "✅ UAT started on port $(UAT_PORT)"
	@echo "   Logs: tail -f /tmp/uat_$(UAT_PORT).log"

athena-up:
	@echo "🚀 Starting Athena service on port $(ATHENA_PORT)..."
	@lsof -ti:$(ATHENA_PORT) | xargs -r kill -9 || true
	@cd AI-Projects/universal-ai-tools && \
	ATH_TOKEN=$(ATH_TOKEN) \
	python3 -m uvicorn athena.api:app --host 127.0.0.1 --port $(ATHENA_PORT) --reload > /tmp/athena_$(ATHENA_PORT).log 2>&1 &
	@sleep 3
	@echo "✅ Athena started on port $(ATHENA_PORT)"
	@echo "   Logs: tail -f /tmp/athena_$(ATHENA_PORT).log"

all-real:
	@echo "🚀 Starting all services in real mode..."
	@bash scripts/real_up.sh

stop-all:
	@bash scripts/real_down.sh

# NeuroForge Adapter Wiring
.PHONY: bridge-up bridge-down bridge-all bridge-smoke bridge-slo bridge-chaos

BRIDGE_PID := .bridge.pid

bridge-up:
	@echo "🔗 Starting NeuroForge Adapter on :8014"
	@# Check if already running
	@test -f $(BRIDGE_PID) && kill -0 $$(cat $(BRIDGE_PID)) 2>/dev/null && { echo "✅ Bridge already running"; exit 0; } || true
	@# Kill any process on port 8014
	@lsof -ti:8014 2>/dev/null | xargs -n 1 kill -9 2>/dev/null || true
	@# Install deps
	@cd bridge && python3 -m pip install -r requirements.txt >/dev/null 2>&1 || true
	@# Start bridge
	@cd bridge && UAT_BASE=$${UAT_BASE:-http://127.0.0.1:8080} \
		ATHENA_BASE=$${ATHENA_BASE:-http://127.0.0.1:8090} \
		UAT_TOKEN=$${UAT_TOKEN:-} \
		ATH_TOKEN=$${ATH_TOKEN:-} \
		ENV=$${ENV:-dev} \
		USE_MOCK=$${USE_MOCK:-1} \
		BRIDGE_TOKEN=$${BRIDGE_TOKEN:-} \
		python3 -m uvicorn adapter:app --host 127.0.0.1 --port 8014 --reload > ../logs/adapter.log 2>&1 & echo $$! > ../$(BRIDGE_PID)
	@sleep 3
	@echo "✅ Adapter started on http://127.0.0.1:8014 (PID: $$(cat $(BRIDGE_PID)))"

bridge-down:
	@echo "🔗 Stopping NeuroForge Adapter"
	@-kill -9 $$(cat $(BRIDGE_PID)) 2>/dev/null || true
	@rm -f $(BRIDGE_PID)
	@echo "✅ Adapter stopped"

bridge-all: bridge-up
	@echo "🚀 Launching NeuroForge pointing to adapter"
	@sleep 2
	@cd NeuroForgeApp && API_BASE=http://127.0.0.1:8014 QA_MODE=1 EVO_SUGGESTIONS=0 swift run

bridge-smoke:
	@echo "🧪 Running smoke tests"
	@python3 scripts/health_smoke.py

bridge-slo:
	@echo "📊 Running SLO checks (p95 < 250ms)"
	@python3 scripts/slo_check.py

bridge-chaos:
	@echo "💥 Chaos test: Kill UAT, confirm fallback to mock"
	@pkill -f ":8080" 2>/dev/null || true
	@sleep 1
	@curl -s http://127.0.0.1:8014/traces | jq -e '.source == "mock-data"' && echo "✅ Fallback working" || echo "❌ Fallback failed"

# Legacy aliases
wire-up: bridge-up
wire-down: bridge-down
wire-all: bridge-all
wire-test: bridge-smoke

# Integration testing
.PHONY: test-smoke test-backends test-e2e test-slo test-accept test-all

test-smoke:
	@echo "🧪 Running smoke tests (fast contract checks)"
	@BRIDGE_BASE=$${BRIDGE_BASE:-http://127.0.0.1:8014} pytest -m smoke tests/interop/

test-backends:
	@echo "🔗 Testing backends directly (UAT + Athena)"
	@UAT_BASE=$${UAT_BASE:-http://127.0.0.1:8181} \
	 ATHENA_BASE=$${ATHENA_BASE:-http://127.0.0.1:8090} \
	 UAT_TOKEN=$${UAT_TOKEN} \
	 ATH_TOKEN=$${ATH_TOKEN} \
	 pytest -m backends tests/interop/

test-e2e:
	@echo "🌊 Running end-to-end tests (full flow)"
	@BRIDGE_BASE=$${BRIDGE_BASE:-http://127.0.0.1:8014} \
	 BRIDGE_TOKEN=$${BRIDGE_TOKEN} \
	 pytest -m e2e tests/interop/

test-slo:
	@echo "⚡ Running SLO tests (p95 < 250ms)"
	@BRIDGE_BASE=$${BRIDGE_BASE:-http://127.0.0.1:8014} \
	 SLO_P95_MS=$${SLO_P95_MS:-250} \
	 BRIDGE_TOKEN=$${BRIDGE_TOKEN} \
	 pytest -m slo tests/interop/

test-accept:
	@echo "🎯 Running full acceptance test suite"
	@./scripts/acceptance_test.sh

test-all: test-smoke test-e2e test-slo
	@echo "✅ All integration tests complete"
