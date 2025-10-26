#!/bin/bash
echo "🔴 CRITICAL GAPS & PLACEHOLDER ANALYSIS"
echo "========================================================================"
echo ""

total_placeholders=0
total_disabled=0
total_hardcoded=0

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔴 CRITICAL ISSUE 1: Placeholder Implementations"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "FastVLM Vision:"
if docker logs fastvlm 2>&1 | tail -20 | grep -q "Placeholder"; then
    echo "  ❌ RUNNING IN PLACEHOLDER MODE"
    ((total_placeholders++))
else
    echo "  ✅ Real implementation (or not running)"
fi

echo ""
echo "Kokoro TTS:"
if docker logs athena-kokoro 2>&1 | tail -20 | grep -q "placeholder"; then
    echo "  ❌ RUNNING IN PLACEHOLDER MODE"
    ((total_placeholders++))
else
    echo "  ✅ Real implementation"
fi

echo ""
echo "MCP Ecosystem Web Search:"
response=$(curl -s -X POST http://localhost:8412/tool/web_search \
  -H "Content-Type: application/json" \
  -d '{"arguments": {"query": "test"}}' 2>&1)
if echo "$response" | grep -q "placeholder"; then
    echo "  ❌ RETURNS PLACEHOLDER RESULTS"
    ((total_placeholders++))
else
    echo "  ✅ Real search results"
fi

echo ""
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔴 CRITICAL ISSUE 2: Disabled Features"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Autonomous Orchestrator:"
auto_status=$(curl -s http://localhost:9114/status 2>&1 | jq -r '.auto_rollback.enabled' 2>/dev/null)
if [ "$auto_status" = "false" ] || [ "$auto_status" = "null" ]; then
    echo "  ❌ AUTO-ROLLBACK DISABLED"
    ((total_disabled++))
else
    echo "  ✅ Auto-rollback enabled: $auto_status"
fi

echo ""
echo "Cloud Provider:"
router_health=$(curl -s http://localhost:9113/health 2>&1)
if echo "$router_health" | jq -r '.providers.cloud.blocked_by_policy' 2>/dev/null | grep -q "true"; then
    echo "  ✅ CLOUD CORRECTLY BLOCKED (by design)"
else
    echo "  ⚠️  Cloud status unclear"
fi

echo ""
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔴 CRITICAL ISSUE 3: Hardcoded Values"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Checking for hardcoded model names..."
if grep -q "qwen2.5:7b" AI-Projects/universal-ai-tools/api/chat.py 2>/dev/null; then
    echo "  ❌ HARDCODED MODEL in chat.py"
    ((total_hardcoded++))
else
    echo "  ✅ No hardcoded models in chat.py"
fi

echo ""
echo "Checking for hardcoded localhost..."
localhost_count=$(grep -r "localhost\|127\.0\.0\.1" ui/*.html 2>/dev/null | grep -v "http://localhost:8080" | wc -l)
if [ "$localhost_count" -gt 10 ]; then
    echo "  ⚠️  Found $localhost_count localhost references in UI"
    ((total_hardcoded++))
else
    echo "  ✅ Minimal hardcoded localhost ($localhost_count)"
fi

echo ""
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 SUMMARY OF CRITICAL GAPS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Total Placeholder Implementations: $total_placeholders"
echo "Total Disabled Features: $total_disabled"
echo "Total Hardcoded Values: $total_hardcoded"
echo ""
echo "TOTAL CRITICAL ISSUES: $((total_placeholders + total_disabled + total_hardcoded))"
echo ""
echo "========================================================================"
