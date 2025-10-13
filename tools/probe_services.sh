#!/bin/bash
# Athena Tool: Quick health check for all services
cd "$(dirname "$0")/.."

echo "🔍 Probing all services..."
./NeuroForgeApp/scripts/validate_services.sh

