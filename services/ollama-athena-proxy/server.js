#!/usr/bin/env node
/**
 * Ollama-Athena Proxy
 * Intercepts Ollama requests and routes browser queries to Athena Router
 * Port: 11435 (proxy for Ollama on 11434)
 */

const express = require('express');
const fetch = require('node-fetch');

const app = express();
app.use(express.json({ limit: '50mb' }));

const OLLAMA_URL = process.env.OLLAMA_URL || 'http://127.0.0.1:11434';
const ROUTER_URL = process.env.ROUTER_URL || 'http://127.0.0.1:9113';
const PORT = process.env.PORT || 11435;

// Browser detection keywords
const BROWSER_KEYWORDS = [
  'search for', 'look up', 'find information', 'research', 
  'browse', 'search', 'look for', 'open a browser',
  'web search', 'google', 'find on the internet', 'search the web'
];

// Vision detection keywords
const VISION_KEYWORDS = [
  'describe this image', 'what do you see', 'analyze this image',
  'look at this', 'what\'s in this picture', 'image analysis'
];

// Voice/TTS detection keywords  
const VOICE_KEYWORDS = [
  'read this aloud', 'text to speech', 'say this', 'speak',
  'voice output', 'audio output'
];

function isBrowserRequest(prompt) {
  const lower = prompt.toLowerCase();
  return BROWSER_KEYWORDS.some(kw => lower.includes(kw));
}

function isVisionRequest(prompt) {
  const lower = prompt.toLowerCase();
  return VISION_KEYWORDS.some(kw => lower.includes(kw));
}

function isVoiceRequest(prompt) {
  const lower = prompt.toLowerCase();
  return VOICE_KEYWORDS.some(kw => lower.includes(kw));
}

function shouldUseMLX(prompt) {
  // Use MLX for coding tasks (it's optimized for Apple Silicon)
  const lower = prompt.toLowerCase();
  const codingKeywords = ['code', 'function', 'debug', 'programming', 'python', 'javascript'];
  return codingKeywords.some(kw => lower.includes(kw));
}

// Proxy all GET requests to Ollama
app.get('*', async (req, res) => {
  try {
    const response = await fetch(`${OLLAMA_URL}${req.path}`);
    const data = await response.json();
    res.json(data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Intercept generate/chat requests
app.post('/api/generate', async (req, res) => {
  const { prompt } = req.body;
  
  console.log(`[Proxy] Generate request: "${prompt?.substring(0, 50)}..."`);
  
  // Route to appropriate service based on request type
  if (prompt) {
    // 1. Browser/Search requests → Athena Router (MCP Browser)
    if (isBrowserRequest(prompt)) {
      console.log('[Proxy] 🌐 Browser request → Athena Router (MCP Browser)');
      
      try {
        const response = await fetch(`${ROUTER_URL}/route`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            prompt: prompt,
            use_browser: true,
            modality: 'text',
            max_tokens: 500
          })
        });
        
        const data = await response.json();
        
        res.json({
          model: 'athena-browser',
          created_at: new Date().toISOString(),
          response: data.text || data.reply || 'No results',
          done: true,
          context: [],
          total_duration: data.latency_ms * 1000000,
          load_duration: 0,
          prompt_eval_count: 0,
          eval_count: data.tokens_generated || 0
        });
        
        console.log('[Proxy] ✅ Returned browser results');
        return;
        
      } catch (error) {
        console.error('[Proxy] ❌ Browser routing failed:', error.message);
      }
    }
    
    // 2. Vision requests → Athena Router (FastVLM)
    if (isVisionRequest(prompt)) {
      console.log('[Proxy] 👁️  Vision request → Athena Router (FastVLM)');
      
      try {
        const response = await fetch(`${ROUTER_URL}/route`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            prompt: prompt,
            modality: 'vision',
            max_tokens: 500
          })
        });
        
        const data = await response.json();
        
        res.json({
          model: 'athena-vision',
          created_at: new Date().toISOString(),
          response: data.text || data.reply || 'Vision processing complete',
          done: true
        });
        
        console.log('[Proxy] ✅ Returned vision results');
        return;
        
      } catch (error) {
        console.error('[Proxy] ❌ Vision routing failed:', error.message);
      }
    }
    
    // 3. MLX for coding tasks (Apple Silicon optimized)
    if (shouldUseMLX(prompt)) {
      console.log('[Proxy] 💻 Coding task → Athena Router (MLX)');
      
      try {
        const response = await fetch(`${ROUTER_URL}/route`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            prompt: prompt,
            modality: 'text',
            max_tokens: 2000
          })
        });
        
        const data = await response.json();
        
        res.json({
          model: 'athena-mlx',
          created_at: new Date().toISOString(),
          response: data.text || data.reply || 'MLX processing complete',
          done: true,
          context: [],
          total_duration: data.latency_ms * 1000000
        });
        
        console.log('[Proxy] ✅ Returned MLX results');
        return;
        
      } catch (error) {
        console.error('[Proxy] ❌ MLX routing failed:', error.message);
      }
    }
  }
  
  // 4. Default: Pass through to Ollama
  console.log('[Proxy] 💬 Normal chat → Ollama');
  try {
    const response = await fetch(`${OLLAMA_URL}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body)
    });
    
    // Stream response
    response.body.pipe(res);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Intercept chat completions
app.post('/api/chat', async (req, res) => {
  const messages = req.body.messages || [];
  const lastMessage = messages[messages.length - 1]?.content || '';
  
  console.log(`[Proxy] Chat request: "${lastMessage.substring(0, 50)}..."`);
  
  if (isBrowserRequest(lastMessage)) {
    console.log('[Proxy] 🌐 Browser request detected! Routing to Athena...');
    
    try {
      const response = await fetch(`${ROUTER_URL}/route`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: lastMessage,
          use_browser: true,
          max_tokens: 500
        })
      });
      
      const data = await response.json();
      
      // Return in Ollama chat format
      res.json({
        model: req.body.model || 'athena-router',
        created_at: new Date().toISOString(),
        message: {
          role: 'assistant',
          content: data.text || data.reply || 'No results'
        },
        done: true
      });
      
      console.log('[Proxy] ✅ Returned browser results');
      return;
      
    } catch (error) {
      console.error('[Proxy] ❌ Router failed:', error.message);
    }
  }
  
  // Pass through to Ollama
  console.log('[Proxy] → Forwarding to Ollama');
  try {
    const response = await fetch(`${OLLAMA_URL}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body)
    });
    
    response.body.pipe(res);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Proxy all other POST requests
app.post('*', async (req, res) => {
  try {
    const response = await fetch(`${OLLAMA_URL}${req.path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body)
    });
    
    const contentType = response.headers.get('content-type');
    if (contentType?.includes('application/json')) {
      const data = await response.json();
      res.json(data);
    } else {
      response.body.pipe(res);
    }
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(PORT, () => {
  console.log('=========================================');
  console.log('🚀 Ollama-Athena Proxy Started');
  console.log('=========================================');
  console.log(`Proxy:  http://localhost:${PORT}`);
  console.log(`Ollama: ${OLLAMA_URL}`);
  console.log(`Router: ${ROUTER_URL}`);
  console.log('');
  console.log('✅ Browser requests will be routed to Athena');
  console.log('✅ Normal chat will use Ollama');
  console.log('');
  console.log('Configure Open WebUI to use:');
  console.log(`  http://host.docker.internal:${PORT}`);
  console.log('=========================================');
});

