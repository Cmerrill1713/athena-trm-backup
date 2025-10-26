#!/usr/bin/env bash
# TRM A/B Testing Harness
# Compares adaptive policy vs static policy performance

set -euo pipefail

DUR="${1:-1800}"   # seconds (default 30 min)
PCT="${2:-0.5}"    # traffic to adaptive (default 50%)

echo "══════════════════════════════════════════════════════════"
echo "  🧪 TRM A/B TEST"
echo "══════════════════════════════════════════════════════════"
echo "Duration: ${DUR}s"
echo "Adaptive traffic: ${PCT} ($(echo "$PCT * 100" | bc)%)"
echo "Static traffic: $(echo "1 - $PCT" | bc)"
echo ""

END=$(( $(date +%s) + DUR ))
COUNT_ADAPTIVE=0
COUNT_STATIC=0

echo "Starting traffic generation..."
echo ""

while [ "$(date +%s)" -lt "$END" ]; do
  # Flip a biased coin
  if awk -v r="$PCT" 'BEGIN{srand(); exit !(rand()<r)}'; then
    ADAPTIVE=1
    ((COUNT_ADAPTIVE++))
  else
    ADAPTIVE=0
    ((COUNT_STATIC++))
  fi

  # Send request with adaptive flag
  curl -s -X POST "http://localhost:8000/api/execute" \
    -H 'Content-Type: application/json' \
    -d "{
      \"objective\":\"Explain how the AGI planner works with TRM\",
      \"tools\":[],
      \"max_steps\":4,
      \"flags\":{\"adaptive_trm\":$ADAPTIVE}
    }" >/dev/null 2>&1 || true
  
  # Progress indicator
  if [ $((COUNT_ADAPTIVE + COUNT_STATIC)) -eq 1 ] || [ $(((COUNT_ADAPTIVE + COUNT_STATIC) % 50)) -eq 0 ]; then
    echo "  Requests sent: $((COUNT_ADAPTIVE + COUNT_STATIC)) (adaptive: $COUNT_ADAPTIVE, static: $COUNT_STATIC)"
  fi
  
  sleep 0.25
done

echo ""
echo "══════════════════════════════════════════════════════════"
echo "  ✅ A/B Test Complete"
echo "══════════════════════════════════════════════════════════"
echo "Total requests: $((COUNT_ADAPTIVE + COUNT_STATIC))"
echo "  - Adaptive policy: $COUNT_ADAPTIVE"
echo "  - Static policy: $COUNT_STATIC"
echo ""
echo "📊 Check metrics with:"
echo "  make trm-metrics"
echo "  curl -s http://localhost:9093/metrics | grep trm_policy"
echo ""
echo "Compare success rates, latency P95, and context waste ratio."

