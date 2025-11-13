"""Authentication dependencies for FastAPI."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

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
        credentials: HTTP Bearer credentials containing JWT token
        
    Returns:
        Dictionary containing user information (user_id, email)
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    
    try:
        payload = decode_access_token(token)
        
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Extract user information from token
        user_id: str = payload.get("user_id")
        email: str = payload.get("email")
        
        if user_id is None or email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return {"user_id": user_id, "email": email}
        
    except JWTError as e:
        logger.warning(
            "Token validation failed",
            extra={"extra_fields": {"error": str(e)}}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(
            "Unexpected error in token validation",
            extra={"extra_fields": {"error": str(e)}}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication error",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Get current active user.
    
    This is an additional dependency that can be used to check
    if the user is active before allowing access to protected routes.
    
    Args:
        current_user: Current user from get_current_user dependency
        
    Returns:
        Current user dictionary
        
    Raises:
        HTTPException: If user is not active
    """
    # Note: In this implementation, we're assuming the user is active
    # if they have a valid token. In a real application, you might
    # want to fetch the user from the database and check is_active flag.
    return current_user
