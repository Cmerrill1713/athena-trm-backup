#!/usr/bin/env bash
# FastVLM Health Check - Quick health verification
# Returns 0 if healthy, 1 if not

ENDPOINT="http://127.0.0.1:8811/health"
TIMEOUT=5

# Check if server responds
if ! response=$(curl -s --max-time $TIMEOUT "$ENDPOINT" 2>/dev/null); then
    echo "❌ FastVLM server not responding"
    exit 1
fi

# Parse health status
status=$(echo "$response" | jq -r '.status' 2>/dev/null)

if [ "$status" = "healthy" ]; then
    model=$(echo "$response" | jq -r '.model' 2>/dev/null)
    echo "✅ FastVLM healthy: $model"
    exit 0
else
    echo "❌ FastVLM unhealthy: $status"
    exit 1
fi

