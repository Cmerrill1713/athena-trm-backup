#!/usr/bin/env bash
# Athena CLI Chat - Uses your working LLM Gateway
# Backend: http://127.0.0.1:8015

set -euo pipefail

GATEWAY="http://127.0.0.1:8015/v1/chat/completions"
BOLD='\033[1m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BOLD}==================================${NC}"
echo -e "${BOLD}   Athena CLI Chat (Local AI)${NC}"
echo -e "${BOLD}==================================${NC}"
echo ""
echo "Backend: LLM Gateway (qwen2.5:0.5b via Ollama)"
echo "Type 'exit' or 'quit' to end chat"
echo ""

# Check if gateway is running
if ! curl -sf http://127.0.0.1:8015/health > /dev/null 2>&1; then
    echo "❌ Error: LLM Gateway not running on port 8015"
    echo ""
    echo "Start it with:"
    echo "  cd /Users/christianmerrill/Documents/GitHub"
    echo "  python3 services/llm_gateway/app.py &"
    exit 1
fi

# Chat loop
while true; do
    # Prompt
    echo -ne "${GREEN}You:${NC} "
    read -r input
    
    # Exit conditions
    if [[ -z "$input" ]] || [[ "$input" == "exit" ]] || [[ "$input" == "quit" ]]; then
        echo ""
        echo "Goodbye! 👋"
        break
    fi
    
    # Call LLM Gateway with Athena personality
    echo -ne "${BLUE}Athena:${NC} "
    
    # Escape input for JSON
    escaped_input=$(echo "$input" | jq -Rs .)
    
    response=$(curl -s "$GATEWAY" \
        -H "Content-Type: application/json" \
        -d "{
            \"messages\": [
                {
                    \"role\": \"system\",
                    \"content\": \"You are Athena, a helpful and knowledgeable AI assistant. You provide clear, accurate, and concise answers. You're friendly but professional.\"
                },
                {
                    \"role\": \"user\",
                    \"content\": $escaped_input
                }
            ],
            \"stream\": false,
            \"temperature\": 0.7
        }" \
        | jq -r '.choices[0].message.content' 2>/dev/null)
    
    if [[ -z "$response" ]] || [[ "$response" == "null" ]]; then
        echo "❌ Error: No response from gateway"
    else
        echo "$response"
    fi
    
    echo ""
done

