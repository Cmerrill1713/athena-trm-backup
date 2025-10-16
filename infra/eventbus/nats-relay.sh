#!/usr/bin/env bash
#
# NATS Event Bus Relay for Athena Governance
# Mirrors all app subjects to Athena receipts with light enrichment
#

set -euo pipefail

# Load environment
MODE="${ATHENA_MODE:-shadow}"
POLICY="${ATHENA_POLICY_VERSION:-unknown}"

echo "🔄 Setting up NATS relay: app → athena (mode=$MODE, policy=$POLICY)"

# Add relay from app events to Athena receipts
nats relay add \
  --name app-to-athena \
  --source "app.>" \
  --target "athena.receipts.app.>" \
  --transform "add:{\"trace_id\":\"\${NATS_MSG_ID}\",\"ts\":\"\${TIME_RFC3339}\",\"mode\":\"${MODE}\",\"policy\":\"${POLICY}\"}"

echo "✅ NATS relay configured"
echo ""
echo "📊 Monitor with:"
echo "   nats stream info athena.receipts"
echo "   nats consumer info athena.receipts governance-consumer"

