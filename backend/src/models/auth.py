"""Authentication models for MyStock application."""
from pydantic import BaseModel, EmailStr, Field

from .user import UserResponse


class LoginRequest(BaseModel):
    """Model for login request."""
    
    email: EmailStr
    password: str


class SignupRequest(BaseModel):
    """Model for signup request."""
    
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)


class AuthResponse(BaseModel):
    """Model for authentication response."""
    
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user": {
                    "user_id": "user_123abc",
                    "email": "user@example.com",
                    "created_at": "2025-01-01T00:00:00Z",
                    "is_active": True
                }
            }
        }
    }


class TokenPayload(BaseModel):
    """Model for JWT token payload."""
    
    email: str
    user_id: str
    exp: int
    iat: int
