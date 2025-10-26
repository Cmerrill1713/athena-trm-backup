#!/usr/bin/env python3
"""
RAG-Aware Router - Intelligent routing between RAG, LLM, and Hybrid modes

Analyzes incoming queries to determine optimal routing:
- RAG: Factual questions, documentation lookups, policy questions
- LLM: Creative tasks, open-ended questions, brainstorming
- Hybrid: Complex queries requiring both retrieval and reasoning
- TRM: Recursive reasoning tasks requiring deliberation
"""

import os
import re
import logging
import httpx
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# Configuration
RAG_GATEWAY_URL = os.getenv("RAG_GATEWAY_URL", "http://localhost:8088")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
TRM_SERVICE_URL = os.getenv("TRM_SERVICE_URL", "http://localhost:8089")

# Routing thresholds
PROBE_THRESHOLD = float(os.getenv("RAG_PROBE_THRESHOLD", "0.65"))  # τ1 from plan
MIN_HYBRID_SCORE = float(os.getenv("RAG_MIN_HYBRID_SCORE", "0.50"))


class RouteDecision(Enum):
    """Route decision types"""
    RAG = "rag"              # Pure retrieval
    LLM = "llm"              # Pure generation
    HYBRID = "hybrid"        # Retrieval + generation
    TRM = "trm"              # TRM recursive reasoning
    TRM_RAG = "trm_rag"      # TRM with RAG context


@dataclass
class QueryIntent:
    """Classified query intent"""
    category: str  # faq | howto | code | policy | brainstorm | reasoning
    confidence: float
    features: Dict[str, Any]


@dataclass
class RoutingResult:
    """Result of routing decision"""
    route: RouteDecision
    confidence: float
    reasoning: str
    probe_score: Optional[float] = None
    intent: Optional[QueryIntent] = None


class IntentClassifier:
    """
    Fast intent classifier for routing decisions.
    
    Uses pattern matching and heuristics for low-latency classification.
    Can be upgraded to a fine-tuned TRM classifier later.
    """
    
    # Intent patterns (regex-based for speed)
    PATTERNS = {
        "faq": [
            r"\b(what is|what are|who is|when was|where is|define)\b",
            r"\b(explain|describe|tell me about)\b",
            r"\?$"  # Ends with question mark
        ],
        "howto": [
            r"\b(how to|how do|how can|steps to|guide|tutorial|walkthrough)\b",
            r"\b(install|setup|configure|deploy|create|build|implement)\b"
        ],
        "code": [
            r"\b(function|class|method|variable|import|syntax|error|debug)\b",
            r"\b(code|script|program|implementation)\b",
            r"```",  # Code blocks
            r"\bfix\b.*\berror\b"
        ],
        "policy": [
            r"\b(policy|rule|regulation|compliance|allowed|forbidden|permitted)\b",
            r"\b(governance|security|access control|authorization)\b"
        ],
        "reasoning": [
            r"\b(analyze|compare|evaluate|assess|consider|deliberate)\b",
            r"\b(pros and cons|advantages|disadvantages|trade-offs)\b",
            r"\b(why|reasoning|rationale|justify)\b"
        ],
        "brainstorm": [
            r"\b(idea|creative|brainstorm|imagine|design|invent|innovate)\b",
            r"\b(suggest|propose|alternative|option)\b"
        ]
    }
    
    def classify(self, query: str) -> QueryIntent:
        """
        Classify query intent using pattern matching.
        
        Returns:
            QueryIntent with category and confidence
        """
        query_lower = query.lower()
        
        # Count pattern matches per category
        scores = {category: 0 for category in self.PATTERNS}
        
        for category, patterns in self.PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    scores[category] += 1
        
        # Find best match
        best_category = max(scores, key=scores.get)
        best_score = scores[best_category]
        
        # Calculate confidence (normalize by number of patterns)
        total_patterns = sum(len(patterns) for patterns in self.PATTERNS.values())
        confidence = min(best_score / 3.0, 1.0)  # Cap at 1.0
        
        # Extract features
        features = {
            "length": len(query),
            "has_question_mark": "?" in query,
            "word_count": len(query.split()),
            "lexical_density": self._calculate_lexical_density(query)
        }
        
        return QueryIntent(
            category=best_category if best_score > 0 else "general",
            confidence=confidence,
            features=features
        )
    
    def _calculate_lexical_density(self, text: str) -> float:
        """Calculate lexical density (ratio of unique words to total words)"""
        words = text.lower().split()
        if not words:
            return 0.0
        unique_words = set(words)
        return len(unique_words) / len(words)


class RAGRouter:
    """
    RAG-aware router that intelligently routes queries to:
    - RAG: High-confidence retrieval queries
    - Hybrid: Medium-confidence queries needing both retrieval + generation
    - LLM: Creative/open-ended queries
    - TRM: Reasoning tasks
    - TRM+RAG: Reasoning with knowledge base grounding
    """
    
    def __init__(
        self,
        rag_gateway_url: str = RAG_GATEWAY_URL,
        ollama_url: str = OLLAMA_URL,
        trm_service_url: str = TRM_SERVICE_URL,
        probe_threshold: float = PROBE_THRESHOLD
    ):
        self.rag_gateway_url = rag_gateway_url
        self.ollama_url = ollama_url
        self.trm_service_url = trm_service_url
        self.probe_threshold = probe_threshold
        
        self.classifier = IntentClassifier()
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def route(self, query: str, user_hint: Optional[str] = None) -> RoutingResult:
        """
        Route query to optimal backend.
        
        Args:
            query: User query
            user_hint: Optional routing hint ("force_rag", "force_llm", etc.)
        
        Returns:
            RoutingResult with routing decision and reasoning
        """
        logger.info(f"Routing query: {query[:100]}")
        
        # Step 1: Check user hint
        if user_hint:
            if user_hint == "force_rag":
                return RoutingResult(
                    route=RouteDecision.RAG,
                    confidence=1.0,
                    reasoning="User forced RAG mode",
                    intent=None
                )
            elif user_hint == "force_llm":
                return RoutingResult(
                    route=RouteDecision.LLM,
                    confidence=1.0,
                    reasoning="User forced LLM mode",
                    intent=None
                )
        
        # Step 2: Classify intent
        intent = self.classifier.classify(query)
        logger.info(f"Intent: {intent.category} (confidence: {intent.confidence:.2f})")
        
        # Step 3: Fast BM25 probe (check if KB has relevant docs)
        probe_score = await self._probe_kb(query)
        logger.info(f"KB probe score: {probe_score:.3f}")
        
        # Step 4: Apply routing policy
        route, reasoning = self._apply_routing_policy(intent, probe_score)
        
        return RoutingResult(
            route=route,
            confidence=max(intent.confidence, probe_score) if probe_score else intent.confidence,
            reasoning=reasoning,
            probe_score=probe_score,
            intent=intent
        )
    
    async def _probe_kb(self, query: str, top_k: int = 3) -> float:
        """
        Fast BM25 probe to check if KB has relevant documents.
        
        Returns:
            Highest relevance score (0.0-1.0)
        """
        try:
            response = await self.client.post(
                f"{self.rag_gateway_url}/kb/search",
                json={
                    "query": query,
                    "topK": top_k,
                    "mode": "bm25",  # Fast keyword search
                    "semanticEnabled": False
                },
                timeout=2.0  # Fast probe
            )
            
            if response.status_code == 200:
                data = response.json()
                hits = data.get("hits", [])
                
                if hits:
                    # Return highest score
                    return max(hit.get("score", 0.0) for hit in hits)
            
            return 0.0
            
        except Exception as e:
            logger.warning(f"KB probe failed: {e}")
            return 0.0
    
    def _apply_routing_policy(self, intent: QueryIntent, probe_score: float) -> Tuple[RouteDecision, str]:
        """
        Apply routing policy based on intent and probe score.
        
        Policy (from user plan):
        - if probe_score >= τ1 (0.65) → RAG
        - else if intent ∈ {faq, howto, policy, code} → Hybrid
        - else if intent == reasoning → TRM or TRM+RAG (depending on probe)
        - else → LLM
        """
        
        # High-confidence retrieval → RAG
        if probe_score >= self.probe_threshold:
            return RouteDecision.RAG, f"High KB relevance (score={probe_score:.2f})"
        
        # Reasoning tasks → TRM (with RAG if relevant docs exist)
        if intent.category == "reasoning":
            if probe_score >= MIN_HYBRID_SCORE:
                return RouteDecision.TRM_RAG, f"Reasoning with KB context (probe={probe_score:.2f})"
            else:
                return RouteDecision.TRM, "Recursive reasoning without KB"
        
        # Factual/procedural intents → Hybrid (some KB relevance)
        if intent.category in ["faq", "howto", "policy", "code"]:
            if probe_score >= MIN_HYBRID_SCORE:
                return RouteDecision.HYBRID, f"Factual query with some KB relevance (intent={intent.category}, probe={probe_score:.2f})"
            else:
                return RouteDecision.RAG, f"Factual query but low KB match → try semantic search (intent={intent.category})"
        
        # Creative/open-ended → LLM
        if intent.category == "brainstorm":
            return RouteDecision.LLM, "Creative/open-ended query"
        
        # Default: Hybrid (safe fallback)
        return RouteDecision.HYBRID, f"Default hybrid mode (intent={intent.category}, probe={probe_score:.2f})"
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Convenience function
async def route_query(query: str, user_hint: Optional[str] = None) -> RoutingResult:
    """
    Quick routing function.
    
    Usage:
        result = await route_query("How do I reset tokens?")
        print(f"Route to: {result.route.value}")
    """
    router = RAGRouter()
    try:
        return await router.route(query, user_hint)
    finally:
        await router.close()


if __name__ == "__main__":
    import asyncio
    
    async def test():
        router = RAGRouter()
        
        test_queries = [
            "What is recursive reasoning?",  # Should route to RAG
            "How do I train TRM models?",     # Should route to Hybrid or RAG
            "Brainstorm ideas for AGI",       # Should route to LLM
            "Compare TRM vs Transformer",     # Should route to TRM or TRM_RAG
            "Fix this code error: NameError", # Should route to RAG or Hybrid
        ]
        
        try:
            for query in test_queries:
                result = await router.route(query)
                print(f"\nQuery: {query}")
                print(f"  Route: {result.route.value}")
                print(f"  Confidence: {result.confidence:.2f}")
                print(f"  Reasoning: {result.reasoning}")
                if result.intent:
                    print(f"  Intent: {result.intent.category}")
        finally:
            await router.close()
    
    asyncio.run(test())

