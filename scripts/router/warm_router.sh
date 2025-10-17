#!/bin/bash
# Warm up Athena Router
# Pre-loads MLX model and primes caches before production traffic

set -e

ROUTER_URL="${ROUTER_URL:-http://127.0.0.1:9113}"

echo "🔥 Warming up Athena Router..."
echo "   Router: $ROUTER_URL"

# Wait for router to be ready
echo "   Waiting for router..."
for i in {1..30}; do
  if curl -sf "$ROUTER_URL/health" > /dev/null 2>&1; then
    echo "   ✅ Router is ready"
    break
  fi
  if [ $i -eq 30 ]; then
    echo "   ❌ Router not responding after 30s"
    exit 1
  fi
  sleep 1
done

# Send warmup requests to each provider
echo "   Sending warmup requests..."

# Warmup 1: Short prompt (cache MLX model)
curl -s "$ROUTER_URL/route" \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"warmup","max_tokens":5}' > /dev/null

sleep 0.5

# Warmup 2: Code prompt (realistic workload)
curl -s "$ROUTER_URL/route" \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"def hello():\n    pass","max_tokens":20}' > /dev/null

sleep 0.5

# Warmup 3: Medium prompt (fill cache)
curl -s "$ROUTER_URL/route" \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Write a Python function to calculate fibonacci","max_tokens":50}' > /dev/null

echo "   ✅ Warmup complete"
echo ""

# Show router status
echo "📊 Router Status:"
curl -s "$ROUTER_URL/health" | jq -r '
  "   Status: \(.status)",
  "   Providers available: \(.providers | to_entries | map(select(.value.available == true)) | map(.key) | join(", "))",
  "   Cloud access: \(if .policy.allow_cloud then "enabled ⚠️" else "disabled ✅" end)"
'

echo ""
echo "✅ Router is warm and ready for traffic"

