"""
Circuit Breaker - Per-model failure protection

Tracks failure rates in sliding windows and opens breaker
when thresholds are exceeded, forcing fallback to safe alternatives.
"""

import time
import collections

# Import metrics
try:
    import sys
    from pathlib import Path
    github_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(github_root))
    from src.metrics.breaker_metrics import BREAKER_OPEN, BREAKER_TRIPS_TOTAL
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    print("⚠️  Breaker metrics not available")

class CircuitBreaker:
    """Simple sliding-window breaker per model."""
    
    def __init__(self, model: str, env: str = "local", build: str = "dev",
                 window_sec: int = 300, min_requests: int = 50,
                 fail_ratio_threshold: float = 0.15, open_secs: int = 300):
        self.model = model
        self.env = env
        self.build = build
        self.window_sec = window_sec
        self.min_requests = min_requests
        self.fail_ratio_threshold = fail_ratio_threshold
        self.open_secs = open_secs
        self.events = collections.deque()  # (ts, success:bool)
        self.state_open_until = 0

    def _gc(self, now: float):
        """Garbage collect events outside the window"""
        cutoff = now - self.window_sec
        while self.events and self.events[0][0] < cutoff:
            self.events.popleft()

    def record(self, success: bool):
        """Record outcome and maybe trip breaker"""
        now = time.time()
        self._gc(now)
        self.events.append((now, success))
        self._maybe_trip(now)

    def _maybe_trip(self, now: float):
        """Check if breaker should trip"""
        n = len(self.events)
        if n < self.min_requests:
            return
        
        fails = sum(1 for _, ok in self.events if not ok)
        fail_ratio = fails / max(1, n)
        
        if fail_ratio >= self.fail_ratio_threshold and now >= self.state_open_until:
            # Trip the breaker
            self.state_open_until = now + self.open_secs
            
            if METRICS_AVAILABLE:
                BREAKER_OPEN.labels(self.model, self.env, self.build).set(1)
                BREAKER_TRIPS_TOTAL.labels(self.model, "high_fail", self.env, self.build).inc()
            
            print(f"🔴 Breaker OPEN for {self.model}: {fail_ratio*100:.1f}% failures ({fails}/{n}) - open for {self.open_secs}s")

    def allow(self) -> bool:
        """Check if requests are allowed (breaker closed)"""
        now = time.time()
        
        if now < self.state_open_until:
            # Still open
            if METRICS_AVAILABLE:
                duration = self.state_open_until - now
                # Update duration gauge (not implemented in metrics yet, but good to have)
            return False
        
        # Breaker can close
        if METRICS_AVAILABLE:
            current = BREAKER_OPEN.labels(self.model, self.env, self.build)._value.get()
            if current != 0:
                BREAKER_OPEN.labels(self.model, self.env, self.build).set(0)
                print(f"🟢 Breaker CLOSED for {self.model}")
        
        return True
    
    def get_state(self) -> dict:
        """Get current breaker state for debugging"""
        now = time.time()
        self._gc(now)
        
        is_open = now < self.state_open_until
        n = len(self.events)
        fails = sum(1 for _, ok in self.events if not ok)
        
        return {
            "model": self.model,
            "is_open": is_open,
            "events_in_window": n,
            "failures": fails,
            "fail_ratio": fails / max(1, n),
            "opens_in": max(0, self.state_open_until - now) if is_open else 0
        }
