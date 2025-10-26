# 🎯 Custom Athena Open WebUI Configuration

## ✅ **Your Current Setup:**

- **Open WebUI**: Running on http://localhost:3000 (Docker container)
- **Ollama**: Running on http://localhost:11434
- **Athena Router**: Available on http://localhost:9113

## 🔧 **Customization Options:**

### **1. Custom Themes & Branding**

You can customize Open WebUI by:

```bash
# Access the running container
docker exec -it open-webui bash

# Navigate to customization directory
cd /app/backend/app/webui

# Customize the interface
```

### **2. Custom System Prompts**

Create Athena-specific system prompts:

```json
{
  "athena_assistant": "You are Athena, an advanced AI assistant with access to web search, coding capabilities, and vision analysis. You can help with research, programming, and general questions.",
  "athena_coding": "You are Athena Code, specialized in programming tasks. Provide clean, efficient code with explanations.",
  "athena_research": "You are Athena Research, specialized in finding and analyzing information from web sources and research papers."
}
```

### **3. Custom Model Configurations**

Set up your models with Athena-specific settings:

```yaml
models:
  qwen2.5:7b:
    system_prompt: "athena_assistant"
    temperature: 0.7
    max_tokens: 2000
  qwen3-coder:30b:
    system_prompt: "athena_coding"
    temperature: 0.3
    max_tokens: 4000
  llava:7b:
    system_prompt: "athena_vision"
    temperature: 0.5
    max_tokens: 1500
```

### **4. Custom CSS Styling**

Add Athena branding:

```css
/* Athena Custom Styles */
:root {
  --athena-primary: #6366f1;
  --athena-secondary: #8b5cf6;
  --athena-accent: #06b6d4;
}

.athena-brand {
  background: linear-gradient(135deg, var(--athena-primary), var(--athena-secondary));
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
}
```

## 🚀 **Quick Customization Steps:**

### **Step 1: Access Open WebUI**
```bash
# Open in browser
open http://localhost:3000
```

### **Step 2: Configure Ollama Connection**
- Go to Settings → Connections
- Set Ollama Base URL: `http://host.docker.internal:11434`

### **Step 3: Add Athena Models**
- Go to Models tab
- Add your custom models with Athena prompts

### **Step 4: Customize Interface**
- Go to Settings → Interface
- Upload custom logo/branding
- Set custom colors

## 🎨 **Advanced Customization:**

### **Custom Docker Compose**
```yaml
version: '3.8'
services:
  athena-open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: athena-open-webui
    ports:
      - "3000:8080"
    volumes:
      - ./custom-ui:/app/backend/app/webui
      - ./athena-config:/app/backend/app/config
    environment:
      - OLLAMA_BASE_URL=http://host.docker.internal:11434
      - WEBUI_NAME="Athena Desktop"
      - WEBUI_URL="http://localhost:3000"
```

### **Custom Environment Variables**
```bash
# Athena-specific settings
WEBUI_NAME="Athena Desktop"
WEBUI_URL="http://localhost:3000"
OLLAMA_BASE_URL="http://host.docker.internal:11434"
DEFAULT_MODELS="qwen2.5:7b,qwen3-coder:30b,llava:7b"
```

## 🔍 **Current Configuration:**

Your Open WebUI is already running with:
- ✅ Ollama integration
- ✅ Model management
- ✅ Chat interface
- ✅ File upload support
- ✅ Custom prompts

## 🎯 **Next Steps:**

1. **Access**: http://localhost:3000
2. **Configure**: Set Ollama URL to `http://host.docker.internal:11434`
3. **Customize**: Add Athena branding and prompts
4. **Test**: Try different models and capabilities

## 📝 **Customization Files:**

I can help you create:
- Custom CSS for Athena branding
- Custom system prompts
- Custom model configurations
- Custom Docker setup

**What would you like to customize first?**
