"""
OTEL Tracing Integration for Athena Dev Daemon
Propagate traceparent through the entire request chain
"""
import logging
import uuid
from typing import Optional, Dict, Any
from fastapi import Request

logger = logging.getLogger(__name__)

# OTEL headers
TRACEPARENT_HEADER = "traceparent"
TRACESTATE_HEADER = "tracestate"


def ensure_trace(headers: Dict[str, str]) -> str:
    """
    Ensure we have a trace ID, either from incoming headers or generate new
    
    Args:
        headers: Request headers
    
    Returns:
        trace_id: W3C trace ID
    """
    # Check for existing traceparent
    traceparent = headers.get(TRACEPARENT_HEADER) or headers.get(TRACEPARENT_HEADER.lower())
    
    if traceparent:
        # Parse W3C traceparent: version-traceid-parentid-flags
        parts = traceparent.split('-')
        if len(parts) >= 2:
            trace_id = parts[1]
            logger.info(f"Using existing trace_id: {trace_id}")
            return trace_id
    
    # Generate new trace ID
    trace_id = uuid.uuid4().hex[:32]  # 32 hex chars
    logger.info(f"Generated new trace_id: {trace_id}")
    return trace_id


def create_traceparent(trace_id: str, parent_id: Optional[str] = None) -> str:
    """
    Create W3C traceparent header
    
    Format: version-traceid-parentid-flags
    Example: 00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01
    
    Args:
        trace_id: Trace ID (32 hex chars)
        parent_id: Parent span ID (16 hex chars), generated if None
    
    Returns:
        traceparent header value
    """
    version = "00"  # W3C version
    parent_id = parent_id or uuid.uuid4().hex[:16]  # 16 hex chars
    flags = "01"  # Sampled
    
    return f"{version}-{trace_id}-{parent_id}-{flags}"


def inject_trace_headers(trace_id: str, parent_id: Optional[str] = None) -> Dict[str, str]:
    """
    Create headers to inject into downstream requests
    
    Args:
        trace_id: Trace ID
        parent_id: Parent span ID (optional)
    
    Returns:
        Headers dict with traceparent
    """
    return {
        TRACEPARENT_HEADER: create_traceparent(trace_id, parent_id)
    }


class SpanContext:
    """
    Simple span context for dev daemon operations
    """
    
    def __init__(self, trace_id: str, operation: str):
        self.trace_id = trace_id
        self.operation = operation
        self.span_id = uuid.uuid4().hex[:16]
        self.start_time = None
        self.end_time = None
        self.attributes = {}
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        logger.info(f"Span started: {self.operation} (trace={self.trace_id}, span={self.span_id})")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        self.end_time = time.time()
        duration_ms = (self.end_time - self.start_time) * 1000
        
        status = "error" if exc_type else "ok"
        logger.info(
            f"Span ended: {self.operation} "
            f"(trace={self.trace_id}, span={self.span_id}, "
            f"duration={duration_ms:.2f}ms, status={status})"
        )
        
        # TODO: Export to OTEL collector
        # For now, just log it
        if exc_type:
            logger.error(f"Span error: {exc_val}")
    
    def set_attribute(self, key: str, value: Any):
        """Add attribute to span"""
        self.attributes[key] = value
    
    def get_headers_for_downstream(self) -> Dict[str, str]:
        """Get headers to propagate to downstream services"""
        return inject_trace_headers(self.trace_id, self.span_id)


def create_span(trace_id: str, operation: str) -> SpanContext:
    """
    Create a new span context
    
    Usage:
        with create_span(trace_id, "gather_snippets") as span:
            span.set_attribute("snippets_count", 8)
            # do work
    
    Args:
        trace_id: Trace ID
        operation: Operation name
    
    Returns:
        SpanContext
    """
    return SpanContext(trace_id, operation)


# Example integration with httpx
def add_tracing_to_httpx_client(trace_id: str, span_id: str):
    """
    Example: Add tracing headers to httpx client
    
    Usage:
        headers = inject_trace_headers(trace_id, span_id)
        async with httpx.AsyncClient(headers=headers) as client:
            response = await client.post(url, json=data)
    """
    return inject_trace_headers(trace_id, span_id)

