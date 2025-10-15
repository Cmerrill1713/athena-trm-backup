#!/bin/bash
# Athena Tool: Start complete stack (Bridge + Athena + UAT + Kokoro + RAG + Vision)
set -e
cd "$(dirname "$0")/.."

echo "🚀 Bringing full stack online..."
make stack-full && make truth

echo "✅ Full stack operational"
./NeuroForgeApp/scripts/validate_services.sh

