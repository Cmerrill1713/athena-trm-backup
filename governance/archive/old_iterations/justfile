# AI Republic Development Tasks
# =============================
#
# Justfile for AI Republic development workflow
# Install just: brew install just
#
# Usage:
#   just          # Show available tasks
#   just test      # Run tests
#   just build     # Build everything
#   just ci        # Run CI pipeline

# Default task
default:
    @just --list

# Setup development environment
setup:
    @echo "🔧 Setting up AI Republic development environment..."
    @make setup

# Run all tests
test:
    @echo "🧪 Running AI Republic tests..."
    @make test

# Build everything
build: frontend backend
    @echo "✅ Full build complete"

# Build frontend only
frontend:
    @echo "🏗️  Building frontend..."
    @make frontend

# Build backend only
backend:
    @echo "🚀 Building backend..."
    @make backend

# Build container
docker:
    @echo "🐳 Building container..."
    @make docker

# Run CI pipeline locally
ci:
    @echo "🔬 Running CI pipeline..."
    @make ci

# Watch for changes
watch:
    @echo "👀 Starting watch mode..."
    @make watch

# Development status
status:
    @make status

# Clean everything
clean:
    @echo "🧹 Cleaning..."
    @make clean

# Full development stack
dev: setup build test
    @echo "🚀 Development stack ready!"

# Run in container
container: docker
    @echo "🐳 Starting container..."
    @make container

# Production build
ship: clean setup build test docker
    @echo "🚢 Ready for production deployment!"

# Quick aliases for common tasks
alias t := test
alias b := build
alias w := watch
alias s := status
alias c := container
