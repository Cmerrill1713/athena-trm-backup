#!/bin/bash
# Athena Tool: Run end-to-end platform validation
set -e
cd "$(dirname "$0")/.."

echo "🧪 Running platform validation..."

if [ -f "./VALIDATE_PLATFORM.sh" ]; then
    ./VALIDATE_PLATFORM.sh
elif [ -f "./NeuroForgeApp/scripts/validate_services.sh" ]; then
    echo "⚠️  Full validation script not found, running service health check..."
    ./NeuroForgeApp/scripts/validate_services.sh
else
    echo "❌ No validation script found"
    exit 1
fi

echo ""
echo "✅ Platform validation complete"

