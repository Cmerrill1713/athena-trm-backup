# AI Republic Development Workflow
# =================================
#
# Zero-sudo, automated build/test/deploy system
#
# Usage:
#   make frontend    # Build SwiftUI app
#   make backend     # Start Python services
#   make test        # Run burn-in tests
#   make all         # Full development stack
#   make watch       # Auto-rebuild on changes
#   make docker      # Build container
#   make ci          # Run CI pipeline locally

.PHONY: all frontend backend test watch clean setup status docker ci athena-play qa qa-strict

# Configuration
AR_HOME ?= $(HOME)/.local/share/ai-republic
PYTHONPATH ?= $(AR_HOME)

# Default target
all: setup frontend backend test

# Setup development environment
setup:
	@echo "🔧 Setting up AI Republic development environment..."
	@which xcodebuild >/dev/null 2>&1 || (echo "❌ Xcode not found. Install Xcode from App Store."; exit 1)
	@which python3 >/dev/null 2>&1 || (echo "❌ Python 3 not found."; exit 1)
	@python3 --version | grep -q "Python 3.8" || echo "⚠️  Python 3.8+ recommended"
	@which docker >/dev/null 2>&1 || echo "⚠️  Docker not found - container features limited"
	@mkdir -p "$(AR_HOME)"
	@bash ~/.local/share/ai-republic/setup_aliases.sh 2>/dev/null || echo "⚠️  Alias setup optional"
	@echo "✅ Development environment ready"

# Frontend: Build SwiftUI app
frontend:
	@echo "🏗️  Building NeuroForge frontend..."
	@cd NeuroForgeApp && make build
	@echo "✅ Frontend build complete"

# Athena Play: Complete frontend build and launch with focus fixes
athena-play:
	@echo "🔧 Preparing frontend…"
	@cd NeuroForgeApp && bash scripts/strip_previews.sh
	@echo "🏗️ Building (Debug)…"
	@cd NeuroForgeApp && swift build 2>/dev/null || (echo "❌ Swift build failed"; exit 1)
	@echo "🚀 Launching…"
	@cd NeuroForgeApp && .build/debug/NeuroForgeApp &
	@echo "✅ Athena app launched with focus fixes!"
	@echo "💡 Press ⌘K to focus chat input from anywhere"

# Backend: Start Python services
backend:
	@echo "🚀 Starting AI Republic backend services..."
	@# Start MCP ecosystem if available
	@-docker-compose -f docker-compose.mcp.yml up -d 2>/dev/null || echo "⚠️  MCP services not available"
	@# Start Athena services
	@-python3 athena_scheduler.py --daemon 2>/dev/null || echo "⚠️  Athena scheduler not started"
	@-python3 athena_memory_optimizer.py --daemon 2>/dev/null || echo "⚠️  Memory optimizer not started"
	@# Start AI Republic federation
	@-cd ai_republic/phase1 && python3 phase1_deployment.sh --start 2>/dev/null || echo "⚠️  Phase 1 not available"
	@echo "✅ Backend services started (check logs for details)"

# Test: Run burn-in and spike tests
test:
	@echo "🧪 Running AI Republic burn-in tests..."
	@export PYTHONPATH="$(PYTHONPATH)" && bash "$(AR_HOME)/TEST_NOW.sh"
	@echo "✅ All tests passed"

# Docker: Build container
docker:
	@echo "🐳 Building AI Republic container..."
	@docker build -f Dockerfile.ai-republic -t ai-republic:dev .
	@echo "✅ Container built: ai-republic:dev"

# CI: Run CI pipeline locally
ci:
	@echo "🔬 Running AI Republic CI pipeline locally..."
	@# Test burn-in system
	@echo "Testing burn-in system..."
	@export PYTHONPATH="$(PYTHONPATH)" && bash "$(AR_HOME)/TEST_NOW.sh"
	@# Test frontend build
	@echo "Testing frontend build..."
	@cd NeuroForgeApp && make build >/dev/null 2>&1 && echo "✅ Frontend build OK" || echo "❌ Frontend build failed"
	@# Test container build
	@echo "Testing container build..."
	@docker build -f Dockerfile.ai-republic -t ai-republic:ci-test . >/dev/null 2>&1 && echo "✅ Container build OK" || echo "❌ Container build failed"
	@# Security scan
	@echo "Running security scan..."
	@-which bandit >/dev/null 2>&1 && bandit -r . --quiet --format txt | head -20 || echo "⚠️  Bandit not installed - security scan skipped"
	@echo "✅ CI pipeline completed"

# Watch mode: Auto-rebuild on changes
watch:
	@echo "👀 Starting watch mode (Ctrl+C to stop)..."
	@# Use fswatch if available, otherwise basic loop
	@if command -v fswatch >/dev/null 2>&1; then \
		echo "Using fswatch for efficient watching..."; \
		fswatch -o -r --exclude="\.git" --exclude="DerivedData" --exclude="__pycache__" . | \
		xargs -n1 -I{} sh -c 'echo "🔄 Changes detected, rebuilding..."; make frontend 2>/dev/null || echo "⚠️  Frontend build failed"'; \
	else \
		echo "fswatch not available, using basic watch..."; \
		while true; do \
			sleep 5; \
			if [ "$$(find . -name "*.swift" -newer /tmp/ai_republic_last_build 2>/dev/null)" ]; then \
				echo "🔄 Swift changes detected, rebuilding..."; \
				make frontend 2>/dev/null || echo "⚠️  Frontend build failed"; \
				touch /tmp/ai_republic_last_build; \
			fi; \
		done; \
	fi

# Status: Show current state
status:
	@echo "📊 AI Republic Development Status"
	@echo "=================================="
	@echo ""
	@echo "🏗️  Frontend:"
	@-ls -la NeuroForgeApp/build/*.app 2>/dev/null && echo "   ✅ App built" || echo "   ❌ App not built"
	@echo ""
	@echo "🚀 Backend Services:"
	@-pgrep -f "athena_scheduler" >/dev/null && echo "   ✅ Athena scheduler running" || echo "   ❌ Athena scheduler not running"
	@-pgrep -f "memory_optimizer" >/dev/null && echo "   ✅ Memory optimizer running" || echo "   ❌ Memory optimizer not running"
	@-docker ps | grep -q mcp && echo "   ✅ MCP ecosystem running" || echo "   ❌ MCP ecosystem not running"
	@echo ""
	@echo "🐳 Container:"
	@-docker images | grep -q ai-republic && echo "   ✅ Container built" || echo "   ❌ Container not built"
	@echo ""
	@echo "🧪 Testing:"
	@echo "   AR_HOME: $(AR_HOME)"
	@echo "   PYTHONPATH: $(PYTHONPATH)"
	@-test -f "$(AR_HOME)/TEST_NOW.sh" && echo "   ✅ Test runner available" || echo "   ❌ Test runner missing"
	@-bash "$(AR_HOME)/TEST_NOW.sh" >/dev/null 2>&1 && echo "   ✅ Tests pass" || echo "   ❌ Tests fail"
	@echo ""
	@echo "💡 Quick Commands:"
	@echo "   make frontend    # Build SwiftUI app"
	@echo "   make backend     # Start services"
	@echo "   make test        # Run tests"
	@echo "   make docker      # Build container"
	@echo "   make ci          # Run CI locally"
	@echo "   make watch       # Auto-rebuild"
	@echo "   make clean       # Clean everything"

# Clean all artifacts
clean:
	@echo "🧹 Cleaning AI Republic development artifacts..."
	@# Frontend clean
	@cd NeuroForgeApp && make clean 2>/dev/null || echo "⚠️  Frontend clean failed"
	@# Backend services
	@-pkill -f "athena_scheduler" 2>/dev/null || true
	@-pkill -f "memory_optimizer" 2>/dev/null || true
	@-docker-compose -f docker-compose.mcp.yml down 2>/dev/null || true
	@# Python cache
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@# Docker cleanup
	@-docker rmi ai-republic:dev ai-republic:ci-test 2>/dev/null || true
	@# Test artifacts
	@-rm -rf /tmp/athena_* 2>/dev/null || true
	@echo "✅ Clean complete"

# Development shortcuts
dev: setup
	@echo "🚀 Starting full development stack..."
	@make frontend
	@make backend
	@echo "🎯 Development stack ready!"
	@echo ""
	@echo "💡 Next steps:"
	@echo "   1. Open NeuroForgeApp/NeuroForgeApp.xcworkspace in Xcode"
	@echo "   2. Run the app (Cmd+R)"
	@echo "   3. Test features in the UI"
	@echo "   4. Run 'make test' to verify burn-in tests"
	@echo "   5. Use 'make watch' for auto-rebuild"

# Container shortcuts
container: docker
	@echo "🐳 Starting AI Republic container..."
	@docker run -it --rm -v $(PWD):/app -v $(AR_HOME):/home/developer/.local/share/ai-republic \
		-e PYTHONPATH=/home/developer/.local/share/ai-republic:/app \
		-e AR_HOME=/home/developer/.local/share/ai-republic \
		ai-republic:dev bash

# Production shortcuts
ship: clean setup
	@echo "🚢 Preparing for production deployment..."
	@make frontend
	@make test
	@make docker
	@echo "✅ Ready for production"
	@echo ""
	@echo "💡 Deployment checklist:"
	@echo "   □ Run 'make test' - all tests pass"
	@echo "   □ Archive app in Xcode for distribution"
	@echo "   □ Deploy backend services to production"
	@echo "   □ Push container: docker push ai-republic:dev"
	@echo "   □ Update AR_HOME paths for production environment"
	@echo "   □ Verify emergency spike tests in production"

# Set your iPhone destination here (E.164 format like +15551234567)
IPHONE_DEST ?= +15551234567

# Audit targets
audit-smoke:
	@echo "🧪 Running Comprehensive Evaluation Audit (Smoke)..."
	@FAST_TIMEOUT=900 IPHONE_DEST=$(IPHONE_DEST) bash scripts/audit_smoke.sh

audit-triage:
	@echo "🔍 Running Audit Triage Helper..."
	@bash scripts/audit_triage.sh

audit-checklist:
	@echo "📋 Running Audit Operator Checklist..."
	@FAST_TIMEOUT=900 IPHONE_DEST=$(IPHONE_DEST) bash scripts/audit_checklist.sh

audit-notify:
	@echo "📱 Testing iPhone notification..."
	@./scripts/notify_iphone.sh "$(IPHONE_DEST)" "🔔 Test notification from $$(hostname)"

# Athena UI test for focus regression
ui-test-focus:
	@echo "🧪 Running typing focus UI test..."
	@xcodebuild -scheme NeuroForgeApp -destination 'platform=macOS' test \
		-only-testing:AthenaUITests/TypingFocusTests 2>&1 | \
		grep -E "(Test Case|passed|failed|Testing started)" || true
	@echo "✅ Focus UI test complete"

# Help target
help:
	@echo "AI Republic Development Workflow"
	@echo "==============================="
	@echo ""
	@echo "Primary Targets:"
	@echo "  make all         # Full development setup"
	@echo "  make frontend    # Build SwiftUI app"
	@echo "  make backend     # Start Python services"
	@echo "  make test        # Run burn-in tests"
	@echo "  make docker      # Build container"
	@echo "  make ci          # Run CI pipeline locally"
	@echo "  make audit-smoke # Comprehensive evaluation audit"
	@echo "  make audit-triage # Audit results diagnostic helper"
	@echo "  make audit-checklist # Operator checklist (run after changes)"
	@echo "  make audit-notify # Test iPhone notification"
	@echo "  make watch       # Auto-rebuild on changes"
	@echo "  make clean       # Clean all artifacts"
	@echo ""
	@echo "Development:"
	@echo "  make setup       # Initialize environment"
	@echo "  make dev         # Full development stack"
	@echo "  make container   # Run in container"
	@echo "  make status      # Show current state"
	@echo ""
	@echo "Production:"
	@echo "  make ship        # Prepare for deployment"
	@echo ""
	@echo "Configuration:"
	@echo "  AR_HOME=$(AR_HOME)"
	@echo "  PYTHONPATH=$(PYTHONPATH)"
	@echo ""
	@echo "For more help, see README.md or individual target comments"
# --- Frontside hooks ---
.PHONY: frontside-build frontside-run frontside-e2e show-critical show-tribunal show-emergency

XCB_FLAGS = -scheme NeuroForgeApp -configuration Debug \
            -destination 'platform=macOS' \
            -derivedDataPath Build

frontside-build:
	@bash scripts/strip_previews.sh || true
	@cd NeuroForgeApp && swift build

frontside-run: frontside-build
	@cd NeuroForgeApp && .build/debug/NeuroForgeApp &

frontside-e2e: frontside-build
	@cd NeuroForgeApp && ATHENA_E2E=1 .build/debug/NeuroForgeApp
	@echo "Waiting for E2E report…"; \
	for i in $$(seq 1 30); do \
		test -f $$HOME/athena_e2e.json && { echo "OK:"; cat $$HOME/athena_e2e.json; exit 0; }; \
		sleep 0.3; \
	done; \
	echo "No E2E report produced" >&2; exit 1

show-critical: frontside-build ; APP_PATH_OVERRIDE=.build/debug/NeuroForgeApp.app bin/athenactl show-critical
show-tribunal: frontside-build ; APP_PATH_OVERRIDE=.build/debug/NeuroForgeApp.app bin/athenactl show-tribunal
show-emergency: frontside-build ; APP_PATH_OVERRIDE=.build/debug/NeuroForgeApp.app bin/athenactl show-emergency

# --- QA Sweep ---
qa:
	@bash scripts/athena_qa.sh

qa-strict:
	@set -e; \
	 swiftlint --strict; \
	 swiftformat --lint NeuroForgeApp/Sources; \
	 bandit -r scripts src 2>/dev/null || true; \
	 sqlfluff lint sql 2>/dev/null || true
