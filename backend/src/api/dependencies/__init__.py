"""
Authentication dependencies for FastAPI.
Provides get_current_user dependency for protected endpoints.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ...utils.jwt import decode_access_token
from ...utils.logging import get_logger

logger = get_logger(__name__)

# HTTP Bearer token security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer credentials from request
    
    Returns:
        User data from token payload
    
    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    
    payload = decode_access_token(token)
    
    if payload is None:
        logger.warning("Invalid token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_email: Optional[str] = payload.get("sub")
    if user_email is None:
        logger.warning("Token missing subject claim")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info(
        "User authenticated",
        extra={"extra_fields": {"user_email": user_email}}
    )
    
    return {"email": user_email, "user_id": payload.get("user_id")}


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    )
) -> Optional[dict]:
    """
    Get current user if token is provided, otherwise return None.
    For endpoints that optionally require authentication.
    
    Args:
        credentials: Optional HTTP Bearer credentials
    
    Returns:
        User data if token is valid, None otherwise
    """
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
