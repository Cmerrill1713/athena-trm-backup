"""
Conversational Router - Combines natural dialogue with real execution
Brings together UAI chat and AGI Core execution
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)


class ConversationMemory:
    """Maintains conversation history and context"""
    
    def __init__(self, max_history: int = 10):
        self.messages: List[Dict[str, Any]] = []
        self.max_history = max_history
        self.user_context = {}
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to history"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        })
        
        # Trim to max history
        if len(self.messages) > self.max_history * 2:  # Keep pairs
            self.messages = self.messages[-(self.max_history * 2):]
    
    def get_history(self) -> List[Dict[str, str]]:
        """Get conversation history for LLM"""
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in self.messages
        ]
    
    def get_context_summary(self) -> str:
        """Get a summary of current context"""
        if not self.messages:
            return "New conversation"
        
        recent = self.messages[-3:]
        summary = "\n".join([
            f"{msg['role']}: {msg['content'][:100]}..."
            for msg in recent
        ])
        return summary


class ConversationalRouter:
    """
    Routes between natural conversation and task execution.
    
    Flow:
    1. User message arrives
    2. Analyze intent (chat vs action)
    3. If chat → respond conversationally
    4. If action → execute via AGI Core
    5. Maintain conversation memory
    """
    
    def __init__(
        self,
        chat_endpoint: str = "http://localhost:8080/v1/chat/completions",
        execute_endpoint: str = "http://localhost:8100/api/execute"
    ):
        self.chat_endpoint = chat_endpoint
        self.execute_endpoint = execute_endpoint
        self.memory = ConversationMemory()
    
    async def analyze_intent(self, message: str) -> Dict[str, Any]:
        """
        Determine if message is conversational or actionable.
        
        Returns:
            {
                "type": "chat" | "action" | "hybrid",
                "confidence": 0.0-1.0,
                "action_objective": str (if action/hybrid)
            }
        """
        message_lower = message.lower()
        
        # Action keywords
        action_keywords = [
            'run', 'execute', 'check', 'search', 'find', 'analyze',
            'create', 'build', 'test', 'deploy', 'optimize',
            'show me', 'get', 'fetch', 'retrieve', 'download'
        ]
        
        # Chat keywords
        chat_keywords = [
            'how are you', 'what do you think', 'tell me about yourself',
            'hello', 'hi', 'hey', 'thanks', 'thank you',
            'why', 'can you explain', 'what is your', 'who are you'
        ]
        
        # Check for action intent
        has_action = any(kw in message_lower for kw in action_keywords)
        has_chat = any(kw in message_lower for kw in chat_keywords)
        
        # Question words often need information retrieval (hybrid)
        question_words = ['what', 'where', 'when', 'who', 'which']
        is_question = any(message_lower.startswith(qw) for qw in question_words)
        
        # Decide intent
        if has_action and not has_chat:
            return {
                "type": "action",
                "confidence": 0.9,
                "action_objective": message
            }
        elif is_question and not has_chat:
            return {
                "type": "hybrid",  # Answer + retrieve info
                "confidence": 0.7,
                "action_objective": message
            }
        elif has_chat:
            return {
                "type": "chat",
                "confidence": 0.8,
                "action_objective": None
            }
        else:
            # Default to chat for general statements
            return {
                "type": "chat",
                "confidence": 0.6,
                "action_objective": None
            }
    
    async def handle_chat(self, message: str) -> str:
        """Handle pure conversational message"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Build messages with history
                messages = self.memory.get_history()
                messages.append({"role": "user", "content": message})
                
                # Add system prompt for personality
                full_messages = [{
                    "role": "system",
                    "content": (
                        "You are Athena, an advanced AI assistant with real execution capabilities. "
                        "You are curious, helpful, and have a warm personality. "
                        "You can execute real commands, search knowledge bases, and perform actual tasks. "
                        "Be conversational and natural, but also let users know when you can take real action."
                    )
                }] + messages
                
                response = await client.post(
                    self.chat_endpoint,
                    json={
                        "model": "athena-chat",
                        "messages": full_messages,
                        "temperature": 0.7,
                        "max_tokens": 500
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    reply = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    return reply
                else:
                    logger.error(f"Chat endpoint error: {response.status_code}")
                    return "I'm having trouble accessing my conversational system right now."
                    
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return f"I encountered an error: {str(e)}"
    
    async def handle_action(self, objective: str, tools: Optional[List[str]] = None) -> Dict[str, Any]:
        """Handle actionable task via AGI Core"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.execute_endpoint,
                    json={
                        "objective": objective,
                        "tools": tools or [
                            "system.doctor",
                            "rag.query",
                            "mcp.shell",
                            "mcp.fs.read",
                            "mcp.web_search"
                        ],
                        "max_steps": 12,
                        "flags": {"adaptive_trm": True}
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Execute endpoint error: {response.status_code}")
                    return {
                        "status": "error",
                        "result": {"error": f"Execution failed: {response.status_code}"}
                    }
                    
        except Exception as e:
            logger.error(f"Execution error: {e}")
            return {
                "status": "error",
                "result": {"error": str(e)}
            }
    
    async def handle_hybrid(self, message: str) -> Dict[str, Any]:
        """
        Handle hybrid request (conversational + action).
        Example: "What is Docker?" → Search knowledge base + explain
        """
        # First, get information via action
        action_result = await self.handle_action(message, tools=["rag.query", "mcp.web_search"])
        
        # Then, formulate conversational response
        context = ""
        if action_result.get("result", {}).get("artifacts"):
            for artifact in action_result["result"]["artifacts"]:
                if artifact.get("type") == "rag_context":
                    context = artifact.get("content", "")
        
        # Build conversational response with context
        chat_prompt = f"""Based on this information:

{context}

Please answer: {message}

Provide a natural, conversational response."""
        
        chat_response = await self.handle_chat(chat_prompt)
        
        return {
            "type": "hybrid",
            "response": chat_response,
            "execution": action_result,
            "context_used": bool(context)
        }
    
    async def route(self, message: str) -> Dict[str, Any]:
        """
        Main routing method.
        
        Args:
            message: User's message
        
        Returns:
            Response with type, content, and metadata
        """
        # Add user message to memory
        self.memory.add_message("user", message)
        
        # Analyze intent
        intent = await self.analyze_intent(message)
        logger.info(f"Intent analysis: {intent['type']} (confidence: {intent['confidence']:.2f})")
        
        # Route based on intent
        if intent["type"] == "action":
            # Execute task
            result = await self.handle_action(intent["action_objective"])
            
            # Create conversational summary
            if result.get("status") == "completed":
                summary = f"✅ I've completed that task! {result.get('result', {}).get('summary', '')}"
            else:
                summary = f"I tried to execute that, but encountered an issue: {result.get('result', {}).get('error', 'Unknown error')}"
            
            self.memory.add_message("assistant", summary, {"execution": result})
            
            return {
                "type": "action",
                "response": summary,
                "execution": result,
                "intent": intent
            }
        
        elif intent["type"] == "hybrid":
            # Retrieve info + explain
            result = await self.handle_hybrid(message)
            self.memory.add_message("assistant", result["response"], {"type": "hybrid"})
            return result
        
        else:
            # Pure conversation
            response = await self.handle_chat(message)
            self.memory.add_message("assistant", response)
            
            return {
                "type": "chat",
                "response": response,
                "intent": intent
            }
    
    def reset_conversation(self):
        """Clear conversation history"""
        self.memory = ConversationMemory()
        logger.info("Conversation reset")
