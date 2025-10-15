#!/usr/bin/env bash
# Build and run NeuroForge frontend with proper environment variables
set -euo pipefail

# Navigate to project root
cd "$(cd "$(dirname "$0")"/.. && pwd)"

echo "🔨 Building NeuroForge..."
swift build -c debug

echo ""
echo "🚀 Launching NeuroForge..."
echo "   API_BASE: ${API_BASE:-http://localhost:8014}"
echo "   QA_MODE: ${QA_MODE:-1}"
echo ""

# Launch with environment variables
API_BASE="${API_BASE:-http://localhost:8014}" \
QA_MODE="${QA_MODE:-1}" \
  "./.build/debug/NeuroForgeApp.app/Contents/MacOS/NeuroForgeApp"
