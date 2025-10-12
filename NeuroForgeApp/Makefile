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
	 DerivedData/Logs || true
	@echo "✅ UI tests complete - artifacts in artifacts/UITestArtifacts.zip"
