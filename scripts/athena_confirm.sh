#!/usr/bin/env bash
# Athena Confirm - Safety wrapper for destructive operations
# Usage: bash athena_confirm.sh "command description" "actual command"

set -euo pipefail

DESCRIPTION="$1"
COMMAND="$2"

# Destructive keywords that require confirmation
DESTRUCTIVE_KEYWORDS=(
    "nuke"
    "destroy"
    "promote"
    "rollback"
    "delete"
    "remove"
    "kill"
    "stop"
    "clear"
)

# Check if command contains destructive keywords
IS_DESTRUCTIVE=0
for keyword in "${DESTRUCTIVE_KEYWORDS[@]}"; do
    if echo "$COMMAND" | grep -qi "$keyword"; then
        IS_DESTRUCTIVE=1
        break
    fi
done

# Require confirmation for destructive operations
if [ $IS_DESTRUCTIVE -eq 1 ]; then
    echo "⚠️  Destructive operation: $DESCRIPTION"
    echo "   Command: $COMMAND"
    read -r -p "   Confirm [yes/no]: " answer
    
    if [ "$answer" != "yes" ]; then
        echo "❌ Cancelled"
        exit 1
    fi
fi

# Log the operation
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Voice: $DESCRIPTION → $COMMAND" >> logs/athena_voice_audit.log

# Execute
echo "🧠 Athena: Executing '$DESCRIPTION'..."
eval "$COMMAND"

