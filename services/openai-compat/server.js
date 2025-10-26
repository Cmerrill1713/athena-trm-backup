#!/usr/bin/env node
/**
 * OpenAI-Compatible Adapter for Athena RAG
 * 
 * Wraps your existing RAG backend (/query and /chat) to be OpenAI-compatible
 * so off-the-shelf UIs (Open WebUI, ChatBot UI, LibreChat) work out of the box.
 * 
 * Usage:
 *   npm install
 *   RAG_API_BASE_URL=http://127.0.0.1:8090 node server.js
 * 
 * Port: 3000 by default (env: PORT)
 */

import cors from "cors";
import express from "express";
import fetch from "node-fetch";
import * as metrics from "./metrics.js";

const app = express();
app.use(express.json());
app.use(cors());

// Configuration
const RAG_API = process.env.RAG_API_BASE_URL || "http://127.0.0.1:8090";
const CHAT_API = process.env.CHAT_API_BASE_URL || "http://127.0.0.1:8089";
const ROUTER_API = process.env.ROUTER_API_BASE_URL || "http://127.0.0.1:9113";
const TOKEN = process.env.RAG_API_TOKEN || "";
const PORT = process.env.PORT || 3000;
const TIMEOUT_MS = parseInt(process.env.TIMEOUT_MS || "30000");
const DEFAULT_MODE = process.env.DEFAULT_MODE || "nearText";
const DEFAULT_TOP_K = parseInt(process.env.DEFAULT_TOP_K || "5");
const ENABLE_STREAMING = process.env.ENABLE_STREAMING !== "false";

// Logging
const log = (msg) => console.log(`[OpenAI-Compat] ${new Date().toISOString()} - ${msg}`);

// Helper: Detect browser/search requests
function isBrowserRequest(message) {
  const browserKeywords = [
    "open a browser", "browser", "search for", "look up", "find information",
    "research papers", "search the web", "look online", "find on the internet"
  ];
  const msgLower = message.toLowerCase();
  return browserKeywords.some(keyword => msgLower.includes(keyword));
}

// ============================================================================
// Health & Info
// ============================================================================

app.get("/", (req, res) => {
  res.json({
    service: "openai-compat-adapter",
    version: "1.0.0",
    rag_api: RAG_API,
    chat_api: CHAT_API,
    endpoints: {
      chat: "/v1/chat/completions",
      models: "/v1/models",
      health: "/health",
    },
  });
});

app.get("/health", (req, res) => {
  res.json({ status: "healthy", service: "openai-compat" });
});

app.get("/healthz", (req, res) => {
  res.json({ 
    status: "ok",
    service: "openai-compat",
    backends: {
      rag: RAG_API,
      chat: CHAT_API
    },
    config: {
      streaming: ENABLE_STREAMING,
      default_mode: DEFAULT_MODE,
      default_top_k: DEFAULT_TOP_K,
      timeout_ms: TIMEOUT_MS
    }
  });
});

// Prometheus metrics endpoint
app.get("/metrics", async (req, res) => {
  res.setHeader("Content-Type", metrics.register.contentType);
  res.send(await metrics.register.metrics());
});

// ============================================================================
// OpenAI-Compatible Endpoints
// ============================================================================

// List models (OpenAI format)
app.get("/v1/models", (req, res) => {
  res.json({
    object: "list",
    data: [
      {
        id: "athena-rag",
        object: "model",
        created: Math.floor(Date.now() / 1000),
        owned_by: "athena",
      },
      {
        id: "athena-chat",
        object: "model",
        created: Math.floor(Date.now() / 1000),
        owned_by: "athena",
      },
      {
        id: "athena-hybrid",
        object: "model",
        created: Math.floor(Date.now() / 1000),
        owned_by: "athena",
      },
    ],
  });
});

// Chat completions (OpenAI format → Athena backend)
app.post("/v1/chat/completions", async (req, res) => {
  const startTime = Date.now();
  const route = "/v1/chat/completions";
  
  metrics.startActiveRequest(route);
  
  try {
    const {
      messages = [],
      model = "athena-rag",
      stream = false,
      temperature,
      max_tokens,
      top_k = DEFAULT_TOP_K,
      mode = DEFAULT_MODE, // bm25, nearText, hybrid
    } = req.body;

    // Validate request (contract check)
    if (!messages || !Array.isArray(messages) || messages.length === 0) {
      metrics.endActiveRequest(route);
      return res.status(400).json({ error: { message: "messages array required" } });
    }

    // Extract user message
    const userMessages = messages.filter((m) => m.role === "user");
    const userMsg = userMessages.map((m) => m.content).join("\n");

    if (!userMsg) {
      metrics.endActiveRequest(route);
      return res.status(400).json({ error: { message: "No user message provided" } });
    }

    // Validate model
    const validModels = ["athena-rag", "athena-chat", "athena-hybrid"];
    if (!validModels.includes(model)) {
      metrics.endActiveRequest(route);
      return res.status(400).json({ error: { message: `Invalid model. Must be one of: ${validModels.join(", ")}` } });
    }

    log(`Chat request: model=${model}, query="${userMsg.substring(0, 50)}..."`);

    // Track model usage
    metrics.trackModelUsage(model);

    // Check if this is a browser request
    const useBrowser = isBrowserRequest(userMsg);

    // Route to appropriate backend based on model name
    let reply;
    let backendUsed;

    if (useBrowser) {
      // Use router for browser requests
      log(`🌐 Browser request detected, routing to Athena router`);
      reply = await callRouter(userMsg, true);
      backendUsed = "athena-router (browser)";
    } else if (model.includes("chat")) {
      // Use smart_chat service (port 8088)
      reply = await callSmartChat(userMsg);
      backendUsed = "smart_chat";
    } else if (model.includes("rag") || model.includes("hybrid")) {
      // Use RAG gateway (port 8090)
      const ragMode = model.includes("hybrid") ? "hybrid" : mode;
      metrics.trackRAGMode(ragMode);
      reply = await callRAG(userMsg, ragMode, top_k);
      backendUsed = `rag_gateway (${ragMode})`;
    } else {
      // Default to smart chat
      reply = await callSmartChat(userMsg);
      backendUsed = "smart_chat (default)";
    }

    // Check for empty responses
    if (!reply || reply.trim().length < 10) {
      metrics.trackEmptyResponse(model);
    }

    // Handle streaming (if requested and enabled)
    if (stream && ENABLE_STREAMING) {
      res.setHeader("Content-Type", "text/event-stream");
      res.setHeader("Cache-Control", "no-cache");
      res.setHeader("Connection", "keep-alive");

      // Send chunks in OpenAI SSE format
      const chunks = reply.split(" ");
      for (const chunk of chunks) {
        const data = {
          id: "chatcmpl-" + Date.now(),
          object: "chat.completion.chunk",
          created: Math.floor(Date.now() / 1000),
          model: model,
          choices: [
            {
              index: 0,
              delta: { content: chunk + " " },
              finish_reason: null,
            },
          ],
        };
        res.write(`data: ${JSON.stringify(data)}\n\n`);
        await sleep(50); // Simulate streaming delay
      }

      // Final chunk
      res.write(
        `data: ${JSON.stringify({
          id: "chatcmpl-" + Date.now(),
          object: "chat.completion.chunk",
          created: Math.floor(Date.now() / 1000),
          model: model,
          choices: [{ index: 0, delta: {}, finish_reason: "stop" }],
        })}\n\n`
      );
      res.write("data: [DONE]\n\n");
      res.end();
      metrics.trackStream("ended");
    } else {
      // Non-streaming response
      res.json({
        id: "chatcmpl-" + Date.now(),
        object: "chat.completion",
        created: Math.floor(Date.now() / 1000),
        model: model,
        choices: [
          {
            index: 0,
            message: {
              role: "assistant",
              content: reply,
            },
            finish_reason: "stop",
          },
        ],
        usage: {
          prompt_tokens: userMsg.split(" ").length,
          completion_tokens: reply.split(" ").length,
          total_tokens: userMsg.split(" ").length + reply.split(" ").length,
        },
        backend: backendUsed, // Extra metadata
      });
    }

    log(`✅ Success: ${reply.substring(0, 50)}... (backend: ${backendUsed})`);
    
    // Track metrics
    const duration = (Date.now() - startTime) / 1000;
    metrics.trackRequest(route, "POST", 200, duration);
    metrics.endActiveRequest(route);
  } catch (e) {
    log(`❌ Error: ${e.message}`);
    
    // Track error
    const duration = (Date.now() - startTime) / 1000;
    metrics.trackRequest(route, "POST", 500, duration);
    metrics.endActiveRequest(route);
    
    // Track upstream error if applicable
    if (e.message.includes("RAG API") || e.message.includes("Smart Chat")) {
      const backend = e.message.includes("RAG") ? "rag" : "chat";
      const reason = e.message.includes("timeout") ? "timeout" : 
                     e.message.includes("5") ? "5xx" : "connection";
      metrics.trackUpstreamError(backend, reason);
    }
    
    // Track stream error if applicable
    if (req.body.stream) {
      metrics.trackStream("errored");
    }
    
    res.status(500).json({ error: { message: e.message, type: "server_error" } });
  }
});

// ============================================================================
// Backend Callers
// ============================================================================

/**
 * Call Athena router (port 9113) for browser and advanced requests
 */
async function callRouter(message, useBrowser = false) {
  const backendStart = Date.now();
  
  try {
    const r = await fetch(`${ROUTER_API}/route`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        prompt: message,
        modality: "text",
        use_browser: useBrowser,
        max_tokens: 500
      }),
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });

    const backendDuration = (Date.now() - backendStart) / 1000;
    metrics.trackBackendLatency("router", backendDuration);

    if (!r.ok) {
      throw new Error(`Router API error: ${r.status} ${await r.text()}`);
    }

    const data = await r.json();
    return data.text || data.reply || "No response from router";
  } catch (e) {
    const backendDuration = (Date.now() - backendStart) / 1000;
    metrics.trackBackendLatency("router", backendDuration);
    throw e;
  }
}

/**
 * Call smart_chat service (port 8088)
 */
async function callSmartChat(message) {
  const backendStart = Date.now();
  
  try {
    const r = await fetch(`${CHAT_API}/v1/chat/completions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(TOKEN ? { Authorization: `Bearer ${TOKEN}` } : {}),
      },
      body: JSON.stringify({
        messages: [{ role: "user", content: message }],
        max_tokens: 100
      }),
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });

    const backendDuration = (Date.now() - backendStart) / 1000;
    metrics.trackBackendLatency("chat", backendDuration);

    if (!r.ok) {
      throw new Error(`Smart Chat API error: ${r.status} ${await r.text()}`);
    }

    const data = await r.json();
    return data.reply;
  } catch (e) {
    const backendDuration = (Date.now() - backendStart) / 1000;
    metrics.trackBackendLatency("chat", backendDuration);
    throw e;
  }
}

/**
 * Call RAG gateway (port 8090) and format results as conversational response
 */
async function callRAG(query, mode = "nearText", topK = 5) {
  const backendStart = Date.now();
  
  try {
    const r = await fetch(`${RAG_API}/query`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(TOKEN ? { Authorization: `Bearer ${TOKEN}` } : {}),
      },
      body: JSON.stringify({
        query,
        top_k: topK,
        min_score: 0.55,
        mode: mode,
      }),
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });

    const backendDuration = (Date.now() - backendStart) / 1000;
    metrics.trackBackendLatency("rag", backendDuration);

    if (!r.ok) {
      throw new Error(`RAG API error: ${r.status} ${await r.text()}`);
    }

    const data = await r.json();

    // Format RAG results as conversational response
    if (!data.hits || data.hits.length === 0) {
      return `I couldn't find relevant information for "${query}". Could you rephrase your question?`;
    }

    // Build response from top hits
    const topHits = data.hits.slice(0, 3); // Use top 3 hits
    let response = `Based on the knowledge base, here's what I found:\n\n`;

    topHits.forEach((hit, i) => {
      response += `${i + 1}. ${hit.content || hit.text || "No content"}\n`;
      if (hit.score) {
        response += `   (Relevance: ${(hit.score * 100).toFixed(1)}%)\n`;
      }
      response += `\n`;
    });

    response += `\nWould you like me to elaborate on any of these points?`;

    return response;
  } catch (e) {
    const backendDuration = (Date.now() - backendStart) / 1000;
    metrics.trackBackendLatency("rag", backendDuration);
    throw e;
  }
}

/**
 * Sleep helper for streaming
 */
function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// ============================================================================
// Error Handler
// ============================================================================

app.use((err, req, res, next) => {
  log(`Unhandled error: ${err.message}`);
  res.status(500).json({
    error: {
      message: err.message,
      type: "internal_server_error",
    },
  });
});

// ============================================================================
// Start Server
// ============================================================================

app.listen(PORT, () => {
  log(`🚀 OpenAI-Compatible Adapter running on http://localhost:${PORT}`);
  log(`📡 RAG API: ${RAG_API}`);
  log(`💬 Chat API: ${CHAT_API}`);
  log(`🔌 Endpoints:`);
  log(`   - POST /v1/chat/completions (OpenAI-compatible)`);
  log(`   - GET  /v1/models`);
  log(`   - GET  /health`);
  log(``);
  log(`📖 Usage: Point your UI to http://localhost:${PORT}/v1 as OpenAI endpoint`);
});

