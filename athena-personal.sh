#!/bin/bash

# Athena Personal Ollama Setup
# Quick access to different AI capabilities

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
OLLAMA_HOST="127.0.0.1:11434"
ATHENA_ROUTER="127.0.0.1:9113"

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     🎯 ATHENA PERSONAL OLLAMA SETUP        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# Function to check if service is running
check_service() {
    local service=$1
    local port=$2
    if curl -sf "http://${port}" > /dev/null 2>&1; then
        echo -e "✅ ${service} is running on port ${port}"
        return 0
    else
        echo -e "❌ ${service} is not running on port ${port}"
        return 1
    fi
}

# Function to start Ollama if needed
start_ollama() {
    if ! check_service "Ollama" "${OLLAMA_HOST}"; then
        echo -e "${YELLOW}Starting Ollama service...${NC}"
        ollama serve &
        sleep 3
        if check_service "Ollama" "${OLLAMA_HOST}"; then
            echo -e "${GREEN}✅ Ollama started successfully${NC}"
        else
            echo -e "${RED}❌ Failed to start Ollama${NC}"
            exit 1
        fi
    fi
}

# Function to pull a model if not available
ensure_model() {
    local model=$1
    if ! ollama list | grep -q "${model}"; then
        echo -e "${YELLOW}Pulling model: ${model}${NC}"
        ollama pull "${model}"
    else
        echo -e "✅ Model ${model} is available"
    fi
}

# Function to chat with a specific model
chat_with_model() {
    local model=$1
    local prompt=$2
    echo -e "${BLUE}Chatting with ${model}...${NC}"
    echo -e "${YELLOW}Prompt: ${prompt}${NC}"
    echo ""
    
    ollama run "${model}" "${prompt}"
}

# Function to use Athena Router for advanced capabilities
use_athena_router() {
    local prompt=$1
    local modality=${2:-"text"}
    
    echo -e "${BLUE}Using Athena Router for: ${modality}${NC}"
    echo -e "${YELLOW}Prompt: ${prompt}${NC}"
    echo ""
    
    curl -s -X POST "http://${ATHENA_ROUTER}/route" \
        -H "Content-Type: application/json" \
        -d "{
            \"prompt\": \"${prompt}\",
            \"modality\": \"${modality}\",
            \"max_tokens\": 1000
        }" | jq -r '.text // .reply // "No response"'
}

# Main menu
show_menu() {
    echo -e "${GREEN}Available Commands:${NC}"
    echo ""
    echo "1. chat [model] [prompt]     - Chat with specific model"
    echo "2. search [query]           - Web search via Athena Router"
    echo "3. code [prompt]            - Coding assistance via Athena Router"
    echo "4. vision [prompt]          - Vision analysis via Athena Router"
    echo "5. voice [text]              - Text-to-speech via Athena Router"
    echo "6. models                    - List available models"
    echo "7. pull [model]              - Pull/download a model"
    echo "8. status                    - Check service status"
    echo "9. config                    - Show configuration"
    echo "0. exit                      - Exit"
    echo ""
}

# Parse command line arguments
case "${1:-menu}" in
    "chat")
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo -e "${RED}Usage: $0 chat [model] [prompt]${NC}"
            echo -e "${YELLOW}Example: $0 chat qwen2.5:7b 'What is machine learning?'${NC}"
            exit 1
        fi
        start_ollama
        ensure_model "$2"
        chat_with_model "$2" "$3"
        ;;
    
    "search")
        if [ -z "$2" ]; then
            echo -e "${RED}Usage: $0 search [query]${NC}"
            echo -e "${YELLOW}Example: $0 search 'latest AI research papers'${NC}"
            exit 1
        fi
        if check_service "Athena Router" "9113"; then
            use_athena_router "search for $2" "text"
        else
            echo -e "${RED}❌ Athena Router not available. Using basic Ollama instead.${NC}"
            start_ollama
            chat_with_model "qwen2.5:7b" "Search for: $2"
        fi
        ;;
    
    "code")
        if [ -z "$2" ]; then
            echo -e "${RED}Usage: $0 code [prompt]${NC}"
            echo -e "${YELLOW}Example: $0 code 'write a python function to sort a list'${NC}"
            exit 1
        fi
        if check_service "Athena Router" "9113"; then
            use_athena_router "$2" "text"
        else
            echo -e "${RED}❌ Athena Router not available. Using coding model instead.${NC}"
            start_ollama
            ensure_model "qwen3-coder:30b"
            chat_with_model "qwen3-coder:30b" "$2"
        fi
        ;;
    
    "vision")
        if [ -z "$2" ]; then
            echo -e "${RED}Usage: $0 vision [prompt]${NC}"
            echo -e "${YELLOW}Example: $0 vision 'describe this image'${NC}"
            exit 1
        fi
        if check_service "Athena Router" "9113"; then
            use_athena_router "$2" "vision"
        else
            echo -e "${RED}❌ Athena Router not available. Using vision model instead.${NC}"
            start_ollama
            ensure_model "llava:7b"
            chat_with_model "llava:7b" "$2"
        fi
        ;;
    
    "voice")
        if [ -z "$2" ]; then
            echo -e "${RED}Usage: $0 voice [text]${NC}"
            echo -e "${YELLOW}Example: $0 voice 'Hello world'${NC}"
            exit 1
        fi
        if check_service "Athena Router" "9113"; then
            use_athena_router "read this aloud: $2" "voice"
        else
            echo -e "${RED}❌ Athena Router not available for voice.${NC}"
            exit 1
        fi
        ;;
    
    "models")
        start_ollama
        echo -e "${GREEN}Available Models:${NC}"
        ollama list
        ;;
    
    "pull")
        if [ -z "$2" ]; then
            echo -e "${RED}Usage: $0 pull [model]${NC}"
            echo -e "${YELLOW}Example: $0 pull llama3.2:3b${NC}"
            exit 1
        fi
        start_ollama
        ollama pull "$2"
        ;;
    
    "status")
        echo -e "${GREEN}Service Status:${NC}"
        check_service "Ollama" "${OLLAMA_HOST}"
        check_service "Athena Router" "9113"
        echo ""
        echo -e "${GREEN}Available Models:${NC}"
        ollama list 2>/dev/null || echo "Ollama not running"
        ;;
    
    "config")
        echo -e "${GREEN}Configuration:${NC}"
        echo "Ollama Host: ${OLLAMA_HOST}"
        echo "Athena Router: ${ATHENA_ROUTER}"
        echo ""
        if [ -f ~/.ollama/config.json ]; then
            echo -e "${GREEN}Personal Config:${NC}"
            cat ~/.ollama/config.json | jq .
        else
            echo "No personal config found"
        fi
        ;;
    
    "menu"|"")
        show_menu
        ;;
    
    "exit"|"0")
        echo "Goodbye!"
        exit 0
        ;;
    
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        show_menu
        ;;
esac
