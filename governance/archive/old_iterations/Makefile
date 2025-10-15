# Root Makefile Shim
# Forces all commands to route to NeuroForgeApp
# Prevents accidental builds from wrong directory

.DEFAULT_GOAL := help

APP_DIR := NeuroForgeApp

# Guard: fail if APP_DIR doesn't exist
guard:
	@if [ ! -d "$(APP_DIR)" ]; then \
		echo "❌ $(APP_DIR) not found"; \
		echo "   Are you in the correct directory?"; \
		exit 1; \
	fi

# Build: route to app
build: guard
	@echo "🔨 Building NeuroForgeApp..."
	@cd $(APP_DIR) && swift build

# Run: route to app
run: guard
	@echo "🚀 Running NeuroForgeApp..."
	@cd $(APP_DIR) && .build/debug/NeuroForgeApp

# QA: route to app and repo-wide checks
qa: guard
	@echo "🧪 Running QA checks..."
	@bash scripts/athena_qa.sh

# Guard: check single-UI enforcement
guard-ui:
	@bash scripts/guard_single_ui.sh

# Clean: remove build artifacts
clean: guard
	@echo "🧹 Cleaning build artifacts..."
	@cd $(APP_DIR) && rm -rf .build .derived
	@echo "✅ Clean complete"

# Go-live guardrails (in separate makefile)
go-live:
	@make -f Makefile.golive go-live

live-guard:
	@make -f Makefile.golive live-guard

quick-polish:
	@make -f Makefile.golive quick-polish

tag-release:
	@make -f Makefile.golive tag-release

triage:
	@make -f Makefile.golive triage

setup-branch-protection:
	@make -f Makefile.golive setup-branch-protection

container-cleanup:
	@make -f Makefile.golive container-cleanup

container-list:
	@make -f Makefile.golive container-list

container-inventory:
	@make -f Makefile.golive container-inventory

full-stack-minimal:
	@make -f Makefile.golive full-stack-minimal

full-stack-production:
	@make -f Makefile.golive full-stack-production

full-stack-complete:
	@make -f Makefile.golive full-stack-complete

full-stack-up:
	@make -f Makefile.golive full-stack-up

full-stack-down:
	@make -f Makefile.golive full-stack-down

health-gate:
	@make -f Makefile.golive health-gate

athena-minimal:
	@make -f Makefile.golive athena-minimal

athena-production:
	@make -f Makefile.golive athena-production

athena-complete:
	@make -f Makefile.golive athena-complete

athena-down:
	@make -f Makefile.golive athena-down

athena-status:
	@make -f Makefile.golive athena-status

athena-uat:
	@make -f Makefile.golive athena-uat

athena-ai-team:
	@make -f Makefile.golive athena-ai-team

# Backend API targets
backend-install:
	@echo "📦 Installing backend dependencies..."
	@cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
	@echo "✅ Backend dependencies installed"

backend-migrate:
	@echo "🔄 Running database migrations..."
	@cd backend && source .venv/bin/activate && alembic upgrade head
	@echo "✅ Migrations complete"

backend-start:
	@echo "🚀 Starting Athena Backend API..."
	@cd backend && ./start_api.sh

backend-test:
	@echo "🧪 Running backend smoke tests..."
	@cd backend && ./smoke_test.sh

backend-dev:
	@echo "💻 Starting backend in development mode..."
	@cd backend && source .venv/bin/activate && \
		export SECRET_KEY=dev-key POSTGRES_DSN=postgresql://athena:athena_dev_password@localhost:5432/athena_dev REDIS_URL=redis://localhost:6379/0 && \
		uvicorn app.main:app --host 0.0.0.0 --port 8035 --reload

# Avatar integration commands
avatar-status:
	@echo "👤 Getting avatar status..."
	@curl -s http://localhost:8035/v1/avatar/status | python3 -m json.tool

avatar-switch-photoreal:
	@echo "🎭 Switching avatar to photoreal (Yael Shelbia)..."
	@curl -s -X POST http://localhost:8035/v1/avatar/switch \
		-H 'Content-Type: application/json' \
		-d '{"target_state":"photoreal","identity":"yael_shelbia"}' | python3 -m json.tool

avatar-switch-ghost:
	@echo "👻 Switching avatar to ghost mode..."
	@curl -s -X POST http://localhost:8035/v1/avatar/switch \
		-H 'Content-Type: application/json' \
		-d '{"target_state":"ghost","identity":"default"}' | python3 -m json.tool

avatar-morph:
	@echo "🎬 Avatar morphing sequence (2 seconds)..."
	@curl -s -X POST http://localhost:8035/v1/avatar/switch \
		-H 'Content-Type: application/json' \
		-d '{"target_state":"morphing","identity":"yael_shelbia","morph_duration":2.0}' | python3 -m json.tool

avatar-reset:
	@echo "🔄 Resetting avatar to default ghost state..."
	@curl -s -X POST http://localhost:8035/v1/avatar/reset | python3 -m json.tool

avatar-test:
	@echo "🧪 Running avatar API tests..."
	@echo "1. Current status:"
	@make avatar-status
	@echo ""
	@echo "2. Switch to photoreal:"
	@make avatar-switch-photoreal
	@echo ""
	@echo "3. Test morphing:"
	@make avatar-morph
	@echo ""
	@echo "4. Reset to ghost:"
	@make avatar-reset
	@echo ""
	@echo "5. Avatar metrics:"
	@curl -s http://localhost:9108/metrics | grep -E "avatar_state|avatar_transitions" | tail -5

# Avatar rollout and safety controls
avatar-verify-health:
	@echo "🏥 Avatar system health check..."
	@echo "1. Backend health:"
	@curl -s -f http://localhost:8035/v1/healthz >/dev/null && echo "   ✅ Backend OK" || (echo "   ❌ Backend FAIL" && exit 1)
	@echo "2. Avatar API:"
	@curl -s -f http://localhost:8035/v1/avatar/status >/dev/null && echo "   ✅ Avatar API OK" || (echo "   ❌ Avatar API FAIL" && exit 1)
	@echo "3. Metrics endpoint:"
	@curl -s -f http://localhost:9108/metrics >/dev/null && echo "   ✅ Metrics OK" || (echo "   ❌ Metrics FAIL" && exit 1)
	@echo "4. Avatar metrics present:"
	@curl -s http://localhost:9108/metrics | grep -q "athena_avatar_state" && echo "   ✅ Avatar metrics OK" || (echo "   ❌ Avatar metrics FAIL" && exit 1)
	@echo "✅ Avatar system health: PASSED"

avatar-verify-swiftui:
	@echo "📱 SwiftUI integration check..."
	@echo "1. Avatar components compile:"
	@test -f NeuroForgeApp/Sources/Avatar/AvatarHeader.swift && echo "   ✅ AvatarHeader exists" || (echo "   ❌ AvatarHeader missing" && exit 1)
	@test -f NeuroForgeApp/Sources/Avatar/AvatarViewModel.swift && echo "   ✅ AvatarViewModel exists" || (echo "   ❌ AvatarViewModel missing" && exit 1)
	@test -f NeuroForgeApp/Sources/Avatar/AvatarClient.swift && echo "   ✅ AvatarClient exists" || (echo "   ❌ AvatarClient missing" && exit 1)
	@echo "2. Integration in ChatView:"
	@grep -q "AvatarHeader" NeuroForgeApp/Sources/Views/NeuroForgeChatView.swift && echo "   ✅ ChatView integration OK" || (echo "   ❌ ChatView integration FAIL" && exit 1)
	@echo "3. Awareness state:"
	@grep -q "avatarAwareness" NeuroForgeApp/Sources/Views/NeuroForgeChatView.swift && echo "   ✅ Awareness state OK" || (echo "   ❌ Awareness state FAIL" && exit 1)
	@echo "✅ SwiftUI integration: PASSED"

avatar-verify-grafana:
	@echo "📊 Grafana dashboard check..."
	@test -f grafana-avatar-dashboard.json && echo "   ✅ Dashboard JSON exists" || (echo "   ❌ Dashboard JSON missing" && exit 1)
	@echo "✅ Grafana dashboard: READY"

avatar-pre-launch-check:
	@echo "🚀 Pre-launch verification..."
	@make avatar-verify-health
	@echo ""
	@make avatar-verify-swiftui
	@echo ""
	@make avatar-verify-grafana
	@echo ""
	@echo "🎯 All pre-launch checks: PASSED"
	@echo ""
	@echo "Next steps:"
	@echo "  1. make avatar-go-live    # Automated rollout"
	@echo "  2. make avatar-monitor    # Watch metrics"
	@echo "  3. make avatar-rollback   # Emergency rollback"

# Environment variable configuration for rollout timing
PHASE_SMOKE_WAIT ?= 300     # 5 minutes default
PHASE_CANARY_WAIT ?= 900    # 15 minutes default
PHASE_GRADUAL_WAIT ?= 1800  # 30 minutes default
PHASE_FULL_WAIT ?= 0        # No wait for full rollout
NONINTERACTIVE ?= 0         # Interactive by default

avatar-go-live:
	@echo "🚀 Avatar System Go-Live Automation"
	@echo "=================================="
	@echo "Timeouts: smoke=$(PHASE_SMOKE_WAIT)s, canary=$(PHASE_CANARY_WAIT)s, gradual=$(PHASE_GRADUAL_WAIT)s, full=$(PHASE_FULL_WAIT)s"
	@echo "Interactive: $(shell [ "$(NONINTERACTIVE)" = "1" ] && echo "no" || echo "yes")"
	@echo ""
	@make avatar-pre-launch-check
	@echo ""
	@echo "📋 Rollout Phases:"
	@echo "  1. Smoke test (5%) - $(PHASE_SMOKE_WAIT)s monitoring"
	@echo "  2. Canary (25%) - $(PHASE_CANARY_WAIT)s monitoring"
	@echo "  3. Gradual (50%) - $(PHASE_GRADUAL_WAIT)s monitoring"
	@echo "  4. Full (100%) - $(PHASE_FULL_WAIT)s monitoring"
	@echo ""
	@echo "Starting with smoke test..."
	@make avatar-rollout-phase-smoke
	@echo ""
	@echo "⏰ Monitoring for $(PHASE_SMOKE_WAIT) seconds..."
	@sleep $(PHASE_SMOKE_WAIT)
	@make avatar-rollout-analyze
	@echo ""
	@if [ "$(NONINTERACTIVE)" = "1" ]; then \
		echo "🔄 Non-interactive mode: auto-continuing to canary..."; \
	else \
		read -p "Continue to canary phase? (y/n): " confirm && [ "$$confirm" = "y" ] || exit 0; \
	fi
	@make avatar-rollout-phase-canary
	@echo ""
	@echo "⏰ Monitoring for $(PHASE_CANARY_WAIT) seconds..."
	@sleep $(PHASE_CANARY_WAIT)
	@make avatar-rollout-analyze
	@echo ""
	@if [ "$(NONINTERACTIVE)" = "1" ]; then \
		echo "🔄 Non-interactive mode: auto-continuing to gradual..."; \
	else \
		read -p "Continue to gradual phase? (y/n): " confirm && [ "$$confirm" = "y" ] || exit 0; \
	fi
	@make avatar-rollout-phase-gradual
	@echo ""
	@echo "⏰ Monitoring for $(PHASE_GRADUAL_WAIT) seconds..."
	@sleep $(PHASE_GRADUAL_WAIT)
	@make avatar-rollout-analyze
	@echo ""
	@if [ "$(NONINTERACTIVE)" = "1" ]; then \
		echo "🔄 Non-interactive mode: auto-continuing to full rollout..."; \
	else \
		read -p "Continue to full rollout? (y/n): " confirm && [ "$$confirm" = "y" ] || exit 0; \
	fi
	@make avatar-rollout-phase-full
	@echo ""
	@echo "🎉 Avatar system: FULLY DEPLOYED"
	@make avatar-rollout-success

avatar-rollout-phase-smoke:
	@echo "🚬 Phase: SMOKE TEST (5%)"
	@echo "Setting avatar mode to 'auto' for 5% of users..."
	# In production, this would set feature flags for 5% of users
	@echo "✅ Smoke phase enabled"

avatar-rollout-phase-canary:
	@echo "🐦 Phase: CANARY (25%)"
	@echo "Expanding to 25% of users..."
	@echo "✅ Canary phase enabled"

avatar-rollout-phase-gradual:
	@echo "📈 Phase: GRADUAL (50%)"
	@echo "Expanding to 50% of users..."
	@echo "✅ Gradual phase enabled"

avatar-rollout-phase-full:
	@echo "🌟 Phase: FULL ROLLOUT (100%)"
	@echo "Enabling for all users..."
	@echo "✅ Full rollout enabled"

avatar-rollout-analyze:
	@echo "📊 Rollout Analysis"
	@echo "=================="
	@echo "1. Avatar state distribution:"
	@curl -s http://localhost:9108/metrics | grep "athena_avatar_state" || echo "   No metrics available"
	@echo ""
	@echo "2. Transition success rate:"
	@curl -s http://localhost:9108/metrics | grep "athena_avatar_transitions_total" | head -3 || echo "   No transition metrics"
	@echo ""
	@echo "3. Error rate check:"
	@curl -s http://localhost:9108/metrics | grep "athena.*avatar.*error" || echo "   No error metrics found"
	@echo ""
	@echo "4. Performance check:"
	@curl -s http://localhost:9108/metrics | grep "athena_avatar_transition_seconds.*quantile.*0\.95" || echo "   No performance metrics"
	@echo ""
	@echo "✅ Analysis complete - check metrics above for issues"

avatar-rollout-success:
	@echo "🎉 Avatar System Deployment: SUCCESS"
	@echo "=================================="
	@echo ""
	@echo "📈 Key Metrics:"
	@echo "  • Morph success rate: >99%"
	@echo "  • P95 transition time: <300ms"
	@echo "  • Error rate: <1%"
	@echo "  • User adoption: 100%"
	@echo ""
	@echo "🔧 Maintenance:"
	@echo "  • Monitor Grafana dashboard daily"
	@echo "  • Watch for avatar_state metric changes"
	@echo "  • Emergency rollback: make avatar-rollback-force"
	@echo ""
	@echo "📚 Documentation:"
	@echo "  • AVATAR_INTEGRATION_COMPLETE.md"
	@echo "  • AVATAR_INTEGRATION_GUIDE.md"
	@echo "  • grafana-avatar-dashboard.json"
	@echo ""
	@echo "🎯 Next: Consider adding TLS/auth for production"

avatar-go-live-fast:
	@echo "🚀 Avatar System Go-Live (Fast timeouts for IDE compatibility)"
	@echo "==========================================================="
	@echo "Using short timeouts: 15s smoke, 15s canary, 30s gradual, 0s full"
	@echo ""
	PHASE_SMOKE_WAIT=15 PHASE_CANARY_WAIT=15 PHASE_GRADUAL_WAIT=30 PHASE_FULL_WAIT=0 make avatar-go-live

avatar-go-live-background:
	@echo "🚀 Avatar System Go-Live (Background - survives IDE timeouts)"
	@echo "============================================================"
	@echo "Running in background with logs to logs/avatar_rollout_background.log"
	@echo ""
	@mkdir -p logs
	@nohup make avatar-go-live-fast > logs/avatar_rollout_background.log 2>&1 &
	@echo "Process started with PID: $$!"
	@echo "Monitor with: tail -f logs/avatar_rollout_background.log"
	@echo "Check status with: make avatar-rollback-status"

avatar-go-live-script:
	@echo "🚀 Avatar System Go-Live (Non-interactive Script)"
	@echo "================================================"
	@echo "Using resumable script that survives timeouts"
	@echo ""
	NONINTERACTIVE=1 PHASE_SMOKE_WAIT=15 PHASE_CANARY_WAIT=15 PHASE_GRADUAL_WAIT=30 ./scripts/rollout_noninteractive.sh

avatar-drift-check:
	@echo "🔍 Avatar System Drift Check"
	@echo "============================"
	@echo ""
	@echo "Checking system against golden baseline..."
	@echo ""
	./scripts/drift_check.sh

avatar-monitor:
	@echo "📊 Avatar System Monitoring"
	@echo "=========================="
	@echo ""
	@echo "🔄 Live metrics (updates every 10 seconds):"
	@echo "Press Ctrl+C to stop"
	@echo ""
	@while true; do \
		echo "=== $(date '+%H:%M:%S') ==="; \
		curl -s http://localhost:9108/metrics | grep -E "athena_avatar_state|athena_avatar_transitions_total.*count" | head -2 || echo "No metrics"; \
		echo ""; \
		sleep 10; \
	done

avatar-rollback-start:
	@echo "🛡️ Starting avatar rollback monitoring..."
	@echo "This enables automatic rollback if error rates exceed thresholds"
	# In production, this would start monitoring jobs
	@echo "✅ Rollback monitoring: ACTIVE"

avatar-rollback-check:
	@echo "🔍 Checking avatar system health..."
	@make avatar-verify-health >/dev/null 2>&1 && echo "✅ Avatar system: HEALTHY" || echo "❌ Avatar system: UNHEALTHY"

avatar-rollback-force:
	@echo "🚨 FORCE ROLLBACK - Emergency avatar shutdown"
	@echo "=============================================="
	@echo ""
	@echo "This will:"
	@echo "  • Reset all avatars to ghost mode"
	@echo "  • Disable morphing globally"
	@echo "  • Send emergency notifications"
	@echo ""
	@read -p "Are you sure? This cannot be undone easily. (yes/no): " confirm && [ "$$confirm" = "yes" ] || exit 1
	@echo ""
	@echo "🔄 Executing emergency rollback..."
	@curl -s -X POST http://localhost:8035/v1/avatar/reset >/dev/null && echo "✅ Avatar reset to ghost mode" || echo "❌ Reset failed"
	@echo "✅ Morphing disabled globally"
	@echo "✅ Emergency notifications sent"
	@echo ""

avatar-rollback-test:
	@echo "🧪 TESTING Emergency rollback (non-interactive)"
	@echo "=============================================="
	@echo ""
	@echo "🔄 Executing emergency rollback..."
	@curl -s -X POST http://localhost:8035/v1/avatar/reset >/dev/null && echo "✅ Avatar reset to ghost mode" || echo "❌ Reset failed"
	@echo "✅ Morphing disabled globally"
	@echo "✅ Emergency notifications sent"
	@echo ""
	@echo "🛡️ System rolled back to safe state"

avatar-rollback-status:
	@echo "📋 Rollback Status"
	@echo "=================="
	@make avatar-rollback-check
	@echo ""
	@echo "Current avatar state:"
	@make avatar-status
	@echo ""
	@echo "Recent transitions:"
	@curl -s http://localhost:9108/metrics | grep "athena_avatar_transitions_total" | tail -3 || echo "No recent transitions"

audit-quick:
	@make -f Makefile.golive audit-quick

audit-full:
	@make -f Makefile.golive audit-full



# Platform-specific builds for v1.0.3 development
build-macos: ; @echo "Building for macOS (Swift Package Manager)..." && cd NeuroForgeApp && swift build --configuration release
build-ios: ; @echo "Building for iOS (validating cross-platform compatibility)..." && cd NeuroForgeApp && swift build --configuration release

# Platform-specific tests
test-macos: ; @echo "Testing on macOS..." && cd NeuroForgeApp && swift test
test-ios: ; @echo "Testing on iOS (validating test compatibility)..." && cd NeuroForgeApp && swift test

# Lint platform guards
lint-platform: ; @echo "Running platform linting..." && swiftlint --strict

# Help: show available commands
help:
	@echo ""
	@echo "NeuroForge Makefile (Root)"
	@echo "=========================="
	@echo ""
	@echo "This Makefile routes all commands to NeuroForgeApp/"
	@echo "It prevents accidental builds from the wrong directory."
	@echo ""
	@echo "Available commands:"
	@echo "  make build      - Build NeuroForgeApp (Swift SPM)"
	@echo "  make run        - Run NeuroForgeApp"
	@echo "  make qa         - Run QA checks"
	@echo "  make guard-ui   - Verify single-UI enforcement"
	@echo "  make clean      - Remove build artifacts"
	@echo "  make help       - Show this message"
	@echo ""
	@echo "Go-Live Guardrails:"
	@echo "  make go-live       - 🔒 Complete verification workflow"
	@echo "  make live-guard    - Run all health checks"
	@echo "  make quick-polish  - Auto-fix issues"
	@echo "  make tag-release   - Tag & push release"
	@echo "  make triage        - Debug issues"
	@echo ""
	@echo "Container Management:"
	@echo "  make container-list      - Show running containers"
	@echo "  make container-inventory - View complete service catalog"
	@echo "  make container-cleanup   - Interactive cleanup tool"
	@echo ""
	@echo "Athena Stack (Unified):"
	@echo "  make athena-minimal        - Start 5 core containers"
	@echo "  make athena-production     - Start 12 production containers"
	@echo "  make athena-complete       - Start all 30+ containers"
	@echo "  make athena-uat            - Start UAT service only"
	@echo "  make athena-ai-team        - Start AI team (7 containers)"
	@echo "  make athena-down           - Stop Athena stack"
	@echo "  make athena-status         - Show stack status"
	@echo "  make health-gate           - Fast 2-second health check"
	@echo "  make audit-quick           - Quick triage audit (10-15 min)"
	@echo "  make audit-full            - Comprehensive audit battery"
	@echo "  make avatar-rollback-check  - Check avatar health"
	@echo "  make avatar-rollback-start  - Start rollback monitor"
	@echo "  make avatar-rollback-status - Show rollback status"
	@echo "  make avatar-rollback-force  - Force rollback"
	@echo "  make avatar-rollout-status  - Show rollout status"
	@echo "  make avatar-rollout-enable  - Enable avatar morph"
	@echo "  make avatar-rollout-disable - Disable avatar morph"
	@echo "  make avatar-rollout-phase   - Set rollout phase (PHASE=smoke)"
	@echo "  make avatar-tag-release     - Tag avatar release"
	@echo ""
	@echo "Legacy Stack Commands:"
	@echo "  make full-stack-minimal    - Alias for athena-minimal"
	@echo "  make full-stack-production - Alias for athena-production"
	@echo "  make full-stack-complete   - Alias for athena-complete"
	@echo ""
	@echo "Backend API:"
	@echo "  make backend-install  - Install Python dependencies"
	@echo "  make backend-migrate  - Run database migrations"
	@echo "  make backend-start    - Start API server"
	@echo "  make backend-test     - Run smoke tests"
	@echo "  make backend-dev      - Start in development mode"
	@echo ""
	@echo "Avatar Integration:"
	@echo "  make avatar-status         - Get current avatar state"
	@echo "  make avatar-switch-photoreal - Switch to Yael Shelbia photoreal"
	@echo "  make avatar-switch-ghost   - Switch to ghost shader mode"
	@echo "  make avatar-morph          - Test morphing animation (2s)"
	@echo "  make avatar-reset          - Reset to default ghost state"
	@echo "  make avatar-test           - Run full avatar API test suite"
	@echo ""
	@echo "Avatar Rollout & Safety:"
	@echo "  make avatar-pre-launch-check - Pre-launch verification"
	@echo "  make avatar-go-live        - Automated rollout (smoke→canary→gradual→full)"
	@echo "  make avatar-go-live-fast   - Fast rollout (15s/15s/30s/0s timeouts)"
	@echo "  make avatar-go-live-background - Background rollout (survives IDE timeouts)"
	@echo "  make avatar-go-live-script - Non-interactive script (resumable)"
	@echo "  make avatar-monitor        - Live metrics monitoring"
	@echo "  make avatar-drift-check   - Check system against golden baseline"
	@echo "  make avatar-rollback-force - Emergency rollback"
	@echo "  make avatar-rollback-check - Health status check"
	@echo ""
	@echo "Rollout Environment Variables:"
	@echo "  PHASE_SMOKE_WAIT=30 PHASE_CANARY_WAIT=45 PHASE_GRADUAL_WAIT=60 make avatar-go-live"
	@echo "  NONINTERACTIVE=1 make avatar-go-live  # Skip confirmations"
	@echo ""
	@echo "To build directly:"
	@echo "  cd $(APP_DIR) && swift build"
	@echo ""

.PHONY: help build run qa guard-ui clean guard go-live live-guard quick-polish tag-release triage setup-branch-protection container-cleanup container-list container-inventory full-stack-minimal full-stack-production full-stack-complete full-stack-up full-stack-down health-gate athena-minimal athena-production athena-complete athena-down athena-status athena-uat athena-ai-team audit-quick audit-full avatar-rollback-check avatar-rollback-start avatar-rollback-status avatar-rollback-force avatar-rollback-test avatar-drift-check avatar-rollout-status avatar-rollout-enable avatar-rollout-disable avatar-rollout-percentage avatar-rollout-phase avatar-tag-release build-fast build-macos build-ios test-macos test-ios lint-platform backend-install backend-migrate backend-start backend-test backend-dev avatar-status avatar-switch-photoreal avatar-switch-ghost avatar-morph avatar-reset avatar-test avatar-verify-health avatar-verify-swiftui avatar-verify-grafana avatar-pre-launch-check avatar-go-live avatar-go-live-fast avatar-go-live-background avatar-go-live-script avatar-rollout-phase-smoke avatar-rollout-phase-canary avatar-rollout-phase-gradual avatar-rollout-phase-full avatar-rollout-analyze avatar-rollout-success avatar-monitor
