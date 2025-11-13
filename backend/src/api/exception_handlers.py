"""
Global exception handlers for FastAPI application.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from azure.cosmos.exceptions import CosmosHttpResponseError
from ..utils.logging import get_logger
from ..models.errors import ErrorResponse, ValidationErrorResponse

logger = get_logger(__name__)


async def cosmos_exception_handler(
    request: Request, exc: CosmosHttpResponseError
) -> JSONResponse:
    """
    Handle Cosmos DB exceptions.
    
    Args:
        request: FastAPI request
        exc: Cosmos HTTP response error
    
    Returns:
        JSON error response
    """
    logger.error(
        "Cosmos DB error",
        extra={
            "extra_fields": {
                "status_code": exc.status_code,
                "message": exc.message,
                "path": request.url.path,
            }
        },
    )
    
    error_response = ErrorResponse(
        detail="Database error occurred",
        error_code="DATABASE_ERROR",
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(mode='json'),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handle request validation errors.
    
    Args:
        request: FastAPI request
        exc: Request validation error
    
    Returns:
        JSON error response
    """
    logger.warning(
        "Validation error",
        extra={
            "extra_fields": {
                "errors": exc.errors(),
                "path": request.url.path,
            }
        },
    )
    
    error_response = ValidationErrorResponse(
        detail=[
            {
                "loc": err["loc"],
                "msg": err["msg"],
                "type": err["type"],
            }
            for err in exc.errors()
        ]
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump(mode='json'),
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle general unexpected exceptions.
    
    Args:
        request: FastAPI request
        exc: Exception
    
    Returns:
        JSON error response
    """
    logger.exception(
        "Unexpected error",
        extra={
            "extra_fields": {
                "exception_type": type(exc).__name__,
                "path": request.url.path,
            }
        },
    )
    
    error_response = ErrorResponse(
        detail="An unexpected error occurred",
        error_code="INTERNAL_ERROR",
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(mode='json'),
    )
