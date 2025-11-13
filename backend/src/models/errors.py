"""
Error response models for API.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error response model."""
    
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Application-specific error code")
    timestamp: datetime = Field(default_factory=lambda: datetime.utcnow(), description="Error timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z" if v else None
        }
        json_schema_extra = {
            "example": {
                "detail": "Stock symbol not found",
                "error_code": "STOCK_NOT_FOUND",
                "timestamp": "2025-11-06T10:00:00Z"
            }
        }


class ValidationErrorDetail(BaseModel):
    """Validation error detail."""
    
    loc: list[str | int] = Field(..., description="Error location")
    msg: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")


class ValidationErrorResponse(BaseModel):
    """Validation error response model."""
    
    detail: list[ValidationErrorDetail] = Field(..., description="Validation errors")
    error_code: str = Field(default="VALIDATION_ERROR", description="Error code")
    timestamp: datetime = Field(default_factory=lambda: datetime.utcnow())
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z" if v else None
        }
        json_schema_extra = {
            "example": {
                "detail": [
                    {
                        "loc": ["body", "email"],
                        "msg": "value is not a valid email address",
                        "type": "value_error.email"
                    }
                ],
                "error_code": "VALIDATION_ERROR",
                "timestamp": "2025-11-06T10:00:00Z"
            }
        }
