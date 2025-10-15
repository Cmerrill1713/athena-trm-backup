#!/usr/bin/env python3
"""
Local Embedding Service using Ollama
Generates embeddings and stores documents in Weaviate
"""
import json
import time
from datetime import datetime, timezone
import requests
import httpx

class LocalEmbeddingService:
    def __init__(self):
        self.weaviate_url = "http://localhost:8090"
        self.ollama_url = "http://localhost:11434"
        
    def generate_embedding(self, text, model="nomic-embed-text:latest"):
        """Generate embedding using Ollama"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json={
                    "model": model,
                    "prompt": text
                }
            )
            response.raise_for_status()
            result = response.json()
            return result["embedding"]
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None
    
    def add_document_with_embedding(self, class_name, properties, content_field="content"):
        """Add document with locally generated embedding"""
        content = properties.get(content_field, "")
        if not content:
            print("No content to embed")
            return None
            
        # Generate embedding
        embedding = self.generate_embedding(content)
        if embedding is None:
            print("Failed to generate embedding")
            return None
            
        # Add document with embedding
        data = {
            "class": class_name,
            "properties": properties,
            "vector": embedding
        }
        
        try:
            response = requests.post(
                f"{self.weaviate_url}/v1/objects",
                json=data
            )
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error adding document: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error adding document: {e}")
            return None
    
    def generate_sample_data(self):
        """Generate sample data to test the system"""
        print("🧪 Generating sample data with local embeddings...")
        
        # Get current time in RFC3339 format
        now = datetime.now(timezone.utc).isoformat()
        
        # Sample memories
        memories = [
            {
                "serviceId": "weather-agent",
                "memoryType": "conversation", 
                "content": "User asked about current weather conditions in San Francisco. I provided accurate forecast data from weather API.",
                "metadata": json.dumps({"confidence": 0.95, "source": "weather_api"}),
                "timestamp": now
            },
            {
                "serviceId": "code-agent",
                "memoryType": "pattern",
                "content": "Successfully implemented error handling pattern for API calls with retry logic and exponential backoff.",
                "metadata": json.dumps({"pattern_type": "error_handling", "language": "python"}),
                "timestamp": now
            }
        ]
        
        # Sample contexts
        contexts = [
            {
                "contextType": "user_preference",
                "contextKey": "response_style",
                "content": "User prefers concise, technical responses with code examples",
                "createdAt": now,
                "updatedAt": now
            }
        ]
        
        # Sample tools
        tools = [
            {
                "toolName": "weather_lookup",
                "description": "Fetches current weather data for any location",
                "implementationType": "api",
                "implementation": "REST API call to OpenWeatherMap",
                "inputSchema": json.dumps({"location": "string"}),
                "outputSchema": json.dumps({"temperature": "number", "conditions": "string"}),
                "metadata": json.dumps({"api_endpoint": "openweathermap.org"}),
                "createdBy": "system",
                "createdAt": now
            }
        ]
        
        # Add sample data
        added_count = 0
        
        for memory in memories:
            result = self.add_document_with_embedding("AIMemory", memory)
            if result:
                added_count += 1
                print(f"✅ Added memory: {memory['content'][:50]}...")
                
        for context in contexts:
            result = self.add_document_with_embedding("AIContext", context)
            if result:
                added_count += 1
                print(f"✅ Added context: {context['content'][:50]}...")
                
        for tool in tools:
            result = self.add_document_with_embedding("AICustomTool", tool, "description")
            if result:
                added_count += 1
                print(f"✅ Added tool: {tool['toolName']}")
                
        print(f"🎉 Added {added_count} documents with embeddings!")
        return added_count

if __name__ == "__main__":
    service = LocalEmbeddingService()
    service.generate_sample_data()
