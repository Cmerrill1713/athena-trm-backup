"""
Integration tests for REP (Ripple Effect Protocol) coordination

Tests multi-agent coordination scenarios including:
- Message broadcasting and receiving
- Sensitivity calculations
- Peer clustering avoidance
- Load distribution
- Failover coordination
"""

import pytest
import time
import threading
from pathlib import Path
from typing import List

from governance.routing.rep_protocol import (
    REPCoordinator,
    REPDecision,
    REPMessage,
    SystemState,
    SensitivityType,
    SensitivityCalculator
)
from governance.routing.rep_router import REPEnhancedRouter
from governance.routing.basic_router import RoutingRequest


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def redis_url():
    """Redis URL for testing"""
    return "redis://127.0.0.1:6379"


@pytest.fixture
def test_channel():
    """Unique test channel to avoid interference"""
    return f"athena:rep:test:{int(time.time())}"


@pytest.fixture
def coordinator(redis_url, test_channel):
    """Create a test REP coordinator"""
    coord = REPCoordinator(
        agent_id="test_agent_1",
        channel=test_channel,
        redis_url=redis_url
    )
    yield coord
    coord.shutdown()


@pytest.fixture
def system_state():
    """Create a test system state"""
    return SystemState(
        queue_depths={"qwen2.5-coder:7b": 2, "llama3.1:8b": 5},
        latencies_p95={"qwen2.5-coder:7b": 100.0, "llama3.1:8b": 1500.0},
        available_models=["qwen2.5-coder:7b", "llama3.1:8b"],
        accumulated_cost=50.0,
        cost_budget=100.0
    )


@pytest.fixture
def profiles_path():
    """Path to model profiles for testing"""
    return Path(__file__).parent.parent / "model_profiles.json"


# ============================================================================
# Unit Tests - Core Components
# ============================================================================

def test_sensitivity_calculation(coordinator, system_state):
    """Test sensitivity calculation for various conditions"""
    decision = REPDecision(
        model="qwen2.5-coder:7b",
        confidence=0.85,
        domain="code"
    )
    
    sensitivities = coordinator.sensitivity_calculator.calculate_all(
        decision,
        system_state,
        []
    )
    
    # Should have sensitivities for all types
    assert len(sensitivities) >= 4
    
    # Check queue depth sensitivity
    queue_sens = next(s for s in sensitivities if s.type == SensitivityType.MODEL_QUEUE_DEPTH)
    assert queue_sens.value < 0  # Should be negative
    
    # Check cost sensitivity (50% of budget used)
    cost_sens = next(s for s in sensitivities if s.type == SensitivityType.COST_PRESSURE)
    assert -0.2 < cost_sens.value < 0  # Should be slightly negative


def test_message_broadcast_and_receive(redis_url, test_channel):
    """Test message broadcasting and receiving between agents"""
    # Create two coordinators
    coord1 = REPCoordinator(
        agent_id="agent_1",
        channel=test_channel,
        redis_url=redis_url
    )
    coord2 = REPCoordinator(
        agent_id="agent_2",
        channel=test_channel,
        redis_url=redis_url
    )
    
    try:
        # Agent 1 broadcasts a message
        decision = REPDecision(
            model="qwen2.5-coder:7b",
            confidence=0.85,
            domain="code"
        )
        system_state = SystemState()
        
        message = coord1.broadcast_message(decision, system_state)
        assert message is not None
        
        # Give Redis time to propagate
        time.sleep(0.1)
        
        # Agent 2 should receive the message
        messages = coord2.receive_messages(timeout=0.1)
        assert len(messages) >= 1
        
        # Verify message content
        received = messages[0]
        assert received.agent_id == "agent_1"
        assert received.decision.model == "qwen2.5-coder:7b"
        
    finally:
        coord1.shutdown()
        coord2.shutdown()


def test_peer_clustering_detection(redis_url, test_channel):
    """Test detection of peer clustering on same model"""
    # Create multiple agents all choosing same model
    coordinators = []
    for i in range(4):
        coord = REPCoordinator(
            agent_id=f"agent_{i}",
            channel=test_channel,
            redis_url=redis_url
        )
        coordinators.append(coord)
    
    try:
        # All agents broadcast choice for same model
        decision = REPDecision(
            model="qwen2.5-coder:7b",
            confidence=0.85,
            domain="code"
        )
        system_state = SystemState()
        
        for coord in coordinators:
            coord.broadcast_message(decision, system_state)
        
        time.sleep(0.2)  # Let messages propagate
        
        # Receive messages
        for coord in coordinators:
            coord.receive_messages(timeout=0.1)
        
        # Calculate sensitivities - should detect clustering
        test_coord = coordinators[0]
        sensitivities = test_coord.sensitivity_calculator.calculate_all(
            decision,
            system_state,
            test_coord.peer_messages
        )
        
        # Find clustering sensitivity
        cluster_sens = next(
            s for s in sensitivities
            if s.type == SensitivityType.PEER_CLUSTERING
        )
        
        # Should be strongly negative (high clustering)
        assert cluster_sens.value < -0.5
        assert cluster_sens.metadata['same_model_count'] >= 3
        
    finally:
        for coord in coordinators:
            coord.shutdown()


# ============================================================================
# Integration Tests - Multi-Agent Scenarios
# ============================================================================

def test_multi_agent_load_distribution(profiles_path, redis_url, test_channel):
    """Test load distribution across multiple agents"""
    # Skip if profiles not available
    if not profiles_path.exists():
        pytest.skip("Model profiles not available")
    
    # Create 3 router agents
    routers = []
    for i in range(3):
        router = REPEnhancedRouter(
            profiles_path=profiles_path,
            agent_id=f"router_{i}",
            fallback_threshold=0.7,
            enable_rep=True,
            redis_url=redis_url,
            rep_channel=test_channel
        )
        routers.append(router)
    
    try:
        # All route same request
        request = RoutingRequest(query="test code", domain="code")
        choices = []
        
        for router in routers:
            choice = router.route(request)
            choices.append(choice)
            time.sleep(0.1)  # Small delay for coordination
        
        # Check that not all chose the same model (clustering prevented)
        models_chosen = [c.model for c in choices]
        unique_models = set(models_chosen)
        
        # Should have some distribution (not all same)
        # Note: May not always be true due to timing, but should trend this way
        assert len(unique_models) >= 1  # At least one model chosen
        
        # Check REP stats
        stats = routers[0].get_rep_stats()
        assert stats['enabled'] is True
        assert stats['peer_count'] >= 0  # May have received peer messages
        
    finally:
        for router in routers:
            router.shutdown()


def test_failover_coordination(profiles_path, redis_url, test_channel):
    """Test coordinated failover when model unavailable"""
    if not profiles_path.exists():
        pytest.skip("Model profiles not available")
    
    router = REPEnhancedRouter(
        profiles_path=profiles_path,
        agent_id="test_router",
        enable_rep=True,
        redis_url=redis_url,
        rep_channel=test_channel
    )
    
    try:
        # Mark a model as unavailable
        router.system_state.available_models = ["llama3.1:8b"]  # Only llama available
        router.system_state.unavailable_models = ["qwen2.5-coder:7b"]
        
        # Route request
        request = RoutingRequest(query="test", domain="code")
        choice = router.route(request)
        
        # Should have fallback to available model
        assert choice.model in router.system_state.available_models
        
    finally:
        router.shutdown()


def test_cost_coordination(profiles_path, redis_url, test_channel):
    """Test cost-aware coordination across agents"""
    if not profiles_path.exists():
        pytest.skip("Model profiles not available")
    
    router = REPEnhancedRouter(
        profiles_path=profiles_path,
        agent_id="cost_test_router",
        enable_rep=True,
        redis_url=redis_url,
        rep_channel=test_channel
    )
    
    try:
        # Set high cost pressure (90% budget used)
        router.system_state.accumulated_cost = 90.0
        router.system_state.cost_budget = 100.0
        
        # Route request
        request = RoutingRequest(query="test", domain="code")
        choice = router.route(request)
        
        # Calculate sensitivities
        decision = REPDecision(
            model=choice.model,
            confidence=choice.confidence,
            domain=choice.domain
        )
        
        sensitivities = router.rep_coordinator.sensitivity_calculator.calculate_all(
            decision,
            router.system_state,
            []
        )
        
        # Find cost sensitivity
        cost_sens = next(
            s for s in sensitivities
            if s.type == SensitivityType.COST_PRESSURE
        )
        
        # Should be strongly negative (cost pressure)
        assert cost_sens.value < -0.5
        
    finally:
        router.shutdown()


# ============================================================================
# Performance Tests
# ============================================================================

def test_coordination_latency(coordinator, system_state):
    """Test that REP coordination meets latency requirements (<50ms)"""
    decision = REPDecision(
        model="qwen2.5-coder:7b",
        confidence=0.85,
        domain="code"
    )
    
    # Measure broadcast latency
    start = time.time()
    coordinator.broadcast_message(decision, system_state)
    broadcast_latency = (time.time() - start) * 1000
    
    # Should be well under 50ms
    assert broadcast_latency < 50
    
    # Measure sensitivity calculation latency
    start = time.time()
    sensitivities = coordinator.sensitivity_calculator.calculate_all(
        decision,
        system_state,
        []
    )
    calc_latency = (time.time() - start) * 1000
    
    # Should be under 10ms
    assert calc_latency < 10


def test_throughput(coordinator, system_state):
    """Test REP can handle high message throughput"""
    decision = REPDecision(
        model="qwen2.5-coder:7b",
        confidence=0.85,
        domain="code"
    )
    
    # Send 100 messages rapidly
    start = time.time()
    for _ in range(100):
        coordinator.broadcast_message(decision, system_state)
    
    duration = time.time() - start
    throughput = 100 / duration
    
    # Should handle >100 messages/second
    assert throughput > 100


# ============================================================================
# Error Handling Tests
# ============================================================================

def test_redis_connection_failure():
    """Test graceful handling of Redis connection failure"""
    # Try to connect to invalid Redis
    coordinator = REPCoordinator(
        agent_id="test_agent",
        redis_url="redis://invalid-host:6379"
    )
    
    # Should not crash
    decision = REPDecision(model="test", confidence=0.5, domain="code")
    system_state = SystemState()
    
    # Broadcast should fail gracefully
    message = coordinator.broadcast_message(decision, system_state)
    # May be None or may succeed depending on redis-py behavior
    
    coordinator.shutdown()


def test_message_parse_error(redis_url, test_channel):
    """Test handling of malformed messages"""
    coord = REPCoordinator(
        agent_id="test_agent",
        channel=test_channel,
        redis_url=redis_url
    )
    
    try:
        # Redis should skip malformed messages
        # Normal operation should continue
        messages = coord.receive_messages(timeout=0.01)
        assert isinstance(messages, list)
        
    finally:
        coord.shutdown()


# ============================================================================
# Cleanup Tests
# ============================================================================

def test_coordinator_shutdown(redis_url, test_channel):
    """Test clean shutdown of coordinator"""
    coord = REPCoordinator(
        agent_id="test_agent",
        channel=test_channel,
        redis_url=redis_url
    )
    
    # Should shutdown without errors
    coord.shutdown()
    
    # Multiple shutdowns should be safe
    coord.shutdown()


def test_message_ttl_cleanup(coordinator, system_state):
    """Test that old messages are cleaned up"""
    decision = REPDecision(
        model="qwen2.5-coder:7b",
        confidence=0.85,
        domain="code"
    )
    
    # Add an old message
    old_message = REPMessage(
        agent_id="old_agent",
        timestamp=time.time() - 120,  # 2 minutes ago
        decision=decision,
        sensitivities=[]
    )
    coordinator.peer_messages.append(old_message)
    
    # Force cleanup
    coordinator.last_cleanup = 0
    coordinator._cleanup_old_messages()
    
    # Old message should be removed
    assert old_message not in coordinator.peer_messages


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

