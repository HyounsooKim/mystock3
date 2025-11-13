"""
Metrics middleware for tracking API request performance.
Records request latency, status codes, and endpoint usage.
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ...utils.telemetry import get_telemetry_client

logger = logging.getLogger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track API performance metrics.
    Records request duration, status codes, and endpoint usage.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.telemetry = get_telemetry_client()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and track metrics.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
        
        Returns:
            HTTP response
        """
        # Record start time
        start_time = time.time()
        
        # Extract request info
        method = request.method
        path = request.url.path
        endpoint = self._get_endpoint_name(path)
        
        # Process request
        response = None
        status_code = 500
        error = None
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as e:
            error = e
            logger.error(f"Request failed: {method} {path}", exc_info=e)
            raise
        finally:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Track metrics
            self._track_request_metrics(
                method=method,
                endpoint=endpoint,
                status_code=status_code,
                duration_ms=duration_ms,
                success=(200 <= status_code < 400),
                error=error
            )
    
    def _get_endpoint_name(self, path: str) -> str:
        """
        Extract endpoint name from path for grouping metrics.
        Removes dynamic path parameters for aggregation.
        
        Args:
            path: Request path
        
        Returns:
            Normalized endpoint name
        """
        # Remove API version prefix
        if path.startswith("/api/v1"):
            path = path[7:]
        
        # Normalize common patterns
        parts = path.split("/")
        normalized = []
        
        for part in parts:
            if not part:
                continue
            # Replace UUIDs, IDs, symbols with placeholders
            if len(part) == 36 and "-" in part:  # UUID
                normalized.append("{id}")
            elif part.isdigit():  # Numeric ID
                normalized.append("{id}")
            elif part.isupper() and len(part) <= 5:  # Stock symbol
                normalized.append("{symbol}")
            else:
                normalized.append(part)
        
        return "/" + "/".join(normalized) if normalized else "/unknown"
    
    def _track_request_metrics(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration_ms: float,
        success: bool,
        error: Exception = None
    ):
        """
        Track request metrics to Application Insights.
        
        Args:
            method: HTTP method
            endpoint: Normalized endpoint name
            status_code: HTTP status code
            duration_ms: Request duration in milliseconds
            success: Whether request succeeded
            error: Exception if request failed
        """
        properties = {
            "method": method,
            "endpoint": endpoint,
            "status_code": status_code,
            "success": success
        }
        
        # Track latency metric
        self.telemetry.track_metric(
            "ApiRequest.Duration",
            duration_ms,
            properties
        )
        
        # Track request count (value=1 for counting)
        self.telemetry.track_metric(
            "ApiRequest.Count",
            1.0,
            properties
        )
        
        # Track error rate
        if not success:
            self.telemetry.track_metric(
                "ApiRequest.ErrorCount",
                1.0,
                properties
            )
        
        # Track exception details if present
        if error:
            self.telemetry.track_exception(error, properties)
        
        # Log high latency requests
        if duration_ms > 1000:  # >1 second
            logger.warning(
                f"Slow request: {method} {endpoint} took {duration_ms:.2f}ms",
                extra={"custom_dimensions": properties}
            )


def get_metrics_middleware() -> MetricsMiddleware:
    """
    Factory function to create metrics middleware instance.
    
    Returns:
        MetricsMiddleware instance
    """
    return MetricsMiddleware
