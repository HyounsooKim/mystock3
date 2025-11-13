"""
Azure Application Insights telemetry integration.
Provides centralized telemetry tracking for monitoring and observability.
"""

import logging
import os
from typing import Optional, Dict, Any
from functools import wraps
import time

# Application Insights SDK (optional dependency)
try:
    from opencensus.ext.azure.log_exporter import AzureLogHandler
    from opencensus.ext.azure.trace_exporter import AzureExporter
    from opencensus.trace.samplers import ProbabilitySampler
    from opencensus.trace.tracer import Tracer
    from opencensus.trace import execution_context
    INSIGHTS_AVAILABLE = True
except ImportError:
    INSIGHTS_AVAILABLE = False
    AzureLogHandler = None
    AzureExporter = None
    Tracer = None

logger = logging.getLogger(__name__)


class TelemetryClient:
    """
    Centralized telemetry client for Application Insights.
    Handles custom events, metrics, and distributed tracing.
    """
    
    def __init__(self):
        self.connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
        self.enabled = INSIGHTS_AVAILABLE and bool(self.connection_string)
        self.tracer: Optional[Tracer] = None
        
        if self.enabled:
            self._initialize_tracer()
            logger.info("Application Insights telemetry enabled")
        else:
            if not INSIGHTS_AVAILABLE:
                logger.warning(
                    "Application Insights SDK not installed. "
                    "Install with: pip install opencensus-ext-azure"
                )
            elif not self.connection_string:
                logger.warning(
                    "APPLICATIONINSIGHTS_CONNECTION_STRING not configured. "
                    "Telemetry disabled."
                )
    
    def _initialize_tracer(self):
        """Initialize OpenCensus tracer with Azure exporter."""
        if not self.enabled:
            return
        
        try:
            exporter = AzureExporter(connection_string=self.connection_string)
            sampler = ProbabilitySampler(rate=1.0)  # 100% sampling
            self.tracer = Tracer(exporter=exporter, sampler=sampler)
        except Exception as e:
            logger.error(f"Failed to initialize Application Insights tracer: {e}")
            self.enabled = False
    
    def track_event(self, name: str, properties: Optional[Dict[str, Any]] = None):
        """
        Track a custom event.
        
        Args:
            name: Event name (e.g., "StockQuoteFetched", "WatchlistCreated")
            properties: Custom properties dictionary
        """
        if not self.enabled:
            return
        
        try:
            # Log event for Application Insights
            logger.info(
                f"Custom Event: {name}",
                extra={
                    "custom_dimensions": properties or {},
                    "event_name": name
                }
            )
        except Exception as e:
            logger.error(f"Failed to track event '{name}': {e}")
    
    def track_metric(self, name: str, value: float, properties: Optional[Dict[str, Any]] = None):
        """
        Track a custom metric.
        
        Args:
            name: Metric name (e.g., "ApiLatency", "CacheHitRate")
            value: Metric value
            properties: Custom properties dictionary
        """
        if not self.enabled:
            return
        
        try:
            logger.info(
                f"Custom Metric: {name} = {value}",
                extra={
                    "custom_dimensions": properties or {},
                    "metric_name": name,
                    "metric_value": value
                }
            )
        except Exception as e:
            logger.error(f"Failed to track metric '{name}': {e}")
    
    def track_exception(self, exception: Exception, properties: Optional[Dict[str, Any]] = None):
        """
        Track an exception.
        
        Args:
            exception: Exception instance
            properties: Custom properties dictionary
        """
        if not self.enabled:
            return
        
        try:
            logger.exception(
                f"Exception tracked: {type(exception).__name__}",
                exc_info=exception,
                extra={"custom_dimensions": properties or {}}
            )
        except Exception as e:
            logger.error(f"Failed to track exception: {e}")
    
    def track_dependency(
        self,
        name: str,
        dependency_type: str,
        data: str,
        duration: float,
        success: bool,
        properties: Optional[Dict[str, Any]] = None
    ):
        """
        Track a dependency call (external API, database, etc.).
        
        Args:
            name: Dependency name (e.g., "AlphaVantageAPI", "CosmosDB")
            dependency_type: Type (e.g., "HTTP", "Database")
            data: Call details (e.g., URL, query)
            duration: Duration in milliseconds
            success: Whether the call succeeded
            properties: Custom properties dictionary
        """
        if not self.enabled:
            return
        
        try:
            logger.info(
                f"Dependency: {name} ({dependency_type}) - {duration:.2f}ms - {'Success' if success else 'Failed'}",
                extra={
                    "custom_dimensions": {
                        **(properties or {}),
                        "dependency_name": name,
                        "dependency_type": dependency_type,
                        "dependency_data": data,
                        "duration_ms": duration,
                        "success": success
                    }
                }
            )
        except Exception as e:
            logger.error(f"Failed to track dependency '{name}': {e}")
    
    def start_span(self, name: str):
        """
        Start a distributed trace span.
        
        Args:
            name: Span name
        
        Returns:
            Span context manager (use with 'with' statement)
        """
        if not self.enabled or not self.tracer:
            return _NoOpSpan()
        
        try:
            return self.tracer.span(name=name)
        except Exception as e:
            logger.error(f"Failed to start span '{name}': {e}")
            return _NoOpSpan()


class _NoOpSpan:
    """No-op span for when telemetry is disabled."""
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass


# Global telemetry client instance
_telemetry_client: Optional[TelemetryClient] = None


def get_telemetry_client() -> TelemetryClient:
    """Get or create the global telemetry client instance."""
    global _telemetry_client
    if _telemetry_client is None:
        _telemetry_client = TelemetryClient()
    return _telemetry_client


def configure_logging_with_insights():
    """
    Configure Python logging to send logs to Application Insights.
    Call this during application startup.
    """
    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    
    if not INSIGHTS_AVAILABLE:
        logger.warning("Application Insights SDK not available")
        return
    
    if not connection_string:
        logger.warning("APPLICATIONINSIGHTS_CONNECTION_STRING not configured")
        return
    
    try:
        # Add Azure Log Handler to root logger
        azure_handler = AzureLogHandler(connection_string=connection_string)
        azure_handler.setLevel(logging.INFO)
        
        root_logger = logging.getLogger()
        root_logger.addHandler(azure_handler)
        
        logger.info("Application Insights logging configured")
    except Exception as e:
        logger.error(f"Failed to configure Application Insights logging: {e}")


def track_performance(operation_name: str):
    """
    Decorator to track function performance metrics.
    
    Usage:
        @track_performance("FetchStockQuote")
        async def get_stock_quote(symbol: str):
            ...
    
    Args:
        operation_name: Name for the tracked operation
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            client = get_telemetry_client()
            start_time = time.time()
            success = False
            error = None
            
            try:
                result = await func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                error = e
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                
                # Track metric
                client.track_metric(
                    f"{operation_name}.Duration",
                    duration_ms,
                    {"success": str(success)}
                )
                
                # Track exception if failed
                if error:
                    client.track_exception(
                        error,
                        {"operation": operation_name}
                    )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            client = get_telemetry_client()
            start_time = time.time()
            success = False
            error = None
            
            try:
                result = func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                error = e
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                
                # Track metric
                client.track_metric(
                    f"{operation_name}.Duration",
                    duration_ms,
                    {"success": str(success)}
                )
                
                # Track exception if failed
                if error:
                    client.track_exception(
                        error,
                        {"operation": operation_name}
                    )
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
