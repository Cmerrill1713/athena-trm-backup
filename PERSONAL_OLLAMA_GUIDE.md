# 🎯 Athena Personal Ollama Setup

## ✅ **What You Have Now:**

- **Ollama installed and running** with 12+ models
- **Personal configuration** in `~/.ollama/config.json`
- **Smart script** (`athena-personal.sh`) for easy access
- **Convenient alias** (`athena`) added to your shell

## 🚀 **How to Use:**

### **Basic Commands:**

```bash
# Chat with any model
athena chat qwen2.5:7b "What is machine learning?"

# Coding assistance (uses qwen3-coder:30b)
athena code "write a python function to sort a list"

# List available models
athena models

# Check status
athena status

# Pull new models
athena pull llama3.2:3b
```

### **Your Available Models:**

| Model             | Size  | Best For                     |
| ----------------- | ----- | ---------------------------- |
| `qwen2.5:7b`      | 4.7GB | General chat, reasoning      |
| `qwen3-coder:30b` | 18GB  | Programming, code generation |
| `qwen2.5:14b`     | 9.0GB | Advanced reasoning           |
| `llava:7b`        | 4.7GB | Vision, image analysis       |
| `granite4:tiny-h` | 4.2GB | Fast responses               |
| `mistral:7b`      | 4.4GB | Alternative general model    |

## 🎯 **Quick Examples:**

### **General Chat:**

```bash
athena chat qwen2.5:7b "Explain quantum computing in simple terms"
```

### **Coding Help:**

```bash
athena code "create a REST API endpoint in Python using FastAPI"
```

### **Vision Analysis:**

```bash
athena chat llava:7b "describe this image"  # (with image file)
```

### **Fast Responses:**

```bash
athena chat granite4:tiny-h "What's 2+2?"
```

## 🔧 **Configuration:**

Your personal config is in `~/.ollama/config.json`:

```json
{
  "host": "127.0.0.1:11434",
  "models": {
    "default": "qwen2.5:7b",
    "coding": "qwen3-coder:30b",
    "vision": "llava:7b",
    "embedding": "qwen3-embedding:4b"
  },
  "system_prompts": {
    "assistant": "You are Athena, an advanced AI assistant...",
    "coding": "You are Athena Code, specialized in programming...",
    "research": "You are Athena Research, specialized in finding..."
  }
}
```

## 🎨 **Customization:**

### **Add Custom Models:**

```bash
athena pull codellama:7b
athena pull llama3.1:8b
```

### **Create Custom Commands:**

Add to `athena-personal.sh`:

```bash
"research")
    chat_with_model "qwen2.5:14b" "$2"
    ;;
```

### **Set Default Model:**

Edit `~/.ollama/config.json`:

```json
{
  "models": {
    "default": "qwen2.5:14b" // Change this
  }
}
```

## 🚀 **Advanced Usage:**

### **Batch Processing:**

```bash
# Process multiple prompts
for prompt in "explain AI" "write hello world" "what is Python"; do
    athena chat qwen2.5:7b "$prompt"
done
```

### **Model Comparison:**

```bash
# Compare responses from different models
athena chat qwen2.5:7b "What is machine learning?"
athena chat mistral:7b "What is machine learning?"
```

### **Interactive Mode:**

```bash
# Start interactive chat
ollama run qwen2.5:7b
```

## 🔍 **Troubleshooting:**

### **Ollama Not Running:**

```bash
# Start Ollama service
ollama serve &

# Or restart
pkill ollama && ollama serve &
```

### **Model Not Found:**

```bash
# Pull the model
athena pull [model-name]

# List available models
athena models
```

### **Slow Responses:**

- Use smaller models: `granite4:tiny-h`, `qwen2.5:0.5b`
- Close other applications
- Check available RAM

### **Memory Issues:**

- Use smaller models
- Close unused models: `ollama stop [model-name]`

## 📊 **Performance Tips:**

1. **For Speed:** Use `granite4:tiny-h` or `qwen2.5:0.5b`
2. **For Quality:** Use `qwen2.5:14b` or `qwen3-coder:30b`
3. **For Coding:** Always use `qwen3-coder:30b`
4. **For Vision:** Use `llava:7b`

## 🎯 **What's Different from Before:**

- ✅ **No Docker complexity** - Direct Ollama access
- ✅ **No proxy layers** - Simple and fast
- ✅ **Personal configuration** - Customized for you
- ✅ **Easy model switching** - One command
- ✅ **Local-first** - Everything runs locally
- ✅ **Simple interface** - Command line, no UI complexity

## 🎉 **You're All Set!**

Try it now:

```bash
athena chat qwen2.5:7b "Hello! I'm your personal AI assistant."
```

**This is much cleaner, faster, and more personal than the Docker setup!**
