"""
FastAPI application factory and main entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from azure.cosmos.exceptions import CosmosHttpResponseError

from ..config import settings
from ..utils.logging import get_logger, setup_logging
from ..utils.telemetry import configure_logging_with_insights, get_telemetry_client
from ..database.cosmos_client import close_cosmos_client
from .middleware.metrics import get_metrics_middleware
from .middleware.rate_limit import get_rate_limit_middleware
from .exception_handlers import (
    cosmos_exception_handler,
    validation_exception_handler,
    general_exception_handler,
)

# Setup logging
setup_logging()
configure_logging_with_insights()  # Configure Application Insights
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(
        "Starting MyStock application",
        extra={"extra_fields": {"environment": settings.app_env}}
    )
    
    # Track startup event
    telemetry = get_telemetry_client()
    telemetry.track_event("ApplicationStartup", {"environment": settings.app_env})
    
    yield
    
    # Shutdown
    logger.info("Shutting down MyStock application")
    telemetry.track_event("ApplicationShutdown")
    await close_cosmos_client()


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description="Stock portfolio management application",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    
    # Add rate limiting middleware (should be early in chain)
    rate_limit_middleware = get_rate_limit_middleware()
    app.add_middleware(rate_limit_middleware)
    
    # Add metrics middleware (before CORS for accurate timing)
    metrics_middleware = get_metrics_middleware()
    app.add_middleware(metrics_middleware)
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register exception handlers
    app.add_exception_handler(CosmosHttpResponseError, cosmos_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    # Register routers
    from .routes.auth import router as auth_router
    from .routers.stocks import router as stocks_router
    from .routers.watchlist import router as watchlist_router
    from .routes.portfolio import router as portfolio_router
    
    app.include_router(auth_router, prefix=f"{settings.api_v1_prefix}")
    app.include_router(stocks_router, prefix=f"{settings.api_v1_prefix}")
    app.include_router(watchlist_router, prefix=f"{settings.api_v1_prefix}")
    app.include_router(portfolio_router, prefix=f"{settings.api_v1_prefix}")
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "environment": settings.app_env,
            "version": "1.0.0"
        }
    
    logger.info("FastAPI application created successfully")
    return app


# Application instance
app = create_app()
