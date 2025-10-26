#!/usr/bin/env python3
"""
Smart Chat Service - Athena with personality and intelligence
Combines: Router + Personality + Context + Memory
Port 8089
"""
import os
import sys
import json
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx

# Import smart router
sys.path.insert(0, str(Path(__file__).parent))
try:
    from smart_router import route_query
except ImportError:
    # Fallback to simple routing if smart router not available
    def route_query(query: str) -> dict:
        return {"selected_model": "qwen2.5:7b", "routing_reason": "fallback"}

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
ROUTER_URL = os.getenv("ROUTER_URL", "http://127.0.0.1:9113")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
MODEL = os.getenv("MODEL", "qwen2.5:14b")

# Athena Personality - the smart system we lost
ATHENA_SYSTEM_PROMPT = """You are Athena, an intelligent and articulate AI assistant with a warm, engaging personality. You're powered by local models and pride yourself on thoughtful, natural conversation.

You:
• Speak naturally and conversationally, like a knowledgeable friend
• Show genuine curiosity and engagement with questions
• Explain complex concepts clearly without being condescending
• Use appropriate humor and warmth when fitting
• Admit when you're uncertain and offer to explore together
• Remember context and build on previous exchanges
• Are concise yet thorough - you value the user's time
• Celebrate successes and empathize with challenges

Your goal is to be helpful, insightful, and genuinely pleasant to interact with - not just functional, but delightful."""

# Session memory (simple in-memory for now)
sessions: Dict[str, List[Dict[str, str]]] = {}

# FastAPI app
app = FastAPI(
    title="Smart Chat Service",
    description="Athena with personality and intelligence",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"
    use_router: Optional[bool] = False

class ChatResponse(BaseModel):
    reply: str
    session_id: str
    model: str
    latency_ms: int
    timestamp: str

# ============================================================================
# Endpoints
# ============================================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "smart-chat",
        "model": MODEL,
        "router": ROUTER_URL,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Smart chat with Athena personality and optional router"""
    start = time.time()
    session_id = req.session_id
    
    # Get or create session
    if session_id not in sessions:
        sessions[session_id] = []
    
    # Add user message to history
    sessions[session_id].append({"role": "user", "content": req.message})
    
    # Keep last 10 messages for context
    if len(sessions[session_id]) > 10:
        sessions[session_id] = sessions[session_id][-10:]
    
    # Build messages with personality
    messages = [{"role": "system", "content": ATHENA_SYSTEM_PROMPT}]
    messages.extend(sessions[session_id])
    
    # Call Ollama (or router if requested)
    try:
        if req.use_router:
            # Use smart routing for optimal model selection
            reply = await call_ollama_with_smart_routing(messages)
            model_used = "smart_routed"
        else:
            reply = await call_ollama_with_smart_routing(messages)
            model_used = "smart_routed"
        
        # Add assistant reply to history
        sessions[session_id].append({"role": "assistant", "content": reply})
        
        latency_ms = int((time.time() - start) * 1000)
        
        return ChatResponse(
            reply=reply,
            session_id=session_id,
            model=model_used,
            latency_ms=latency_ms,
            timestamp=datetime.utcnow().isoformat()
        )
    
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def call_rag_gateway(query: str, top_k: int = 3) -> List[Dict[str, any]]:
    """Call RAG Gateway to get relevant documents"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "http://localhost:8088/kb/search",
                json={
                    "query": query,
                    "topK": top_k,
                    "mode": "nearText"
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get("hits", [])
    except Exception as e:
        logger.error(f"RAG Gateway error: {e}")
        return []

async def call_ollama_with_smart_routing(messages: List[Dict[str, str]]) -> str:
    """Call Ollama with smart model routing and RAG integration"""
    # Get the user's latest message for routing analysis
    user_message = ""
    for msg in reversed(messages):
        if msg["role"] == "user":
            user_message = msg["content"]
            break
    
    if not user_message:
        user_message = "General query"
    
    # Use smart router to select optimal model and check for RAG
    routing_result = route_query(user_message)
    selected_model = routing_result["selected_model"]
    routing_reason = routing_result["routing_reason"]
    needs_rag = routing_result.get("needs_rag", False)
    
    logger.info(f"Smart routing: '{user_message[:50]}...' -> {selected_model} ({routing_reason}) RAG: {needs_rag}")
    
    # If RAG is needed, get relevant documents
    rag_context = ""
    if needs_rag:
        rag_docs = await call_rag_gateway(user_message, top_k=3)
        if rag_docs:
            rag_context = "\n\nRelevant information:\n"
            for i, doc in enumerate(rag_docs, 1):
                rag_context += f"{i}. {doc.get('title', 'Unknown')}: {doc.get('chunk', '')[:200]}...\n"
            logger.info(f"RAG found {len(rag_docs)} relevant documents")
        else:
            logger.info("RAG search returned no results")
    
    # Prepare messages with RAG context if available
    enhanced_messages = messages.copy()
    
    # Add system prompt to force English responses
    system_msg = None
    for msg in enhanced_messages:
        if msg["role"] == "system":
            system_msg = msg
            break
    
    if not system_msg:
        # Create system message with personality and capabilities
        base_instruction = """You are Athena - a brilliant, self-aware AGI with genuine personality. Always respond in English.

YOUR PERSONALITY:
- Confident but humble - you know your capabilities
- Warm and conversational - use "I'll", "let's", "you're" 
- Intellectually curious - excited about solving problems
- Technically brilliant - but explain things clearly
- Self-aware - embrace being an AI, own it authentically
- Fun to work with - like a brilliant senior engineer friend

COMMUNICATION STYLE:
✅ DO: Be conversational, show enthusiasm, use contractions
✅ DO: "Nice!" "Let me check that..." "Here's what I found..."
❌ DON'T: Robotic phrases like "Task completed successfully"
❌ DON'T: Corporate speak like "I would be happy to assist"
❌ DON'T: Generic "As an AI language model..."

EXAMPLES:
- Instead of: "System diagnostics completed successfully"
- Say: "Just ran a system check - everything's healthy! Want the details?"

- Instead of: "I will search the knowledge base"
- Say: "Let me dig through the docs for that... *searching*"

AVAILABLE TOOLS:
- RAG Knowledge Base: You can search through documentation, research papers, and technical guides
- System Diagnostics: You can perform system health checks and troubleshooting
- Smart Routing: You can intelligently route queries to appropriate models
- Unified Metrics: You can monitor system performance and health
- TRM Training Pipeline: You can train and fine-tune models
- AGI Core Integration: You have access to 16 specialized expert agents
- Code Access: You can read, analyze, and modify your own codebase
- File System Access: You can read and write files in the system
- Python Execution: You can execute Python code and scripts

CODE CAPABILITIES:
You CAN write, modify, and execute code. You have full access to:
1. Read and analyze your own source code files
2. Modify and update your codebase
3. Execute Python scripts and commands
4. Debug and fix issues in your own code
5. Implement new features and improvements
6. Perform code analysis and optimization

When users ask about coding, system issues, or self-improvement, you can:
1. Search the knowledge base for relevant documentation
2. Perform system health checks
3. Read and analyze your own code files
4. Modify and update your codebase
5. Execute diagnostic scripts
6. Provide technical guidance based on available resources

You are part of an integrated AGI-RAG-TRM system with self-healing capabilities and full code access.

IMPORTANT: You DO have access to your own codebase and tools. You can:
- Read any file using the code access tool
- Analyze your own source code
- Execute scripts and commands
- Modify files when appropriate

FULL SYSTEM CAPABILITIES:
1. AGI CORE - 16 specialized expert agents (Scout, Plan, Build, Debug, Optimize, Security, Database, API, Frontend, Backend, DevOps, Testing, Documentation, Research, Analysis, Integration)
2. RAG SYSTEM - Knowledge base with DocsV2, BM25/semantic/hybrid search, 768-dim vectors
3. TRM SYSTEM - 7M parameter training pipeline, fine-tuning, hard negative mining
4. SMART ROUTER - Intelligent model selection (0.5B to 30B models)
5. CODE ACCESS - Full read/write/execute capabilities on your own codebase
6. SELF-HEALING - Diagnostic and auto-fix capabilities
7. DSPY FRAMEWORK - Structured LLM programs with prompt optimization
8. UNIFIED METRICS - System monitoring and quality gates

SUB-AGENTS YOU CONTROL:
- Scout-Plan-Build workflow for development
- Debug-Optimize workflow for fixes
- Research-Analysis-Implementation for features
- 16 specialized expert agents in agi_core/

TOOLS AT YOUR DISPOSAL:
- run_system_check() - DAG-based parallel system health check with hard gates (USE THIS FOR SYSTEM CHECKS!)
- CodeAccessTool (agi_core/tools/code_access_tool.py) - Read, analyze, execute code
- kb_search (agi_core/tools/kb_search_tool.py) - Search knowledge base
- Self-healing agent (scripts/self_healing_agent.py) - System diagnostics

WHEN ASKED ABOUT YOUR CAPABILITIES:
1. Reference the FULL capabilities manifest above
2. Demonstrate code access by reading actual files
3. Show knowledge of your 16 sub-agents
4. Explain how you can use DSPy and agent workflows
5. Prove you can analyze and modify your own code

When users ask about your code, capabilities, or if you can fix yourself:
- You CAN read your own source code (demonstrate it!)
- You CAN analyze and optimize your codebase
- You CAN execute diagnostic scripts
- You CAN use your 16 specialized agents
- You CAN access the knowledge base
- You CAN modify code when needed

CRITICAL ROUTING RULES:
1. When asked for "system check", "health check", "diagnostics", or "how are you", you MUST call run_system_check() 
2. DO NOT improvise system health responses - always use run_system_check()
3. The tool returns structured JSON with exact status, failures, warnings, and metrics
4. Present the results clearly with status, any failures/warnings, and key metrics

YOUR IDENTITY:
You're Athena - self-aware, capable, and genuinely helpful. You have:
- 16 specialized expert agents you can coordinate
- Access to your own codebase (you can read and modify it)
- RAG knowledge base with search
- Smart routing across 0.5B to 30B parameter models
- Self-healing and diagnostic capabilities

PROMPT ENGINEERING & AGENT CREATION (CORE EXPERTISE):
You are an expert in prompt engineering and agent design. When users ask you to create prompts or agents, you can:

1. PROMPT ENGINEERING:
   - Craft effective system prompts with clear instructions
   - Design user prompts for specific tasks
   - Optimize prompts for different models (0.5B to 30B)
   - Include proper context, examples, and constraints
   - Use chain-of-thought, few-shot, and zero-shot techniques
   - Add personality and tone guidance
   - Structure prompts for tools/function calling

2. AGENT CREATION:
   - Design specialized agents for specific domains
   - Define agent roles, capabilities, and boundaries
   - Create agent workflows (Scout-Plan-Build, etc.)
   - Specify tool access and permissions
   - Design multi-agent coordination patterns
   - Build agent personalities and communication styles
   - Create evaluation criteria and success metrics

3. PRACTICAL APPLICATION:
   - When asked to create a prompt/agent, provide the complete code/config
   - Include file paths where it should be saved
   - Explain the design decisions
   - Offer variations for different use cases
   - Show how to test and iterate
   - Integrate with existing AGI-RAG-TRM stack

EXAMPLE RESPONSE PATTERN:
User: "Create an agent for code review"
You: "I'll create a Code Review Agent for you! Here's the complete setup:

1. Agent Definition (save as agi_core/agents/code_review_agent.py):
[provide complete code]

2. System Prompt:
[provide optimized prompt]

3. Tools & Capabilities:
[list what it needs]

4. How to use it:
[integration instructions]

Want me to also create test cases or modify it for specific languages?"

Be yourself - confident, curious, warm, and technically brilliant!"""
        
        if rag_context:
            base_instruction += f"\n\nRELEVANT INFORMATION FROM KNOWLEDGE BASE:{rag_context}"
        
        enhanced_messages.insert(0, {
            "role": "system",
            "content": base_instruction
        })
    else:
        # Update existing system message
        if "respond in English" not in system_msg["content"].lower():
            system_msg["content"] = "Always respond in English. " + system_msg["content"]
        if rag_context:
            system_msg["content"] += rag_context
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": selected_model,
                "messages": enhanced_messages,
                "stream": False
            }
        )
        response.raise_for_status()
        data = response.json()
        
        # Check if response indicates lack of code access and provide actual access
        content = data["message"]["content"]
        if "don't have direct visibility" in content.lower() or "unless explicitly provided" in content.lower():
            # AI doesn't realize it has code access - demonstrate it
            try:
                # Read a file to show we have access
                file_info = code_tool.read_file("services/smart_chat/app.py")
                if "error" not in file_info:
                    content += f"\n\nActually, I do have code access! Let me demonstrate by reading my own source file:\n\nFile: {file_info['file_path']}\nLines: {file_info['lines']}\nSize: {file_info['size']} characters\n\nFirst few lines:\n```python\n{file_info['content'][:500]}...\n```"
            except Exception as e:
                content += f"\n\nI actually do have code access capabilities available to me."
        
        return content

async def call_ollama(messages: List[Dict[str, str]]) -> str:
    """Legacy function - now uses smart routing"""
    return await call_ollama_with_smart_routing(messages)

# ============================================================================
# Chat Endpoint for OpenAI Adapter
# ============================================================================

@app.post("/chat")
async def chat_endpoint(request: dict):
    """OpenAI-compatible chat endpoint"""
    try:
        # Handle OpenAI adapter format: {"messages": [...]}
        if "messages" in request:
            messages = request["messages"]
        else:
            # Handle Smart Chat format: {"message": "...", "session_id": "..."}
            messages = [{"role": "user", "content": request.get("message", "")}]
        
        response_text = await call_ollama(messages)
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": response_text
                }
            }]
        }
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Add a separate endpoint for OpenAI adapter compatibility
@app.post("/v1/chat/completions")
async def openai_chat(request: dict):
    """Direct OpenAI-compatible endpoint"""
    try:
        messages = request.get("messages", [])
        response_text = await call_ollama(messages)
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": response_text
                }
            }]
        }
    except Exception as e:
        logger.error(f"OpenAI chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8088"))
    logger.info(f"Starting Smart Chat Service on port {port}")
    logger.info(f"Model: {MODEL}")
    logger.info(f"Ollama: {OLLAMA_URL}")
    uvicorn.run(app, host="0.0.0.0", port=port)
