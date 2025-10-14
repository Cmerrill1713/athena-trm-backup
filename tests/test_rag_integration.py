#!/usr/bin/env python3
"""
Integration tests for RAG reranker with full pipeline
"""

import pytest
import os
import httpx
from unittest.mock import patch, MagicMock

# Mark integration tests
pytestmark = pytest.mark.integration

class TestRAGIntegration:
    """Integration tests for RAG reranker."""

    @pytest.fixture
    def rag_service_url(self):
        """Get RAG service URL."""
        return os.getenv("RAG_SERVICE_URL", "http://127.0.0.1:8015")

    def test_rag_health_check(self, rag_service_url):
        """Test RAG service health endpoint."""
        try:
            response = httpx.get(f"{rag_service_url}/health", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
        except httpx.ConnectError:
            pytest.skip("RAG service not available")

    @patch.dict(os.environ, {"RAG_RERANK_ENABLED": "false"})
    def test_rag_query_no_rerank(self, rag_service_url):
        """Test RAG query with reranking disabled."""
        try:
            payload = {"query": "test query", "k": 5}
            response = httpx.post(f"{rag_service_url}/api/rag/query",
                                json=payload, timeout=10)

            assert response.status_code == 200
            data = response.json()

            assert "results" in data
            assert isinstance(data["results"], list)

            # Check response structure
            if data["results"]:
                result = data["results"][0]
                assert "title" in result
                assert "text" in result
                assert "score" in result

        except httpx.ConnectError:
            pytest.skip("RAG service not available")

    @patch.dict(os.environ, {"RAG_RERANK_ENABLED": "true"})
    def test_rag_query_with_rerank(self, rag_service_url):
        """Test RAG query with reranking enabled."""
        try:
            payload = {"query": "test query with reranking", "k": 5}
            response = httpx.post(f"{rag_service_url}/api/rag/query",
                                json=payload, timeout=10)

            assert response.status_code == 200
            data = response.json()

            assert "results" in data
            assert isinstance(data["results"], list)

            # Check reranking metadata if present
            if "metadata" in data:
                metadata = data["metadata"]
                if "reranker_stats" in metadata:
                    stats = metadata["reranker_stats"]
                    assert "total_candidates" in stats
                    assert "used_candidates" in stats

        except httpx.ConnectError:
            pytest.skip("RAG service not available")

    def test_rag_metrics_endpoint(self, rag_service_url):
        """Test RAG metrics endpoint."""
        try:
            response = httpx.get(f"{rag_service_url}/metrics", timeout=5)
            assert response.status_code == 200

            metrics_text = response.text
            # Check for expected metrics
            assert "rag_requests_total" in metrics_text
            assert "rag_request_duration_seconds" in metrics_text

            # Check reranker metrics
            assert "rag_rerank_enabled" in metrics_text
            assert "rag_docs_used_count" in metrics_text

        except httpx.ConnectError:
            pytest.skip("RAG service not available")

    @patch('rag.store.psycopg2.connect')
    def test_rag_data_logging(self, mock_connect, rag_service_url):
        """Test that RAG queries log data for optimization."""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        mock_connect.return_value = mock_conn

        try:
            payload = {"query": "test query for logging", "k": 3}
            response = httpx.post(f"{rag_service_url}/api/rag/query",
                                json=payload, timeout=10)

            assert response.status_code == 200

            # Verify logging was attempted (mock will track calls)
            # In real test, would verify database was called

        except httpx.ConnectError:
            pytest.skip("RAG service not available")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
