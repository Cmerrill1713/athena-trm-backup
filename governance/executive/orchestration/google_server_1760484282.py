"""
Google AI & Cloud MCP Server
Provides tools for Google Gemini and Vertex AI
"""
import os

from fastmcp import FastMCP

mcp = FastMCP("google-ai", dependencies=["google-generativeai", "google-cloud-aiplatform"])

@mcp.tool()
def gemini_generate(prompt: str, model: str = "gemini-pro") -> dict:
    """
    Generate text using Google Gemini
    
    Args:
        prompt: The text prompt to generate from
        model: Gemini model to use (gemini-pro, gemini-pro-vision)
    
    Returns:
        Generated text response
    """
    try:
        import google.generativeai as genai

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return {"error": "GOOGLE_API_KEY not set"}

        genai.configure(api_key=api_key)
        model_obj = genai.GenerativeModel(model)
        response = model_obj.generate_content(prompt)

        return {
            "text": response.text,
            "model": model,
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}

@mcp.tool()
def vertex_predict(
    project: str,
    location: str,
    endpoint_id: str,
    instances: list
) -> dict:
    """
    Make predictions using Vertex AI endpoint
    
    Args:
        project: GCP project ID
        location: GCP region (e.g., us-central1)
        endpoint_id: Vertex AI endpoint ID
        instances: List of prediction instances
    
    Returns:
        Prediction results
    """
    try:
        from google.cloud import aiplatform

        client = aiplatform.gapic.PredictionServiceClient()
        endpoint = f"projects/{project}/locations/{location}/endpoints/{endpoint_id}"

        response = client.predict(endpoint=endpoint, instances=instances)

        return {
            "predictions": [p for p in response.predictions],
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}

@mcp.tool()
def gemini_chat(messages: list, model: str = "gemini-pro") -> dict:
    """
    Multi-turn chat with Gemini
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Gemini model to use
    
    Returns:
        Chat response
    """
    try:
        import google.generativeai as genai

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return {"error": "GOOGLE_API_KEY not set"}

        genai.configure(api_key=api_key)
        model_obj = genai.GenerativeModel(model)
        chat = model_obj.start_chat(history=[])

        # Send last message
        last_msg = messages[-1]["content"] if messages else ""
        response = chat.send_message(last_msg)

        return {
            "content": response.text,
            "model": model,
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}

if __name__ == "__main__":
    mcp.run()

