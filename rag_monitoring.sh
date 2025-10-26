#!/bin/bash
# RAG Production Monitoring Script
# ================================
# Monitor vectorizer latency, ANN recall, and cache performance

set -e

WEAVIATE_URL="${WEAVIATE_URL:-http://127.0.0.1:8090}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://127.0.0.1:9090}"

echo "📊 RAG Production Monitoring"
echo "============================"

# Function to check if service is responding
check_service() {
    local service_name=$1
    local service_url=$2
    
    if curl -s --max-time 5 "$service_url" > /dev/null 2>&1; then
        echo "✅ $service_name: UP"
        return 0
    else
        echo "❌ $service_name: DOWN"
        return 1
    fi
}

# Function to get Prometheus metric
get_metric() {
    local metric_name=$1
    local query=$2
    
    curl -s "$PROMETHEUS_URL/api/v1/query" \
        --data-urlencode "query=$query" | \
        jq -r '.data.result[0].value[1] // "N/A"'
}

echo "1️⃣ Service Health Checks"
echo "------------------------"

check_service "Weaviate" "$WEAVIATE_URL/v1/meta"
check_service "Prometheus" "$PROMETHEUS_URL/-/healthy"

echo ""
echo "2️⃣ Vectorizer Performance"
echo "-------------------------"

# Vectorizer latency (95th percentile)
VECTORIZER_LATENCY=$(get_metric "vectorizer_latency_p95" \
    'histogram_quantile(0.95, sum by(le)(rate(weaviate_module_encode_seconds_bucket{model="all-MiniLM-L6-v2"}[5m])))')

if [ "$VECTORIZER_LATENCY" != "N/A" ]; then
    echo "   Vectorizer P95 latency: ${VECTORIZER_LATENCY}s"
    
    # Check if latency is acceptable (< 1 second)
    if (( $(echo "$VECTORIZER_LATENCY < 1.0" | bc -l) )); then
        echo "   ✅ Vectorizer latency: GOOD"
    else
        echo "   ⚠️  Vectorizer latency: HIGH (>1s)"
    fi
else
    echo "   ⚠️  Vectorizer metrics: Not available"
fi

echo ""
echo "3️⃣ Vector Cache Performance"
echo "---------------------------"

# Cache hit rate
CACHE_HIT_RATE=$(get_metric "cache_hit_rate" \
    'rate(weaviate_vector_cache_hits_total[5m]) / rate(weaviate_vector_cache_lookups_total[5m])')

if [ "$CACHE_HIT_RATE" != "N/A" ]; then
    CACHE_PERCENT=$(echo "$CACHE_HIT_RATE * 100" | bc -l)
    echo "   Cache hit rate: ${CACHE_PERCENT}%"
    
    # Check if cache hit rate is good (> 80%)
    if (( $(echo "$CACHE_HIT_RATE > 0.8" | bc -l) )); then
        echo "   ✅ Cache performance: GOOD"
    else
        echo "   ⚠️  Cache performance: LOW (<80%)"
    fi
else
    echo "   ⚠️  Cache metrics: Not available"
fi

echo ""
echo "4️⃣ Query Performance"
echo "--------------------"

# Test query latency
echo "   Testing query performance..."
START_TIME=$(date +%s%N)

QUERY_RESULT=$(curl -s -X POST "$WEAVIATE_URL/v1/graphql" \
    -H "Content-Type: application/json" \
    -d '{"query":"{Get{DocsV2(nearText:{concepts:[\"monitoring test\"]} limit:5){path text _additional{distance}}}}"}' \
    --max-time 10)

END_TIME=$(date +%s%N)
QUERY_LATENCY_MS=$(( (END_TIME - START_TIME) / 1000000 ))

if echo "$QUERY_RESULT" | jq -e '.errors' > /dev/null 2>&1; then
    echo "   ❌ Query failed with errors"
    echo "$QUERY_RESULT" | jq '.errors'
else
    echo "   Query latency: ${QUERY_LATENCY_MS}ms"
    
    if [ $QUERY_LATENCY_MS -lt 500 ]; then
        echo "   ✅ Query performance: EXCELLENT (<500ms)"
    elif [ $QUERY_LATENCY_MS -lt 1000 ]; then
        echo "   ✅ Query performance: GOOD (<1000ms)"
    else
        echo "   ⚠️  Query performance: SLOW (>1000ms)"
    fi
fi

echo ""
echo "5️⃣ ANN Recall Stability"
echo "----------------------"

# Test multiple queries to check distance consistency
echo "   Testing ANN recall stability..."

DISTANCES=()
for i in {1..5}; do
    RESULT=$(curl -s -X POST "$WEAVIATE_URL/v1/graphql" \
        -H "Content-Type: application/json" \
        -d "{\"query\":\"{Get{DocsV2(nearText:{concepts:[\\\"stability test $i\\\"]} limit:1){_additional{distance}}}}\"}" \
        --max-time 10)
    
    DISTANCE=$(echo "$RESULT" | jq -r '.data.Get.DocsV2[0]._additional.distance // "N/A"')
    
    if [ "$DISTANCE" != "N/A" ]; then
        DISTANCES+=("$DISTANCE")
    fi
done

if [ ${#DISTANCES[@]} -gt 0 ]; then
    # Calculate average and standard deviation
    AVG_DISTANCE=$(printf '%s\n' "${DISTANCES[@]}" | awk '{sum+=$1} END {print sum/NR}')
    STD_DEV=$(printf '%s\n' "${DISTANCES[@]}" | awk -v avg="$AVG_DISTANCE" '{sum+=($1-avg)^2} END {print sqrt(sum/NR)}')
    
    echo "   Average distance: $AVG_DISTANCE"
    echo "   Standard deviation: $STD_DEV"
    
    # Check for distance drift (> 2σ)
    if (( $(echo "$STD_DEV < 0.1" | bc -l) )); then
        echo "   ✅ ANN stability: GOOD (low variance)"
    else
        echo "   ⚠️  ANN stability: UNSTABLE (high variance)"
    fi
else
    echo "   ⚠️  ANN stability: Cannot measure (no results)"
fi

echo ""
echo "6️⃣ Resource Usage"
echo "-----------------"

# Check memory usage (if available)
MEMORY_USAGE=$(curl -s "$WEAVIATE_URL/v1/meta" | jq -r '.memoryUsage // "N/A"')

if [ "$MEMORY_USAGE" != "N/A" ]; then
    echo "   Memory usage: $MEMORY_USAGE"
else
    echo "   Memory usage: Not available"
fi

# Check disk usage
DISK_USAGE=$(df -h /var/lib/weaviate 2>/dev/null | tail -1 | awk '{print $5}' || echo "N/A")

if [ "$DISK_USAGE" != "N/A" ]; then
    echo "   Disk usage: $DISK_USAGE"
    
    # Extract percentage
    DISK_PERCENT=$(echo "$DISK_USAGE" | sed 's/%//')
    if [ "$DISK_PERCENT" -lt 80 ]; then
        echo "   ✅ Disk usage: GOOD (<80%)"
    else
        echo "   ⚠️  Disk usage: HIGH (>80%)"
    fi
else
    echo "   Disk usage: Not available"
fi

echo ""
echo "7️⃣ Alerting Rules"
echo "-----------------"

echo "   🚨 Critical alerts:"
echo "      • Vectorizer latency > 2s"
echo "      • Cache hit rate < 50%"
echo "      • Query latency > 2s"
echo "      • ANN distance drift > 3σ"
echo "      • Memory usage > 90%"
echo "      • Disk usage > 95%"

echo ""
echo "   ⚠️  Warning alerts:"
echo "      • Vectorizer latency > 1s"
echo "      • Cache hit rate < 80%"
echo "      • Query latency > 1s"
echo "      • ANN distance drift > 2σ"
echo "      • Memory usage > 80%"
echo "      • Disk usage > 85%"

echo ""
echo "📋 Monitoring Summary"
echo "===================="
echo "   • Vectorizer: Monitor P95 latency"
echo "   • Cache: Track hit rate and evictions"
echo "   • Queries: Measure end-to-end latency"
echo "   • ANN: Watch for distance drift"
echo "   • Resources: Monitor memory and disk"
echo "   • Alerts: Set up Prometheus alerting rules"

echo ""
echo "🎯 Next Steps:"
echo "   1. Set up Prometheus alerting rules"
echo "   2. Create Grafana dashboards"
echo "   3. Configure PagerDuty/Slack notifications"
echo "   4. Run this script every 5 minutes"
echo "   5. Monitor trends over time"
