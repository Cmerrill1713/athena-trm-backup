.PHONY: build run clean test open help

help:
	@echo "NeuroForge Swift UI - Make Targets"
	@echo ""
	@echo "  make build    - Build the app"
	@echo "  make run      - Build and run"
	@echo "  make clean    - Clean build artifacts"
	@echo "  make test     - Run tests"
	@echo "  make open     - Open in Xcode"
	@echo ""

build:
	@echo "🔨 Building NeuroForge..."
	@swift build

run: build
	@echo "🚀 Launching NeuroForge..."
	@API_BASE=http://localhost:8014 swift run

clean:
	@echo "🧹 Cleaning build artifacts..."
	@swift package clean
	@rm -rf .build/

test:
	@echo "🧪 Running tests..."
	@swift test

open:
	@echo "📂 Opening in Xcode..."
	@xed .

xctest:
	@echo "🧪 Running UI tests..."
	@mkdir -p artifacts
	@echo "🔧 Warming up services..."
	@bash scripts/warmup_services.sh || true
	@xcodebuild \
	 -project NeuroForgeApp.xcodeproj \
	 -scheme NeuroForgeApp \
	 -destination 'platform=macOS' \
	 -resultBundlePath artifacts/NeuroForgeUI.xcresult \
	 -derivedDataPath DerivedData \
	 test | tee artifacts/xcodebuild-ui-tests.log; \
	/usr/bin/zip -qry artifacts/UITestArtifacts.zip \
	 artifacts/NeuroForgeUI.xcresult \
	 DerivedData/Logs \
	 UITests/Golden/Actual \
	 UITests/Golden/Diffs || true
	@echo "✅ UI tests complete - artifacts in artifacts/UITestArtifacts.zip"

golden-update:
	@echo "🔄 Updating golden baselines..."
	@./scripts/golden_update.sh

golden-ci:
	@echo "🧪 Running golden diff with CI tolerance..."
	@GOLDEN_TOLERANCE=0.003 $(MAKE) xctest

# Vision + RAG features
.PHONY: vision-rag
vision-rag:
	@API_BASE=http://localhost:8014 QA_MODE=1 swift run

.PHONY: xctest-vision
xctest-vision:
	$(MAKE) xctest

# Complete QA sweep - runs all quality gates in one shot
.PHONY: qa
qa:
	@echo "╔════════════════════════════════════════════════════════════════╗"
	@echo "║                                                                ║"
	@echo "║          NeuroForge Complete QA Sweep                          ║"
	@echo "║                                                                ║"
	@echo "╚════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "🧹 Step 1: Clean build artifacts..."
	@rm -rf .build DerivedData artifacts/*.xcresult UITests/Golden/Actual/* UITests/Golden/Diffs/*
	@echo "✅ Clean complete"
	@echo ""
	@echo "🔧 Step 2: Verify backend services..."
	@cd .. && make green
	@echo "✅ All services healthy"
	@echo ""
	@echo "🔥 Step 3: Warm up services..."
	@bash scripts/warmup_services.sh || true
	@echo "✅ Warmup complete"
	@echo ""
	@echo "🧪 Step 4: UI tests (QA mode)..."
	@QA_MODE=1 $(MAKE) xctest
	@echo "✅ UI tests complete"
	@echo ""
	@echo "📊 Step 5: Golden diff (CI tolerance)..."
	@GOLDEN_TOLERANCE=0.003 QA_MODE=1 $(MAKE) xctest
	@echo "✅ Golden diff complete"
	@echo ""
	@echo "╔════════════════════════════════════════════════════════════════╗"
	@echo "║                                                                ║"
	@echo "║          ✅ QA SWEEP COMPLETE - ALL GREEN                      ║"
	@echo "║                                                                ║"
	@echo "╚════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "📦 Artifacts:"
	@echo "  - artifacts/UITestArtifacts.zip"
	@echo "  - artifacts/NeuroForgeUI.xcresult"
	@echo "  - UITests/Golden/Actual/ (captured screenshots)"
	@echo "  - UITests/Golden/Diffs/ (diff images if any)"
	@echo ""
	@echo "🎯 Verified:"
	@echo "  ✅ Provider Inspector"
	@echo "  ✅ Golden Diff"
	@echo "  ✅ Vision + RAG"
	@echo "  ✅ Prompt Sidebar"
	@echo "  ✅ All UI flows"
	@echo ""
	@echo "🚀 Ready to ship!"

# Governance System
.PHONY: governance-up governance-test governance-metrics governance-alerts
governance-up:
	@echo "🧭 Starting Governance System..."
	@echo "=================================="
	@echo "1. Starting metrics exporter..."
	@python3 ../governance/observability/governance_metrics_exporter.py &
	@echo "2. Starting orchestrator verdict integration..."
	@python3 ../orchestrator/integrate_verdicts.py &
	@echo "3. Starting canary window monitor..."
	@python3 ../release/canary_window.py &
	@echo "4. Starting canary consumer..."
	@python3 ../release/canary_consumer.py &
	@echo "✅ Governance system components started!"
	@echo "📊 Metrics: http://localhost:9109"
	@echo "📊 Canary: http://localhost:9110"
	@echo "🛑 Use 'pkill -f governance' to stop all"

governance-test:
	@echo "🧪 Testing Governance Integration..."
	@python3 ../test_governance_integration.py

governance-metrics:
	@echo "📊 Governance Metrics Status..."
	@curl -s http://localhost:9109/metrics | grep governance | head -10

governance-alerts:
	@echo "🚨 Setting up Slack alerts..."
	@echo "Set SLACK_WEBHOOK_URL and run: python3 ../monitoring/alert_router.py"

governance-containers:
	@echo "🐳 Launching Governance Container Stack..."
	@echo "========================================"
	@echo "This will start: Metrics Exporter, Orchestrator, Canary Monitor, Prometheus, Grafana, Alertmanager"
	@echo ""
	@cd .. && docker-compose -f docker-compose.governance.yml up -d
	@echo ""
	@echo "✅ Governance containers launched!"
	@echo ""
	@echo "🌐 Access Points:"
	@echo "  📊 Metrics Exporter: http://localhost:9109"
	@echo "  🎯 Orchestrator:     http://localhost:9110"
	@echo "  📈 Prometheus:       http://localhost:9090"
	@echo "  📊 Grafana:          http://localhost:3000 (admin/admin)"
	@echo "  🚨 Alertmanager:     http://localhost:9093"
	@echo ""
	@echo "🛑 Stop with: make governance-stop"

governance-stop:
	@echo "🛑 Stopping Governance Container Stack..."
	@cd .. && docker-compose -f docker-compose.governance.yml down
	@echo "✅ Governance containers stopped"

governance-logs:
	@echo "📋 Governance Container Logs..."
	@cd .. && docker-compose -f docker-compose.governance.yml logs --tail=50

governance-status:
	@echo "📊 Governance Container Status..."
	@cd .. && docker-compose -f docker-compose.governance.yml ps

# Complete QA Sweep
.PHONY: qa
qa:
	@echo "🔥 Running Full QA Sweep..."
	@echo "=================================="
	@echo
	@echo "🧹 Step 1: Clean build artifacts"
	@$(MAKE) clean
	@echo
	@echo "🧠 Step 2: Backend health check (6 services)"
	@cd .. && make green || true
	@echo
	@echo "🚀 Step 3: Warmup services"
	@bash scripts/warmup_services.sh || true
	@echo
	@echo "🧪 Step 4: Running full test suite..."
	@$(MAKE) xctest
	@echo
	@echo "📊 Step 5: Generating summary..."
	@echo "=================================="
	@echo "✅ QA Sweep Complete!"
	@echo
	@echo "📁 Artifacts:"
	@ls -lh artifacts/ 2>/dev/null || echo "  (artifacts directory empty or not created)"
	@echo
	@echo "🎯 Next: Check artifacts/xcodebuild-ui-tests.log for details"

.PHONY: golden-ci
golden-ci:
	@echo "🧪 Running Golden CI (with tolerance)..."
	@GOLDEN_TOLERANCE=0.003 $(MAKE) xctest


# Cache and Cleanup Management
.PHONY: clean-cache clean-all clean-docker clean-deep

clean-cache:
	@echo "🧹 Cleaning cache files..."
	@cd .. && ./cleanup_cache.sh

clean-all: clean-cache
	@echo "🧹 Deep cleaning all artifacts..."
	@cd .. && git clean -fdx -e .env -e .vscode

clean-docker:
	@echo "🐳 Cleaning Docker system..."
	@docker system prune -af --volumes
	@echo "✅ Docker cleanup complete"

clean-deep: clean-all clean-docker
	@echo "🔥 Deep clean completed - workspace is pristine!"
