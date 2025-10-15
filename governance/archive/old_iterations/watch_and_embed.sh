#!/bin/bash
# Auto-pipeline: watch for new transcripts and embed them
set -euo pipefail

ROOT="${1:-/Users/christianmerrill/Documents/GitHub}"
TRANSCRIPT_DIRS=("indydevdan_transcripts" "ai_coding_transcripts")
STATE_FILE=".embed_state.jsonl"

cd "$ROOT"
touch "$STATE_FILE"

echo "🔄 Starting auto-embed pipeline"
echo "📁 Watching: ${TRANSCRIPT_DIRS[*]}"
echo "📊 State: $STATE_FILE"
echo

iteration=0
while true; do
    ((iteration++))
    new_files=0
    
    for dir in "${TRANSCRIPT_DIRS[@]}"; do
        if [ ! -d "$dir" ]; then
            continue
        fi
        
        # Find all .txt files
        find "$dir" -name "*.txt" -type f | while read -r f; do
            # Check if already processed
            SUM=$(shasum -a 256 "$f" | awk '{print $1}')
            
            if ! grep -q "$SUM" "$STATE_FILE" 2>/dev/null; then
                echo "[embed] $f"
                if python3 AI-Projects/universal-ai-tools/scripts/embed_one.py "$f"; then
                    echo "$SUM $f $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$STATE_FILE"
                    ((new_files++))
                fi
            fi
        done
    done
    
    if [ $new_files -gt 0 ]; then
        echo "✅ Embedded $new_files new files (iteration $iteration)"
    fi
    
    # Sleep between checks
    sleep 30
done

