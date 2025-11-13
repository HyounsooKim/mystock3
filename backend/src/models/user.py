"""User model for MyStock application."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """Base user model with common fields."""
    
    email: EmailStr


class UserCreate(BaseModel):
    """Model for user creation."""
    
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class User(UserBase):
    """User model with all fields."""
    
    user_id: str
    hashed_password: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    dark_mode: bool = False
    language: str = "ko"
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "user_123abc",
                "email": "user@example.com",
                "hashed_password": "$2b$12$...",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "is_active": True,
                "dark_mode": False,
                "language": "ko"
            }
        }
    }


class UserResponse(UserBase):
    """User model for API responses (no password)."""
    
    user_id: str
    created_at: datetime
    is_active: bool = True
    dark_mode: bool = False
    language: str = "ko"
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "user_123abc",
                "email": "user@example.com",
                "created_at": "2025-01-01T00:00:00Z",
                "is_active": True,
                "dark_mode": False,
                "language": "ko"
            }
        }
    }


class UserUpdate(BaseModel):
    """Model for user updates."""
    
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    is_active: Optional[bool] = None
    dark_mode: Optional[bool] = None
    language: Optional[str] = Field(None, pattern="^(ko|en)$")
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        """Validate password strength if provided."""
        if v is None:
            return v
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
