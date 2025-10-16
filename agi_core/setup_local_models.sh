#!/bin/bash
# Setup Local Models for STOP Optimizer
# Quick setup script for Ollama and recommended models

set -e

echo "================================"
echo "STOP Optimizer - Local Model Setup"
echo "================================"
echo ""

# Check if Ollama is installed
if command -v ollama &> /dev/null; then
    echo "✅ Ollama is already installed"
else
    echo "📥 Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
    echo "✅ Ollama installed successfully"
fi

echo ""

# Check if Ollama is running
if curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo "✅ Ollama server is running"
else
    echo "🚀 Starting Ollama server..."
    ollama serve &
    sleep 3
    echo "✅ Ollama server started"
fi

echo ""
echo "📦 Installing recommended models..."
echo ""

# CodeLlama 7B - Best for general code optimization
if ollama list | grep -q "codellama:7b"; then
    echo "✅ codellama:7b already installed"
else
    echo "📥 Pulling codellama:7b (4GB, ~2-5 min)..."
    ollama pull codellama:7b
    echo "✅ codellama:7b installed"
fi

echo ""

# Optional: DeepSeek Coder
read -p "Install DeepSeek Coder 6.7B? (excellent for algorithms) [y/N]: " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if ollama list | grep -q "deepseek-coder:6.7b"; then
        echo "✅ deepseek-coder:6.7b already installed"
    else
        echo "📥 Pulling deepseek-coder:6.7b (4GB)..."
        ollama pull deepseek-coder:6.7b
        echo "✅ deepseek-coder:6.7b installed"
    fi
fi

echo ""
echo "================================"
echo "✅ Setup Complete!"
echo "================================"
echo ""
echo "Installed models:"
ollama list
echo ""
echo "Next steps:"
echo "  1. Run examples: python3 agi_core/examples_stop.py"
echo "  2. Check guide: cat agi_core/LOCAL_MODELS_GUIDE.md"
echo "  3. Start optimizing your code!"
echo ""
echo "Usage example:"
echo "  from agi_core.stop_optimizer import LLMInterface"
echo "  llm = LLMInterface(model='codellama:7b', use_local=True)"
echo ""

