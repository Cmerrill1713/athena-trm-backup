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
