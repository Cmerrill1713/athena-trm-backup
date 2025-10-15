#!/usr/bin/env bash
# Athena Voice Control - Natural Language to System Commands
# Usage: ./athena_voice.sh "bring everything online"
#    Or: ./athena_voice.sh  (interactive mode)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(dirname "$SCRIPT_DIR")"
INTENT_MAP="$SCRIPT_DIR/athena_voice_map.json"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Parse intent from natural language
parse_intent() {
    local input="$1"
    local input_lower=$(echo "$input" | tr '[:upper:]' '[:lower:]')
    
    # Use Python for JSON parsing
    python3 << EOF
import json
import sys

with open('$INTENT_MAP') as f:
    data = json.load(f)

input_text = '''$input_lower'''

# Match against phrases
matched_intent = None
for intent, config in data['intents'].items():
    for phrase in config['phrases']:
        if phrase.lower() in input_text:
            matched_intent = intent
            print(json.dumps({
                'intent': intent,
                'command': config['command'],
                'response': config['response'],
                'requires_confirmation': config.get('requires_confirmation', False)
            }))
            sys.exit(0)

# No match
sys.exit(1)
EOF
}

# Execute command with confirmation if needed
execute_command() {
    local intent_json="$1"
    
    local command=$(echo "$intent_json" | python3 -c "import sys, json; print(json.load(sys.stdin)['command'])")
    local response=$(echo "$intent_json" | python3 -c "import sys, json; print(json.load(sys.stdin)['response'])")
    local needs_confirm=$(echo "$intent_json" | python3 -c "import sys, json; print(json.load(sys.stdin)['requires_confirmation'])")
    
    echo -e "${CYAN}🧠 Athena:${NC} $response"
    echo ""
    
    # Check if confirmation needed
    if [ "$needs_confirm" = "True" ]; then
        echo -e "${YELLOW}⚠️  This action requires confirmation.${NC}"
        echo -e "Command: ${CYAN}$command${NC}"
        read -p "Proceed? (yes/no): " confirm
        echo ""
        
        if [ "$confirm" != "yes" ] && [ "$confirm" != "y" ]; then
            echo -e "${YELLOW}Action cancelled.${NC}"
            return 0
        fi
    fi
    
    # Execute
    echo -e "${GREEN}Executing:${NC} $command"
    echo ""
    
    cd "$WORKSPACE_ROOT"
    eval "$command"
    
    echo ""
    echo -e "${GREEN}✅ Done.${NC}"
}

# Show help
show_help() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║          🧠 ATHENA VOICE CONTROL - HELP                    ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Available commands:"
    echo ""
    
    python3 << EOF
import json

with open('$INTENT_MAP') as f:
    data = json.load(f)

for category, phrases in data['help']['categories'].items():
    print(f"  {category}:")
    for phrase in phrases:
        print(f"    • \"{phrase}\"")
    print("")
EOF
    
    echo "Examples:"
    echo "  ./athena_voice.sh \"bring everything online\""
    echo "  ./athena_voice.sh \"run smoke tests\""
    echo "  ./athena_voice.sh \"ship it\""
    echo ""
    echo "Interactive mode:"
    echo "  ./athena_voice.sh"
    echo ""
}

# Interactive mode
interactive_mode() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║          🧠 ATHENA VOICE CONTROL                           ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "I'm ready. What would you like me to do?"
    echo "(Type 'help' for commands, 'exit' to quit)"
    echo ""
    
    while true; do
        echo -n -e "${CYAN}You:${NC} "
        read -r input
        
        case "$input" in
            "exit"|"quit"|"bye")
                echo -e "${CYAN}🧠 Athena:${NC} Goodbye."
                exit 0
                ;;
            "help"|"?")
                show_help
                ;;
            "")
                continue
                ;;
            *)
                if intent_json=$(parse_intent "$input" 2>/dev/null); then
                    execute_command "$intent_json"
                else
                    echo -e "${YELLOW}🧠 Athena:${NC} I didn't understand that command."
                    echo "   Try 'help' for available commands."
                fi
                echo ""
                ;;
        esac
    done
}

# Main execution
if [ $# -eq 0 ]; then
    # No arguments = interactive mode
    interactive_mode
else
    # Single command mode
    input="$*"
    
    if [ "$input" = "help" ] || [ "$input" = "--help" ] || [ "$input" = "-h" ]; then
        show_help
        exit 0
    fi
    
    if intent_json=$(parse_intent "$input" 2>/dev/null); then
        execute_command "$intent_json"
    else
        echo -e "${YELLOW}🧠 Athena:${NC} I didn't understand that command."
        echo "   Try './athena_voice.sh help' for available commands."
        exit 1
    fi
fi

