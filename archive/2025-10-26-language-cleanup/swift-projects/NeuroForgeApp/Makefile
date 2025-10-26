# Makefile for NeuroForgeApp Swift Development

SCHEME ?= NeuroForgeApp
WORKSPACE ?= NeuroForgeApp.xcworkspace
DEST ?= platform=macOS
CONFIG ?= Debug

.PHONY: preflight build test run lint watch all clean

preflight:
	@tools/dev/swift-preflight.sh

build:
	@SCHEME=$(SCHEME) WORKSPACE=$(WORKSPACE) CONFIG=$(CONFIG) DEST=$(DEST) tools/dev/swift-build.sh

test:
	@SCHEME=$(SCHEME) WORKSPACE=$(WORKSPACE) DEST=$(DEST) tools/dev/swift-test.sh

run:
	@APP=$(SCHEME) tools/dev/swift-run-macos.sh

lint:
	@tools/dev/swift-lint-format.sh

watch:
	@echo "👀 Watching for changes (Ctrl+C to stop)..."
	@fswatch -o Sources | xargs -n1 -I{} make build || echo "ℹ️  fswatch not found (brew install fswatch)"

all: preflight lint build test

clean:
	@echo "🧹 Cleaning build artifacts..."
	@rm -rf .build
	@rm -rf DerivedData
	@swift package clean || true
	@echo "✅ Clean complete"

# Quick shortcuts
quick-build:
	@swift build

quick-run: quick-build
	@.build/debug/$(SCHEME) &

quick-test:
	@swift test

# Development helpers
fix-concurrency:
	@echo "🔧 Building with strict concurrency checks..."
	@swift build -Xswiftc -warn-concurrency -Xswiftc -strict-concurrency=complete

check-warnings:
	@echo "⚠️  Checking for warnings..."
	@swift build 2>&1 | grep "warning:" || echo "✅ No warnings"

# Truthful build - same as CI
swift-truth:
	@set -e; xcodebuild -scheme NeuroForgeApp -destination 'platform=macOS' | xcbeautify
	@swift test

# UI Snapshots
snapshots:
	@swift test --filter PromptViewSnapshotTests

# Swift Reflex agent (auto-fixes Swift issues)
reflex:
	@python3 ../../tools/reflex/swift_reflex.py \
	  --watch "Sources/**/*.swift" \
	  --build "make swift-truth" \
	  --tests "make test" \
	  --snapshots "make snapshots"

# Pre-commit UI check
pre-commit-ui:
	@../../scripts/pre-commit-ui-check.sh

# iOS builds (if needed)
build-ios:
	@DEST="platform=iOS Simulator,name=iPhone 15" make build

test-ios:
	@DEST="platform=iOS Simulator,name=iPhone 15" make test
