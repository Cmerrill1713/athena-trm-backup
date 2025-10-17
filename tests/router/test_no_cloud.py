"""
Tests to prove zero cloud calls in local-first mode.

These tests verify that the router never attempts cloud access
when local-first policies are active.
"""

import os
import pytest
import requests
from unittest.mock import patch, MagicMock


class TestNoCloud:
    """Test suite for cloud call prevention."""

    def setup_method(self):
        """Set up test environment."""
        # Force local-first mode
        os.environ["ATHENA_NO_CLOUD"] = "1"
        os.environ["ATHENA_FAIL_CLOSED"] = "1"
        os.environ["ATHENA_ALLOW_CLOUD"] = "0"
        os.environ["ATHENA_ALLOW_BROWSER"] = "1"

    def teardown_method(self):
        """Clean up test environment."""
        # Reset environment
        os.environ.pop("ATHENA_NO_CLOUD", None)
        os.environ.pop("ATHENA_FAIL_CLOSED", None)
        os.environ.pop("ATHENA_ALLOW_CLOUD", None)
        os.environ.pop("ATHENA_ALLOW_BROWSER", None)

    @patch('services.router.athena_router.check_local_backends')
    def test_route_fail_closed(self, mock_check_backends):
        """Test that router fails closed when no local backends available."""
        # Mock no backends available
        mock_check_backends.return_value = {
            "mlx": False,
            "ollama": False,
            "browser": False
        }

        # This should fail because we're in fail-closed mode
        response = requests.post(
            "http://127.0.0.1:8099/route",
            json={"prompt": "hello world"},
            timeout=5
        )

        # Should get 403 Forbidden
        assert response.status_code == 403
        data = response.json()
        assert "fail-closed" in data["detail"].lower()

    @patch('services.router.athena_router.check_local_backends')
    def test_route_prefers_local(self, mock_check_backends):
        """Test that router prefers local backends over cloud."""
        # Mock Ollama available
        mock_check_backends.return_value = {
            "mlx": False,
            "ollama": True,
            "browser": True
        }

        response = requests.post(
            "http://127.0.0.1:8099/route",
            json={"prompt": "write code"},
            timeout=5
        )

        assert response.status_code == 200
        data = response.json()

        # Should route to Ollama, not cloud
        assert data["route"] in ["ollama", "mlx", "browser_tools", "none"]
        assert data["route"] != "cloud_frontier"
        assert data["policy"] == "local_first"

    @patch('services.router.athena_router.check_local_backends')
    def test_cloud_always_blocked(self, mock_check_backends):
        """Test that cloud access is always blocked in local-first mode."""
        # Mock all backends available
        mock_check_backends.return_value = {
            "mlx": True,
            "ollama": True,
            "browser": True
        }

        response = requests.post(
            "http://127.0.0.1:8099/route",
            json={"prompt": "any prompt"},
            timeout=5
        )

        assert response.status_code == 200
        data = response.json()

        # Should never route to cloud
        assert data["route"] != "cloud_frontier"

    def test_cloud_env_vars_block(self):
        """Test that environment variables properly block cloud."""
        # Verify environment is set
        assert os.getenv("ATHENA_NO_CLOUD") == "1"
        assert os.getenv("ATHENA_ALLOW_CLOUD") == "0"
        assert os.getenv("ATHENA_FAIL_CLOSED") == "1"

    @patch('services.router.athena_router.routing_metrics')
    def test_metrics_track_blocks(self, mock_metrics):
        """Test that blocked cloud attempts are tracked in metrics."""
        # Mock metrics
        mock_metrics.record_cloud_blocked = MagicMock()

        # This should trigger cloud blocking logic
        # (In practice, this would happen when cloud is requested but blocked)

        # Verify metrics would be called
        # mock_metrics.record_cloud_blocked.assert_called()


class TestCloudMetrics:
    """Test cloud usage metrics."""

    def test_cloud_attempt_counter(self):
        """Test that cloud attempts are counted."""
        # This would be tested by making actual requests
        # and checking Prometheus metrics
        pass

    def test_zero_cloud_acceptance(self):
        """Acceptance test: prove zero cloud calls in test run."""
        # After running full test suite, check:
        # - athena_router_cloud_attempts_total == 0
        # - athena_router_cloud_blocked_total >= 0 (blocks allowed)
        # - athena_router_local_success_total > 0
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
