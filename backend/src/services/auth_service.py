"""Authentication service."""
from typing import Optional

from ..models.auth import AuthResponse, LoginRequest, SignupRequest
from ..models.user import User, UserCreate, UserResponse
from ..repositories.user_repository import get_user_repository
from ..utils.jwt import create_access_token
from ..utils.logging import get_logger
from ..utils.security import hash_password, verify_password

logger = get_logger(__name__)


class AuthService:
    """Service for authentication operations."""
    
    def __init__(self, user_repository=None):
        """Initialize auth service.
        
        Args:
            user_repository: Optional user repository instance for dependency injection.
                           If None, creates a default repository.
        """
        self.user_repo = user_repository if user_repository is not None else get_user_repository()
    
    async def signup(self, signup_data: SignupRequest) -> AuthResponse:
        """
        Sign up a new user.
        
        Args:
            signup_data: Signup request data
            
        Returns:
            Authentication response with token and user
            
        Raises:
            ValueError: If user already exists or validation fails
        """
        # Hash password
        hashed_pwd = hash_password(signup_data.password)
        
        # Create user
        user_create = UserCreate(email=signup_data.email, password=signup_data.password)
        user = await self.user_repo.create(user_create, hashed_pwd)
        
        # Generate JWT token
        token_data = {"email": user.email, "user_id": user.user_id}
        access_token = create_access_token(token_data)
        
        # Create response
        user_response = UserResponse(
            user_id=user.user_id,
            email=user.email,
            created_at=user.created_at,
            is_active=user.is_active
        )
        
        logger.info(f"User signed up successfully", extra={"extra_fields": {"user_id": user.user_id, "email": user.email}})
        
        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )
    
    async def login(self, login_data: LoginRequest) -> AuthResponse:
        """
        Log in a user.
        
        Args:
            login_data: Login request data
            
        Returns:
            Authentication response with token and user
            
        Raises:
            ValueError: If credentials are invalid
        """
        # Get user by email
        user = await self.user_repo.get_by_email(login_data.email)
        if not user:
            logger.warning(f"Login failed: user not found", extra={"extra_fields": {"email": login_data.email}})
            raise ValueError("Invalid email or password")
        
        # Check if user is active
        if not user.is_active:
            logger.warning(f"Login failed: user is inactive", extra={"extra_fields": {"user_id": user.user_id, "email": user.email}})
            raise ValueError("Account is inactive")
        
        # Verify password
        if not verify_password(login_data.password, user.hashed_password):
            logger.warning(f"Login failed: invalid password", extra={"extra_fields": {"email": login_data.email}})
            raise ValueError("Invalid email or password")
        
        # Generate JWT token
        token_data = {"email": user.email, "user_id": user.user_id}
        access_token = create_access_token(token_data)
        
        # Create response
        user_response = UserResponse(
            user_id=user.user_id,
            email=user.email,
            created_at=user.created_at,
            is_active=user.is_active
        )
        
        logger.info(f"User logged in successfully", extra={"extra_fields": {"user_id": user.user_id, "email": user.email}})
        
        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User if found, None otherwise
        """
        return await self.user_repo.get_by_id(user_id)


# Singleton instance
_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """Get auth service instance."""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service

