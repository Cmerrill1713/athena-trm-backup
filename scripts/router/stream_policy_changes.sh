#!/bin/bash
# Stream governance policy change events in real-time

POLICY_LOG="${POLICY_LOG:-governance/state/policy_change_events.jsonl}"

if [ ! -f "$POLICY_LOG" ]; then
  echo "❌ Policy change log not found: $POLICY_LOG"
  echo "   Creating directory..."
  mkdir -p "$(dirname "$POLICY_LOG")"
  touch "$POLICY_LOG"
fi

echo "🏛️  Streaming policy change events from: $POLICY_LOG"
echo "   Format: timestamp | event_type | reason"
echo ""

tail -f "$POLICY_LOG" | while IFS= read -r line; do
  echo "$line" | jq -r '
    "\(.timestamp[:19]) | \(.event_type | . + " " * (12 - length)) | \(.reason)"
  ' 2>/dev/null || echo "$line"
done

