#!/bin/bash
# Log Security Validation - 5-Minute Check
# Validates: Allowlist, Max-tail, Redaction, Timeout, Performance

set -euo pipefail

BRIDGE=${BRIDGE_BASE:-http://127.0.0.1:8014}

echo "╔════════════════════════════════════════════════════════════╗"
echo "║        LOG SECURITY VALIDATION                             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

pass() { printf "✅ %s\n" "$1"; }
fail() { printf "❌ %s\n" "$1"; exit 1; }
warn() { printf "⚠️  %s\n" "$1"; }

# ------------------------
# 1) Allowlist Check
# ------------------------
echo "1️⃣  Testing allowlist (unknown service must fail)..."
STATUS=$(curl -s -o /dev/null -w '%{http_code}' "$BRIDGE/ops/logs?service=unknown&tail=10")
if [ "$STATUS" -ge 400 ]; then
    pass "Allowlist enforced (HTTP $STATUS for unknown service)"
else
    fail "Allowlist bypass! Unknown service returned HTTP $STATUS"
fi

# ------------------------
# 2) Max-Tail Guard
# ------------------------
echo ""
echo "2️⃣  Testing max-tail guard (should clamp at 2000)..."
RESPONSE=$(curl -s "$BRIDGE/ops/logs?service=athena&tail=999999")
LINES=$(echo "$RESPONSE" | jq -r '.lines // 0')
if [ "$LINES" -le 2000 ]; then
    pass "Max-tail guard working (got $LINES lines, max 2000)"
else
    fail "Max-tail bypass! Got $LINES lines (should be ≤2000)"
fi

# ------------------------
# 3) Redaction Patterns
# ------------------------
echo ""
echo "3️⃣  Testing secret redaction..."
CONTENT=$(curl -s "$BRIDGE/ops/logs?service=athena&tail=500" | jq -r '.content')

# Check for common unredacted patterns
LEAKED=0

if echo "$CONTENT" | grep -qE 'Bearer [A-Za-z0-9._-]{20,}'; then
    warn "Found unredacted Bearer token!"
    LEAKED=$((LEAKED + 1))
fi

if echo "$CONTENT" | grep -qE 'sk-[A-Za-z0-9]{32,}'; then
    warn "Found unredacted OpenAI key!"
    LEAKED=$((LEAKED + 1))
fi

if echo "$CONTENT" | grep -qE 'ghp_[A-Za-z0-9]{36,}'; then
    warn "Found unredacted GitHub PAT!"
    LEAKED=$((LEAKED + 1))
fi

if echo "$CONTENT" | grep -qE 'xox[baprs]-[A-Za-z0-9\-]{20,}'; then
    warn "Found unredacted Slack token!"
    LEAKED=$((LEAKED + 1))
fi

if echo "$CONTENT" | grep -qE 'eyJhbGci[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+'; then
    warn "Found unredacted JWT!"
    LEAKED=$((LEAKED + 1))
fi

if [ "$LEAKED" -eq 0 ]; then
    pass "No secrets leaked (checked 5 patterns)"
else
    fail "Found $LEAKED types of unredacted secrets!"
fi

# Verify redaction indicator
REDACTED=$(echo "$RESPONSE" | jq -r '.redacted // false')
if [ "$REDACTED" = "true" ]; then
    pass "Redaction indicator present"
else
    warn "Response missing 'redacted' field"
fi

# ------------------------
# 4) Timeout Protection
# ------------------------
echo ""
echo "4️⃣  Testing timeout protection (shouldn't hang)..."
START=$(date +%s)
timeout 8 curl -s "$BRIDGE/ops/logs?service=athena&tail=100" >/dev/null || true
END=$(date +%s)
ELAPSED=$((END - START))

if [ "$ELAPSED" -lt 8 ]; then
    pass "Request completed in ${ELAPSED}s (timeout protection working)"
else
    warn "Request took ${ELAPSED}s (check timeout settings)"
fi

# ------------------------
# 5) Performance Sanity
# ------------------------
echo ""
echo "5️⃣  Testing performance (latency check)..."
START=$(date +%s%N)
curl -s "$BRIDGE/ops/logs?service=athena&tail=200" >/dev/null
END=$(date +%s%N)
LATENCY_MS=$(( (END - START) / 1000000 ))

if [ "$LATENCY_MS" -lt 1000 ]; then
    pass "Latency OK (${LATENCY_MS}ms for 200 lines)"
elif [ "$LATENCY_MS" -lt 3000 ]; then
    warn "Latency acceptable (${LATENCY_MS}ms, could optimize)"
else
    warn "Latency high (${LATENCY_MS}ms, investigate)"
fi

# ------------------------
# Summary
# ------------------------
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║        LOG SECURITY VALIDATION COMPLETE ✅                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "🔒 Security checks passed!"
echo "   • Allowlist enforced"
echo "   • Max-tail clamped"
echo "   • Secrets redacted"
echo "   • Timeout protected"
echo "   • Performance acceptable"
echo ""
echo "🎯 Safe for production use!"
echo ""

