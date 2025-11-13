"""
JWT token utilities for authentication.
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from ..config import settings
from ..utils.logging import get_logger

logger = get_logger(__name__)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.
    
    Args:
        data: Data to encode in token
        expires_delta: Token expiration time delta
    
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.access_token_expire_days)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow()
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    
    logger.info(
        "Access token created",
        extra={"extra_fields": {"expires_at": expire.isoformat()}}
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and verify JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        return payload
    except JWTError as e:
        logger.warning(
            "Token decode failed",
            extra={"extra_fields": {"error": str(e)}}
        )
        return None


def verify_token(token: str) -> str:
    """
    Verify JWT token and extract user_id.
    
    Args:
        token: JWT token string
    
    Returns:
        User ID from token
        
    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise JWTError("Token missing 'sub' claim")
        return user_id
    except JWTError as e:
        logger.warning(
            "Token verification failed",
            extra={"extra_fields": {"error": str(e)}}
        )
        raise
