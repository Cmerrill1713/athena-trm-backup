#!/usr/bin/env python3
"""
Unit tests for RAG reranker functionality
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock

# Add the RAG module to path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'AI-Projects', 'universal-ai-tools'))

from rag.rerank import rerank, load_dynamic_tau, _cosine_similarity

class TestRAGReranker:
    """Test RAG reranker functionality."""

    def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        a = np.array([1, 0, 0])
        b = np.array([0, 1, 0])
        assert _cosine_similarity(a, b) == 0.0

        a = np.array([1, 0, 0])
        b = np.array([1, 0, 0])
        assert _cosine_similarity(a, b) == 1.0

        a = np.array([1, 1, 0])
        b = np.array([1, 1, 0])
        assert abs(_cosine_similarity(a, b) - 1.0) < 1e-6

    @patch('rag.rerank.RAG_RERANK_ENABLED', False)
    def test_rerank_disabled(self):
        """Test reranker pass-through when disabled."""
        candidates = [
            {"doc_id": "a", "orig": 0.9, "text": "Test A"},
            {"doc_id": "b", "orig": 0.5, "text": "Test B"},
        ]

        query_emb = np.array([1, 0, 0])
        result = rerank(query_emb, candidates)

        assert len(result) == 2
        assert result[0]["orig"] == 0.9
        assert result[1]["orig"] == 0.5
        assert all("rerank" in c for c in result)
        assert all(c["rerank"] == c["orig"] for c in result)
        assert all(c.get("used", False) for c in result)

    @patch('rag.rerank.RAG_RERANK_ENABLED', True)
    @patch('rag.rerank.RERANKER', 'cosine')
    def test_rerank_cosine_enabled(self):
        """Test reranker with cosine similarity enabled."""
        candidates = [
            {
                "doc_id": "a",
                "emb": np.array([1, 0, 0]),  # Perfect match with query
                "orig": 0.5,
                "text": "Test A"
            },
            {
                "doc_id": "b",
                "emb": np.array([0, 1, 0]),  # Orthogonal to query
                "orig": 0.9,
                "text": "Test B"
            },
        ]

        query_emb = np.array([1, 0, 0])  # Matches first candidate perfectly

        result = rerank(query_emb, candidates)

        # Should reorder based on rerank score
        assert len(result) == 2
        assert result[0]["doc_id"] == "a"  # Higher rerank score
        assert result[1]["doc_id"] == "b"
        assert all("rerank" in c for c in result)
        assert all(c.get("used", False) for c in result)

    @patch('rag.rerank.RAG_RERANK_ENABLED', True)
    @patch('rag.rerank.load_dynamic_tau')
    def test_rerank_threshold_filtering(self, mock_load_tau):
        """Test threshold-based filtering."""
        mock_load_tau.return_value = 0.7  # High threshold

        candidates = [
            {"doc_id": "a", "emb": np.array([1, 0, 0]), "orig": 0.9, "text": "High score"},
            {"doc_id": "b", "emb": np.array([0, 1, 0]), "orig": 0.3, "text": "Low score"},
            {"doc_id": "c", "emb": np.array([0, 0, 1]), "orig": 0.2, "text": "Very low score"},
        ]

        query_emb = np.array([1, 0, 0])

        result = rerank(query_emb, candidates)

        # Should keep high-scoring items even if below threshold
        assert len(result) >= 1
        assert result[0]["doc_id"] == "a"  # Highest score should be first

    def test_load_dynamic_tau_fallback(self):
        """Test tau loading with database fallback."""
        with patch('rag.rerank.psycopg2') as mock_psycopg2:
            mock_psycopg2.connect.side_effect = Exception("DB error")

            tau = load_dynamic_tau()
            assert tau == 0.45  # Should return default

    def test_load_dynamic_tau_success(self):
        """Test successful tau loading from database."""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = {'value': '0.65'}
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur

        with patch('rag.rerank.psycopg2.connect') as mock_connect:
            mock_connect.return_value = mock_conn

            tau = load_dynamic_tau()
            assert tau == 0.65

class TestRAGStore:
    """Test RAG data storage functionality."""

    @patch('rag.store.psycopg2.connect')
    def test_log_retrieval_success(self, mock_connect):
        """Test successful retrieval logging."""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        mock_connect.return_value = mock_conn

        from rag.store import log_retrieval

        candidates = [
            {"doc_id": "test1", "orig": 0.8, "rerank": 0.9, "used": True},
            {"doc_id": "test2", "orig": 0.6, "rerank": 0.5, "used": False}
        ]

        result = log_retrieval("test-interaction", "test query", candidates)
        assert result is True

    @patch('rag.store.psycopg2.connect')
    def test_log_retrieval_failure(self, mock_connect):
        """Test retrieval logging with database failure."""
        mock_connect.side_effect = Exception("Connection failed")

        from rag.store import log_retrieval

        result = log_retrieval("test-interaction", "test query", [])
        assert result is False

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
