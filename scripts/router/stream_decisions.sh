#!/bin/bash
# Stream router decisions in real-time
# Formats JSONL for easy reading

DECISION_LOG="${DECISION_LOG:-state/router_decisions.jsonl}"

if [ ! -f "$DECISION_LOG" ]; then
  echo "❌ Decision log not found: $DECISION_LOG"
  echo "   Router may not be running or has no decisions yet"
  exit 1
fi

echo "📊 Streaming router decisions from: $DECISION_LOG"
echo "   Format: timestamp | route | latency | tokens | ECE | cached"
echo ""

tail -f "$DECISION_LOG" | while IFS= read -r line; do
  echo "$line" | jq -r '
    "\(.timestamp[:19]) | \(.route | . + " " * (10 - length)) | \(.latency_ms)ms | \(.tokens_generated // 0)tok | $\(.ece_estimate // 0) | \(if .cached then "💾" else "  " end)"
  ' 2>/dev/null || echo "$line"
done

