"""Authentication API routes."""
from fastapi import APIRouter, Depends, HTTPException, status

from ...models.auth import AuthResponse, LoginRequest, SignupRequest
from ...models.user import UserResponse, UserUpdate
from ...services.auth_service import get_auth_service
from ...repositories.user_repository import get_user_repository
from ...utils.logging import get_logger
from ..dependencies.auth import get_current_user

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(signup_data: SignupRequest):
    """
    Sign up a new user.
    
    - **email**: Valid email address
    - **password**: Password (min 8 chars, must contain uppercase, lowercase, and digit)
    
    Returns authentication token and user information.
    """
    try:
        auth_service = get_auth_service()
        result = await auth_service.signup(signup_data)
        return result
    except ValueError as e:
        logger.warning(f"Signup failed", extra={"extra_fields": {"error": str(e), "email": signup_data.email}})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Signup error", extra={"extra_fields": {"error": str(e), "email": signup_data.email}})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during signup"
        )


@router.post("/login", response_model=AuthResponse)
async def login(login_data: LoginRequest):
    """
    Log in a user.
    
    - **email**: User's email address
    - **password**: User's password
    
    Returns authentication token and user information.
    """
    try:
        auth_service = get_auth_service()
        result = await auth_service.login(login_data)
        return result
    except ValueError as e:
        logger.warning(f"Login failed", extra={"extra_fields": {"error": str(e), "email": login_data.email}})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        logger.error(f"Login error", extra={"extra_fields": {"error": str(e), "email": login_data.email}})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login"
        )


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Log out a user.
    
    Note: With JWT tokens, logout is handled client-side by removing the token.
    This endpoint validates the token and can be used for logging purposes.
    """
    logger.info(f"User logged out", extra={"extra_fields": {"user_id": current_user["user_id"], "email": current_user["email"]}})
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current user information.
    
    Requires valid authentication token in Authorization header.
    """
    auth_service = get_auth_service()
    user = await auth_service.get_user_by_id(current_user["user_id"])
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return UserResponse(
        user_id=user.user_id,
        email=user.email,
        created_at=user.created_at,
        is_active=user.is_active,
        dark_mode=user.dark_mode,
        language=user.language
    )


@router.patch("/me", response_model=UserResponse)
async def update_user_preferences(
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update current user preferences.
    
    - **dark_mode**: Enable/disable dark mode (optional)
    - **language**: User interface language - "ko" or "en" (optional)
    - **email**: Update email address (optional)
    - **password**: Update password (optional)
    
    Requires valid authentication token in Authorization header.
    """
    try:
        user_repo = get_user_repository()
        
        # Handle password update if provided
        hashed_password = None
        if user_update.password:
            from ...utils.security import hash_password
            hashed_password = hash_password(user_update.password)
        
        # Update user
        updated_user = await user_repo.update(
            current_user["user_id"],
            user_update,
            hashed_password
        )
        
        if not updated_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        logger.info(
            f"User preferences updated",
            extra={"extra_fields": {
                "user_id": current_user["user_id"],
                "dark_mode": user_update.dark_mode,
                "language": user_update.language
            }}
        )
        
        return UserResponse(
            user_id=updated_user.user_id,
            email=updated_user.email,
            created_at=updated_user.created_at,
            is_active=updated_user.is_active,
            dark_mode=updated_user.dark_mode,
            language=updated_user.language
        )
    except ValueError as e:
        logger.warning(
            f"User preferences update failed",
            extra={"extra_fields": {"error": str(e), "user_id": current_user["user_id"]}}
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            f"User preferences update error",
            extra={"extra_fields": {"error": str(e), "user_id": current_user["user_id"]}}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating preferences"
        )
