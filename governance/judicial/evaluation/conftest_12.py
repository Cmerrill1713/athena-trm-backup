# PyTest configuration for TinyRecursiveModels
import os
import sys

import pytest

# Ensure project root is importable
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# Async tests support
try:
    import asyncio

    @pytest.fixture(scope="session")
    def event_loop():
        """Create an instance of the default event loop for the test session."""
        loop = asyncio.new_event_loop()
        yield loop
        loop.close()
except ImportError:
    pass


# MLX availability check
@pytest.fixture(scope="session")
def mlx_available():
    """Check if MLX is available."""
    try:
        import mlx.core as mx
        return True
    except ImportError:
        return False


@pytest.fixture
def skip_if_no_mlx(mlx_available):
    """Skip test if MLX is not available."""
    if not mlx_available:
        pytest.skip("MLX not available")


# Common fixtures
@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for tests."""
    return tmp_path


@pytest.fixture
def config_dir():
    """Provide path to config directory."""
    return os.path.join(PROJECT_ROOT, "config")


@pytest.fixture
def models_dir():
    """Provide path to models directory."""
    return os.path.join(PROJECT_ROOT, "models")

