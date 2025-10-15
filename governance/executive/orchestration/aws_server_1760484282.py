"""
Amazon AWS AI MCP Server
Provides tools for AWS Bedrock, SageMaker, and S3
"""
import json
import os

from fastmcp import FastMCP

mcp = FastMCP("aws-ai", dependencies=["boto3"])

@mcp.tool()
def bedrock_invoke(
    model_id: str,
    prompt: str,
    max_tokens: int = 1000,
    temperature: float = 0.7
) -> dict:
    """
    Invoke AWS Bedrock AI models
    
    Args:
        model_id: Bedrock model ID (e.g., anthropic.claude-v2)
        prompt: Text prompt
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
    
    Returns:
        Model response
    """
    try:
        import boto3

        client = boto3.client(
            'bedrock-runtime',
            region_name=os.getenv("AWS_REGION", "us-east-1")
        )

        body = json.dumps({
            "prompt": prompt,
            "max_tokens_to_sample": max_tokens,
            "temperature": temperature,
        })

        response = client.invoke_model(
            modelId=model_id,
            body=body
        )

        result = json.loads(response['body'].read())

        return {
            "completion": result.get("completion", result),
            "model": model_id,
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}

@mcp.tool()
def sagemaker_predict(endpoint_name: str, data: dict) -> dict:
    """
    Make predictions using SageMaker endpoint
    
    Args:
        endpoint_name: SageMaker endpoint name
        data: Input data for prediction
    
    Returns:
        Prediction results
    """
    try:
        import boto3

        client = boto3.client('sagemaker-runtime')

        response = client.invoke_endpoint(
            EndpointName=endpoint_name,
            Body=json.dumps(data),
            ContentType='application/json'
        )

        result = json.loads(response['Body'].read())

        return {
            "predictions": result,
            "endpoint": endpoint_name,
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}

@mcp.tool()
def s3_list_objects(bucket: str, prefix: str = "", max_keys: int = 100) -> dict:
    """
    List objects in S3 bucket
    
    Args:
        bucket: S3 bucket name
        prefix: Object key prefix filter
        max_keys: Maximum number of keys to return
    
    Returns:
        List of S3 object keys
    """
    try:
        import boto3

        s3 = boto3.client('s3')
        response = s3.list_objects_v2(
            Bucket=bucket,
            Prefix=prefix,
            MaxKeys=max_keys
        )

        objects = [obj['Key'] for obj in response.get('Contents', [])]

        return {
            "objects": objects,
            "count": len(objects),
            "bucket": bucket,
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}

if __name__ == "__main__":
    mcp.run()

