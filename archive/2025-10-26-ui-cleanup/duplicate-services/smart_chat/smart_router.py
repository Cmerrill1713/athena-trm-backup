#!/usr/bin/env python3
"""
Smart Model Router - Intelligent model selection based on query characteristics
Model Agnostic with Smart Routing
"""

import os
import json
import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelType(Enum):
    TINY = "tiny"      # 0.5B - 3B params (fast, simple queries)
    SMALL = "small"    # 7B params (balanced)
    MEDIUM = "medium"  # 14B params (complex reasoning)
    LARGE = "large"    # 20B+ params (expert tasks)

@dataclass
class ModelConfig:
    name: str
    model_type: ModelType
    parameter_count: str
    size_gb: float
    use_cases: List[str]
    performance_characteristics: Dict[str, str]

class SmartRouter:
    def __init__(self, ollama_url: str = "http://127.0.0.1:11434"):
        self.ollama_url = ollama_url
        self.available_models = self._discover_models()
        self.model_configs = self._initialize_model_configs()
        
    def _discover_models(self) -> List[str]:
        """Discover available models from Ollama"""
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{self.ollama_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            logger.error(f"Failed to discover models: {e}")
        return []
    
    def _initialize_model_configs(self) -> Dict[str, ModelConfig]:
        """Initialize model configurations based on available models"""
        configs = {}
        
        # Model configurations based on your available models
        model_mapping = {
            "qwen2.5:0.5b": ModelConfig(
                name="qwen2.5:0.5b",
                model_type=ModelType.TINY,
                parameter_count="494M",
                size_gb=0.4,
                use_cases=["quick responses", "simple questions", "lightweight tasks"],
                performance_characteristics={"speed": "fast", "quality": "basic", "memory": "low"}
            ),
            "qwen2.5:7b": ModelConfig(
                name="qwen2.5:7b", 
                model_type=ModelType.SMALL,
                parameter_count="7.6B",
                size_gb=4.7,
                use_cases=["general conversation", "moderate reasoning", "balanced tasks"],
                performance_characteristics={"speed": "medium", "quality": "good", "memory": "medium"}
            ),
            "qwen2.5:14b": ModelConfig(
                name="qwen2.5:14b",
                model_type=ModelType.MEDIUM,
                parameter_count="14.8B", 
                size_gb=9.0,
                use_cases=["complex reasoning", "technical analysis", "detailed explanations"],
                performance_characteristics={"speed": "slower", "quality": "high", "memory": "high"}
            ),
            "qwen3-coder:30b": ModelConfig(
                name="qwen3-coder:30b",
                model_type=ModelType.LARGE,
                parameter_count="30.5B",
                size_gb=18.0,
                use_cases=["expert coding", "complex problem solving", "research tasks"],
                performance_characteristics={"speed": "slow", "quality": "expert", "memory": "very_high"}
            ),
            "gpt-oss:20b": ModelConfig(
                name="gpt-oss:20b",
                model_type=ModelType.LARGE,
                parameter_count="20.9B",
                size_gb=13.0,
                use_cases=["expert analysis", "complex reasoning", "research"],
                performance_characteristics={"speed": "slow", "quality": "expert", "memory": "very_high"}
            )
        }
        
        # Only include models that are actually available
        for model_name, config in model_mapping.items():
            if model_name in self.available_models:
                configs[model_name] = config
                
        return configs
    
    def analyze_query(self, query: str) -> Dict[str, any]:
        """Analyze query characteristics to determine routing strategy"""
        query_lower = query.lower()
        
        # Complexity indicators
        complexity_score = 0
        if any(word in query_lower for word in ["detailed", "comprehensive", "explain", "analyze", "technical"]):
            complexity_score += 2
        if any(word in query_lower for word in ["quantum", "algorithm", "mathematical", "research", "expert"]):
            complexity_score += 3
        if any(word in query_lower for word in ["code", "programming", "implementation", "debug"]):
            complexity_score += 2
        if len(query.split()) > 20:
            complexity_score += 1
            
        # Query type classification
        query_type = "general"
        if any(word in query_lower for word in ["code", "program", "function", "class", "api"]):
            query_type = "coding"
        elif any(word in query_lower for word in ["explain", "how", "what", "why", "analyze"]):
            query_type = "explanatory"
        elif any(word in query_lower for word in ["write", "create", "generate", "compose"]):
            query_type = "generative"
        elif any(word in query_lower for word in ["hello", "hi", "thanks", "bye"]):
            query_type = "casual"
            
        # Urgency (based on context clues)
        urgency = "normal"
        if any(word in query_lower for word in ["quick", "fast", "simple", "brief"]):
            urgency = "high"
        elif any(word in query_lower for word in ["detailed", "comprehensive", "thorough"]):
            urgency = "low"
            
        return {
            "complexity_score": complexity_score,
            "query_type": query_type,
            "urgency": urgency,
            "word_count": len(query.split()),
            "estimated_tokens": len(query.split()) * 1.3  # rough estimate
        }
    
    def select_model(self, query_analysis: Dict[str, any], available_memory_gb: float = 50.0) -> Tuple[str, str]:
        """Select the best model based on query analysis and system resources"""
        
        complexity = query_analysis["complexity_score"]
        query_type = query_analysis["query_type"]
        urgency = query_analysis["urgency"]
        
        # Model selection logic
        if query_type == "casual" or urgency == "high":
            # Use tiny model for casual/quick queries
            for model_name, config in self.model_configs.items():
                if config.model_type == ModelType.TINY:
                    return model_name, "fast_response"
                    
        elif query_type == "coding" and complexity >= 3:
            # Use coding specialist for complex coding tasks
            if "qwen3-coder:30b" in self.model_configs:
                return "qwen3-coder:30b", "expert_coding"
                
        elif complexity >= 4 and available_memory_gb >= 20:
            # Use large model for complex reasoning
            for model_name, config in self.model_configs.items():
                if config.model_type == ModelType.LARGE and config.size_gb <= available_memory_gb:
                    return model_name, "expert_reasoning"
                    
        elif complexity >= 2 and available_memory_gb >= 10:
            # Use medium model for moderate complexity
            for model_name, config in self.model_configs.items():
                if config.model_type == ModelType.MEDIUM and config.size_gb <= available_memory_gb:
                    return model_name, "detailed_analysis"
                    
        # Default to small model for balanced performance
        for model_name, config in self.model_configs.items():
            if config.model_type == ModelType.SMALL:
                return model_name, "balanced_performance"
                
        # Fallback to tiny model
        for model_name, config in self.model_configs.items():
            if config.model_type == ModelType.TINY:
                return model_name, "fallback"
                
        return "qwen2.5:7b", "default"  # Ultimate fallback
    
    def route_query(self, query: str, max_tokens: int = 500) -> Dict[str, any]:
        """Main routing function - analyze query and select optimal model"""
        start_time = time.time()
        
        # Analyze the query
        query_analysis = self.analyze_query(query)
        
        # Get system resources (simplified)
        available_memory_gb = 50.0  # Could be made dynamic
        
        # Select model
        selected_model, routing_reason = self.select_model(query_analysis, available_memory_gb)
        
        routing_time = (time.time() - start_time) * 1000
        
        return {
            "selected_model": selected_model,
            "routing_reason": routing_reason,
            "query_analysis": query_analysis,
            "routing_time_ms": routing_time,
            "available_models": list(self.model_configs.keys()),
            "model_info": {
                "name": self.model_configs[selected_model].name,
                "type": self.model_configs[selected_model].model_type.value,
                "parameters": self.model_configs[selected_model].parameter_count,
                "size_gb": self.model_configs[selected_model].size_gb
            }
        }

# Global router instance
router = SmartRouter()

def route_query(query: str, max_tokens: int = 500) -> Dict[str, any]:
    """Convenience function for routing queries"""
    return router.route_query(query, max_tokens)

if __name__ == "__main__":
    # Test the router
    test_queries = [
        "Hello, how are you?",
        "Write a Python function to sort a list",
        "Explain quantum computing and Shor's algorithm in detail",
        "What's the weather like?",
        "Create a comprehensive analysis of machine learning algorithms"
    ]
    
    for query in test_queries:
        result = route_query(query)
        print(f"\nQuery: {query}")
        print(f"Selected: {result['selected_model']} ({result['routing_reason']})")
        print(f"Analysis: {result['query_analysis']}")
        print(f"Model Info: {result['model_info']}")
