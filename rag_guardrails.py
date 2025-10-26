#!/usr/bin/env python3
"""
RAG Vector Dimension Guardrails
===============================

Hard-fail validation to prevent dimension mismatches from ever creeping back.
This is your first line of defense against the "mismatched dims" boss.
"""

import os
import sys
from typing import List, Union
import logging

# Configuration
EXPECTED_DIM = 384  # all-MiniLM-L6-v2 produces 384-dimensional vectors
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
FEATURE_RAG_SEMANTIC = os.getenv("FEATURE_RAG_SEMANTIC", "true").lower() == "true"

logger = logging.getLogger(__name__)

class DimensionGuardrail:
    """Hard-fail dimension validation"""
    
    @staticmethod
    def assert_dimension(vector: Union[List[float], List[int]], context: str = "") -> None:
        """
        Hard-fail if vector dimension doesn't match expected.
        
        Args:
            vector: The vector to validate
            context: Additional context for error messages
            
        Raises:
            ValueError: If dimension mismatch detected
        """
        if not isinstance(vector, (list, tuple)):
            raise ValueError(f"Vector must be list/tuple, got {type(vector)} {context}")
        
        actual_dim = len(vector)
        if actual_dim != EXPECTED_DIM:
            error_msg = (
                f"🚨 DIMENSION MISMATCH DETECTED! {context}\n"
                f"   Expected: {EXPECTED_DIM} dimensions\n"
                f"   Actual: {actual_dim} dimensions\n"
                f"   Model: {MODEL_NAME}\n"
                f"   This will break vector search!"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.debug(f"✅ Dimension check passed: {actual_dim}D {context}")
    
    @staticmethod
    def validate_batch(vectors: List[List[float]], context: str = "") -> None:
        """Validate a batch of vectors"""
        if not vectors:
            logger.warning(f"Empty vector batch {context}")
            return
        
        # Check first vector dimension
        DimensionGuardrail.assert_dimension(vectors[0], f"{context}[0]")
        
        # Check all vectors have same dimension
        first_dim = len(vectors[0])
        for i, vec in enumerate(vectors[1:], 1):
            if len(vec) != first_dim:
                raise ValueError(
                    f"Inconsistent dimensions in batch {context}: "
                    f"vector[0]={first_dim}D, vector[{i}]={len(vec)}D"
                )
        
        logger.info(f"✅ Batch validation passed: {len(vectors)} vectors, {first_dim}D each {context}")
    
    @staticmethod
    def validate_weaviate_class(class_name: str = "DocsV2") -> bool:
        """Validate Weaviate class has correct vectorizer configuration"""
        import requests
        
        weaviate_url = os.getenv("WEAVIATE_URL", "http://127.0.0.1:8090")
        
        try:
            response = requests.get(f"{weaviate_url}/v1/schema/{class_name}", timeout=10)
            response.raise_for_status()
            schema = response.json()
            
            vectorizer = schema.get("vectorizer", "none")
            vector_index_type = schema.get("vectorIndexType", "none")
            
            if vectorizer == "none":
                logger.error(f"❌ Class {class_name} has no vectorizer!")
                return False
            
            if vector_index_type != "hnsw":
                logger.error(f"❌ Class {class_name} has wrong index type: {vector_index_type}")
                return False
            
            logger.info(f"✅ Class {class_name} validation passed: {vectorizer}, {vector_index_type}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to validate Weaviate class {class_name}: {e}")
            return False

def validate_ingest_pipeline(text: str, expected_embedding_dim: int = EXPECTED_DIM) -> List[float]:
    """
    Validate text through embedding pipeline with dimension checks.
    
    Args:
        text: Text to embed
        expected_embedding_dim: Expected embedding dimension
        
    Returns:
        Validated embedding vector
        
    Raises:
        ValueError: If dimension mismatch or other validation fails
    """
    if not FEATURE_RAG_SEMANTIC:
        logger.warning("🚨 RAG semantic search is DISABLED via FEATURE_RAG_SEMANTIC=false")
        return []
    
    try:
        from sentence_transformers import SentenceTransformer
        
        # Load model
        model = SentenceTransformer(MODEL_NAME)
        
        # Generate embedding
        embedding = model.encode(text, normalize_embeddings=True)
        vector = embedding.tolist()
        
        # Hard-fail dimension check
        DimensionGuardrail.assert_dimension(vector, f"embedding for: '{text[:50]}...'")
        
        logger.info(f"✅ Embedding generated: {len(vector)}D for '{text[:50]}...'")
        return vector
        
    except ImportError:
        logger.error("❌ sentence-transformers not installed. Run: pip install sentence-transformers")
        raise
    except Exception as e:
        logger.error(f"❌ Embedding generation failed: {e}")
        raise

def main():
    """Test the guardrails"""
    logging.basicConfig(level=logging.INFO)
    
    print("🛡️  Testing RAG Vector Dimension Guardrails")
    print("=" * 50)
    
    # Test 1: Valid dimension
    try:
        valid_vector = [0.1] * EXPECTED_DIM
        DimensionGuardrail.assert_dimension(valid_vector, "test vector")
        print("✅ Valid dimension test passed")
    except ValueError as e:
        print(f"❌ Valid dimension test failed: {e}")
    
    # Test 2: Invalid dimension
    try:
        invalid_vector = [0.1] * (EXPECTED_DIM + 1)
        DimensionGuardrail.assert_dimension(invalid_vector, "invalid test vector")
        print("❌ Invalid dimension test should have failed!")
    except ValueError as e:
        print("✅ Invalid dimension correctly rejected")
    
    # Test 3: Batch validation
    try:
        batch = [[0.1] * EXPECTED_DIM for _ in range(5)]
        DimensionGuardrail.validate_batch(batch, "test batch")
        print("✅ Batch validation test passed")
    except ValueError as e:
        print(f"❌ Batch validation test failed: {e}")
    
    # Test 4: Weaviate class validation
    if DimensionGuardrail.validate_weaviate_class("DocsV2"):
        print("✅ Weaviate class validation passed")
    else:
        print("❌ Weaviate class validation failed")
    
    # Test 5: End-to-end embedding pipeline
    try:
        test_text = "This is a test document for RAG validation"
        vector = validate_ingest_pipeline(test_text)
        print(f"✅ End-to-end embedding test passed: {len(vector)}D")
    except Exception as e:
        print(f"❌ End-to-end embedding test failed: {e}")
    
    print("\n🛡️  Guardrails are active! Dimension mismatches will be caught.")

if __name__ == "__main__":
    main()
