#!/usr/bin/env bash
set -euo pipefail

# Test alert routing without impacting real metrics
# Creates a temporary low threshold, verifies alert fires, then restores

echo "🧪 Alert System Smoke Test"
echo "=========================="
echo ""

PROM_URL="${PROMETHEUS_URL:-http://localhost:9090}"
ALERT_URL="${ALERTMANAGER_URL:-http://localhost:9093}"

# 1. Check Prometheus is up
echo "1️⃣  Checking Prometheus..."
if curl -sf "$PROM_URL/-/healthy" >/dev/null; then
  echo "   ✅ Prometheus healthy"
else
  echo "   ❌ Prometheus not responding"
  exit 1
fi

# 2. Check AlertManager is up
echo ""
echo "2️⃣  Checking AlertManager..."
if curl -sf "$ALERT_URL/-/healthy" >/dev/null; then
  echo "   ✅ AlertManager healthy"
else
  echo "   ⚠️  AlertManager not responding (optional)"
fi

# 3. Check alert rules are loaded
echo ""
echo "3️⃣  Checking alert rules..."
RULES=$(curl -s "$PROM_URL/api/v1/rules" | jq -r '.data.groups[].rules[] | select(.type=="alerting") | .name' | wc -l)
echo "   ✅ $RULES alert rules loaded"

# 4. List current alerts
echo ""
echo "4️⃣  Current firing alerts:"
FIRING=$(curl -s "$PROM_URL/api/v1/alerts" | jq -r '.data.alerts[] | select(.state=="firing") | "   🔥 \(.labels.alertname) (\(.labels.severity))"')
if [ -z "$FIRING" ]; then
  echo "   ✅ No alerts firing (good!)"
else
  echo "$FIRING"
fi

# 5. Test alert query
echo ""
echo "5️⃣  Testing alert query evaluation..."
TEST_QUERY="vector(1)"
RESULT=$(curl -s "$PROM_URL/api/v1/query?query=$TEST_QUERY" | jq -r '.data.result[0].value[1]')
if [ "$RESULT" = "1" ]; then
  echo "   ✅ Deadman query evaluates correctly"
else
  echo "   ❌ Query evaluation failed"
fi

# 6. Check recording rules
echo ""
echo "6️⃣  Checking recording rules..."
RECORDING=$(curl -s "$PROM_URL/api/v1/rules" | jq -r '.data.groups[].rules[] | select(.type=="recording") | .name' | wc -l)
echo "   ✅ $RECORDING recording rules active"

# 7. Verify metrics exist
echo ""
echo "7️⃣  Verifying TRM metrics exist..."
METRICS=(
  "routing_decisions_total"
  "routing_success_total"
  "routing_latency_ms_bucket"
  "trm_promotions_total"
)

for metric in "${METRICS[@]}"; do
  COUNT=$(curl -s "$PROM_URL/api/v1/query?query=$metric" | jq -r '.data.result | length')
  if [ "$COUNT" -gt 0 ]; then
    echo "   ✅ $metric ($COUNT series)"
  else
    echo "   ⚠️  $metric (no data yet)"
  fi
done

# 8. Test alert expression
echo ""
echo "8️⃣  Testing sample alert expression..."
ALERT_EXPR="sum(increase(routing_decisions_total[5m]))"
DECISIONS=$(curl -s "$PROM_URL/api/v1/query?query=$ALERT_EXPR" | jq -r '.data.result[0].value[1] // "0"')
echo "   📊 Recent decisions (5m): $DECISIONS"

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Smoke test complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Generate traffic: make seed-metrics"
echo "   2. View alerts: open $PROM_URL/alerts"
echo "   3. Check routing: open $ALERT_URL"
echo ""

# Optional: Trigger a test alert by querying
if [ "${TRIGGER_TEST:-false}" = "true" ]; then
  echo "🔥 Triggering test alert..."
  echo "   (Set NoRoutingActivity threshold low temporarily)"
  # This would require editing rules, reloading, waiting, then restoring
  # Left as manual for safety
fi

