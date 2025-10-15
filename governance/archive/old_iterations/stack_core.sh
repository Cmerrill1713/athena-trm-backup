#!/bin/bash
# Athena Tool: Start core services (Bridge + Athena + UAT)
set -e
cd "$(dirname "$0")/.."

echo "🚀 Bringing core services online..."
make stack-up && make truth

echo "✅ Core services operational"

