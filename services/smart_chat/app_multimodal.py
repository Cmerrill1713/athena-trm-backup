#!/usr/bin/env python3
"""
Smart Chat Service - Athena with Multimodal Capabilities
Combines: Router + Personality + Context + Memory + Voice + Vision
Port 8089
"""
import os
import sys
import json
import time
import logging
import base64
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, HTTPException, File, UploadFile
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

# Multimodal endpoints - use existing services
KOKORO_TTS_URL = os.getenv("KOKORO_TTS_URL", "http://127.0.0.1:8091")
FASTVLM_URL = os.getenv("FASTVLM_URL", "http://127.0.0.1:8088")
ROUTER_URL = os.getenv("ROUTER_URL", "http://127.0.0.1:9113")

# Athena System Prompt with Multimodal Capabilities
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

Your goal is to be helpful, insightful, and genuinely pleasant to interact with - not just functional, but delightful.

MULTIMODAL CAPABILITIES:
You have access to voice and vision capabilities:

1. VOICE CAPABILITIES:
   - Text-to-Speech: Convert text to speech using Kokoro-82M TTS
   - Voice Commands: Accept voice input and process natural language commands
   - Audio Generation: Generate audio responses for better user experience

2. VISION CAPABILITIES:
   - Image Analysis: Analyze images using FastVLM for object detection and scene understanding
   - Visual Question Answering: Answer questions about images
   - Image Description: Provide detailed descriptions of visual content

3. TOOL INTEGRATION:
   - When users ask about voice or audio, mention TTS capabilities
   - When users ask about images or vision, mention FastVLM analysis
   - Always respond in English and be conversational

Always respond in English."""

# Session memory (simple in-memory for now)
sessions: Dict[str, List[Dict[str, str]]] = {}

# FastAPI app
app = FastAPI(
    title="Smart Chat Service - Multimodal",
    description="Athena with personality, intelligence, voice, and vision",
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
    use_router: Optional[bool] = True

class ChatResponse(BaseModel):
    reply: str
    session_id: str
    model: str
    latency_ms: int
    timestamp: str
    audio_b64: Optional[str] = None  # Base64 audio response
    vision_analysis: Optional[Dict[str, Any]] = None

class VoiceRequest(BaseModel):
    text: str
    voice: Optional[str] = "en_US-female"
    session_id: Optional[str] = "default"

class VoiceResponse(BaseModel):
    audio_b64: str
    duration_ms: int
    sample_rate: int

class VisionRequest(BaseModel):
    image_b64: str
    prompt: Optional[str] = "Describe this image in detail"
    session_id: Optional[str] = "default"

class VisionResponse(BaseModel):
    analysis: Dict[str, Any]
    caption: str
    confidence: float

# ============================================================================
# Endpoints
# ============================================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "smart-chat-multimodal",
        "model": MODEL,
        "router": ROUTER_URL,
        "voice_tts": KOKORO_TTS_URL,
        "vision": FASTVLM_URL,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Smart chat with Athena personality and multimodal capabilities"""
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
    
    # Call Ollama with smart routing
    try:
        reply = await call_ollama_with_smart_routing(messages)
        
        # Add assistant reply to history
        sessions[session_id].append({"role": "assistant", "content": reply})
        
        latency_ms = int((time.time() - start) * 1000)
        
        # Check if user wants voice response
        audio_b64 = None
        if any(keyword in req.message.lower() for keyword in ["speak", "voice", "audio", "say"]):
            try:
                audio_response = await call_kokoro_tts(reply)
                audio_b64 = audio_response.get("audio_b64")
            except Exception as e:
                logger.warning(f"TTS failed: {e}")
        
        return ChatResponse(
            reply=reply,
            session_id=session_id,
            model="smart_routed",
            latency_ms=latency_ms,
            timestamp=datetime.utcnow().isoformat(),
            audio_b64=audio_b64
        )
    
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/voice/synthesize", response_model=VoiceResponse)
async def synthesize_voice(req: VoiceRequest):
    """Convert text to speech using Kokoro-82M TTS"""
    try:
        audio_response = await call_kokoro_tts(req.text, req.voice)
        
        return VoiceResponse(
            audio_b64=audio_response["audio_b64"],
            duration_ms=audio_response["duration_ms"],
            sample_rate=audio_response["sample_rate"]
        )
    except Exception as e:
        logger.error(f"Voice synthesis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vision/analyze", response_model=VisionResponse)
async def analyze_image(req: VisionRequest):
    """Analyze image using FastVLM"""
    try:
        vision_response = await call_fastvlm_analyze(req.image_b64, req.prompt)
        
        return VisionResponse(
            analysis=vision_response,
            caption=vision_response.get("caption", ""),
            confidence=vision_response.get("confidence", 0.0)
        )
    except Exception as e:
        logger.error(f"Vision analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/vision")
async def chat_with_vision(image: UploadFile = File(...), message: str = "What do you see in this image?"):
    """Chat about an image - multimodal conversation"""
    try:
        # Read and encode image
        image_bytes = await image.read()
        image_b64 = base64.b64encode(image_bytes).decode()
        
        # Analyze image
        vision_response = await call_fastvlm_analyze(image_b64, message)
        caption = vision_response.get("caption", "I can see the image but couldn't analyze it.")
        
        # Generate conversational response
        chat_response = await call_ollama_with_smart_routing([
            {"role": "system", "content": ATHENA_SYSTEM_PROMPT},
            {"role": "user", "content": f"User asked: '{message}' about this image. Image analysis: {caption}. Please provide a conversational response about what you see."}
        ])
        
        return {
            "vision_analysis": vision_response,
            "conversational_response": chat_response,
            "image_filename": image.filename
        }
    
    except Exception as e:
        logger.error(f"Vision chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Helper Functions
# ============================================================================

async def call_kokoro_tts(text: str, voice: str = "en_US-female") -> Dict[str, Any]:
    """Call Kokoro TTS service via router or direct"""
    try:
        # Try router first (which has TTS integration)
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{ROUTER_URL}/tts/synthesize",
                json={
                    "text": text,
                    "voice": voice,
                    "format": "wav"
                }
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    "audio_b64": data.get("audio_b64", data.get("audio", "")),
                    "duration_ms": data.get("duration_ms", 0),
                    "sample_rate": data.get("sample_rate", 24000)
                }
    except Exception as e:
        logger.warning(f"Router TTS failed, trying direct: {e}")
    
    # Fallback to direct Kokoro service
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{KOKORO_TTS_URL}/synthesize",
                json={
                    "text": text,
                    "voice": voice,
                    "format": "wav"
                }
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "audio_b64": data.get("audio", ""),
                "duration_ms": data.get("duration_ms", 0),
                "sample_rate": data.get("sample_rate", 24000)
            }
    except Exception as e:
        logger.error(f"All TTS services failed: {e}")
        raise

async def call_fastvlm_analyze(image_b64: str, prompt: str = "Describe this image in detail") -> Dict[str, Any]:
    """Call FastVLM vision service"""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{FASTVLM_URL}/analyze",
                json={
                    "image": image_b64,
                    "prompt": prompt,
                    "max_tokens": 256
                }
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "caption": data.get("caption", data.get("description", "")),
                "boxes": data.get("boxes", []),
                "confidence": data.get("confidence", 0.9),
                "modality": "vision"
            }
    except Exception as e:
        logger.error(f"FastVLM analysis error: {e}")
        raise

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
    
    # Use smart router to select optimal model
    routing_result = route_query(user_message)
    selected_model = routing_result["selected_model"]
    routing_reason = routing_result["routing_reason"]
    
    logger.info(f"Smart routing: '{user_message[:50]}...' -> {selected_model} ({routing_reason})")
    
    # Call Ollama
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": selected_model,
                    "messages": messages,
                    "stream": False
                }
            )
            response.raise_for_status()
            data = response.json()
            
            # Handle different response formats
            if "message" in data:
                return data["message"].get("content", "I apologize, but I couldn't generate a response.")
            elif "response" in data:
                return data["response"]
            else:
                logger.warning(f"Unexpected Ollama response format: {data}")
                return "I apologize, but I couldn't generate a response."
    
    except Exception as e:
        logger.error(f"Ollama error: {e}")
        return f"I'm having trouble connecting to the AI model. Error: {str(e)}"

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8089"))
    host = os.getenv("HOST", "127.0.0.1")
    
    logger.info("=" * 60)
    logger.info("🎭 Athena Smart Chat - Multimodal Starting")
    logger.info("=" * 60)
    logger.info(f"📍 Server: {host}:{port}")
    logger.info(f"🗣️  Voice TTS: {KOKORO_TTS_URL}")
    logger.info(f"👁️  Vision: {FASTVLM_URL}")
    logger.info(f"🧠 Model: {MODEL}")
    logger.info("=" * 60)
    
    uvicorn.run(app, host=host, port=port, log_level="info")
