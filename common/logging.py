# Structured Logging for Loki
# JSON logs that integrate with tracing

import os
import json
import time
from typing import Dict
from opentelemetry import trace


class StructuredLogger:
    """Structured logger that outputs JSON for Loki ingestion."""

    def __init__(self, service: str):
        self.service = service
        self.trace = trace.get_tracer(__name__)

    def _get_trace_context(self) -> Dict[str, str]:
        """Extract trace context for log correlation."""
        current_span = trace.get_current_span()
        if current_span.is_recording():
            span_context = current_span.get_span_context()
            return {
                "trace_id": format(span_context.trace_id, "032x"),
                "span_id": format(span_context.span_id, "016x"),
            }
        return {}

    def _log(self, level: str, message: str, **kwargs):
        """Internal logging method."""
        log_entry = {
            "timestamp": time.time(),
            "service": self.service,
            "level": level.upper(),
            "message": message,
            "pid": os.getpid(),
            **self._get_trace_context(),
            **kwargs
        }

        # Remove None values
        log_entry = {k: v for k, v in log_entry.items() if v is not None}

        # Output JSON to stdout (Promtail will pick it up)
        print(json.dumps(log_entry), flush=True)

    def debug(self, message: str, **kwargs):
        self._log("debug", message, **kwargs)

    def info(self, message: str, **kwargs):
        self._log("info", message, **kwargs)

    def warn(self, message: str, **kwargs):
        self._log("warn", message, **kwargs)

    def error(self, message: str, error: Exception = None, **kwargs):
        if error:
            kwargs["error"] = str(error)
            kwargs["error_type"] = type(error).__name__
        self._log("error", message, **kwargs)

    def fatal(self, message: str, **kwargs):
        self._log("fatal", message, **kwargs)


# Global logger instance
logger = StructuredLogger(os.getenv("SERVICE_NAME", "unknown"))

# Convenience functions
def log(**kwargs):
    """Quick logging function - infers level from context."""
    level = kwargs.pop("level", "info")
    message = kwargs.pop("message", "")
    getattr(logger, level.lower())(message, **kwargs)

def traced_log(name: str, **kwargs):
    """Log within a trace span."""
    with logger.trace.get_tracer(__name__).start_as_current_span(name):
        log(**kwargs)
