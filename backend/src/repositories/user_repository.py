"""User repository for database operations."""
from datetime import datetime
from typing import Optional
import uuid

from azure.cosmos import exceptions

from ..database.cosmos_client import get_container
from ..models.user import User, UserCreate, UserUpdate
from ..utils.logging import get_logger

logger = get_logger(__name__)


class UserRepository:
    """Repository for user data operations."""
    
    def __init__(self):
        """Initialize user repository."""
        self.container = get_container("users")
    
    async def create(self, user_data: UserCreate, hashed_password: str) -> User:
        """
        Create a new user.
        
        Args:
            user_data: User creation data
            hashed_password: Hashed password
            
        Returns:
            Created user
            
        Raises:
            ValueError: If user with email already exists
        """
        # Check if user already exists
        existing_user = await self.get_by_email(user_data.email)
        if existing_user:
            logger.warning(f"User creation failed: email already exists", extra={"extra_fields": {"email": user_data.email}})
            raise ValueError("User with this email already exists")
        
        # Create user document
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()
        
        user_dict = {
            "id": user_id,
            "user_id": user_id,
            "email": user_data.email,
            "hashed_password": hashed_password,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "is_active": True,
            "dark_mode": False,
            "language": "ko"
        }
        
        try:
            created_item = self.container.create_item(body=user_dict)
            logger.info(f"User created successfully", extra={"extra_fields": {"user_id": user_id, "email": user_data.email}})
            return User(**created_item)
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to create user", extra={"extra_fields": {"error": str(e), "email": user_data.email}})
            raise
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User if found, None otherwise
        """
        try:
            item = self.container.read_item(item=user_id, partition_key=user_id)
            return User(**item)
        except exceptions.CosmosResourceNotFoundError:
            return None
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to get user by ID", extra={"extra_fields": {"error": str(e), "user_id": user_id}})
            raise
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.
        
        Args:
            email: User email
            
        Returns:
            User if found, None otherwise
        """
        query = "SELECT * FROM c WHERE c.email = @email"
        parameters = [{"name": "@email", "value": email}]
        
        try:
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            if items:
                return User(**items[0])
            return None
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to get user by email", extra={"extra_fields": {"error": str(e), "email": email}})
            raise
    
    async def update(self, user_id: str, user_data: UserUpdate, hashed_password: Optional[str] = None) -> Optional[User]:
        """
        Update user.
        
        Args:
            user_id: User ID
            user_data: User update data
            hashed_password: New hashed password (if password is being updated)
            
        Returns:
            Updated user if found, None otherwise
        """
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        # Update fields
        update_dict = user.model_dump()
        if user_data.email is not None:
            update_dict["email"] = user_data.email
        if hashed_password is not None:
            update_dict["hashed_password"] = hashed_password
        if user_data.is_active is not None:
            update_dict["is_active"] = user_data.is_active
        if user_data.dark_mode is not None:
            update_dict["dark_mode"] = user_data.dark_mode
        if user_data.language is not None:
            update_dict["language"] = user_data.language
        update_dict["updated_at"] = datetime.utcnow().isoformat()
        
        try:
            updated_item = self.container.replace_item(item=user_id, body=update_dict)
            logger.info(f"User updated successfully", extra={"extra_fields": {"user_id": user_id}})
            return User(**updated_item)
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to update user", extra={"extra_fields": {"error": str(e), "user_id": user_id}})
            raise
    
    async def delete(self, user_id: str) -> bool:
        """
        Delete user (soft delete by setting is_active to False).
        
        Args:
            user_id: User ID
            
        Returns:
            True if deleted, False if not found
        """
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        update_data = UserUpdate(is_active=False)
        await self.update(user_id, update_data)
        logger.info(f"User soft deleted", extra={"extra_fields": {"user_id": user_id}})
        return True


# Singleton instance
_user_repository: Optional[UserRepository] = None


def get_user_repository() -> UserRepository:
    """Get user repository instance."""
    global _user_repository
    if _user_repository is None:
        _user_repository = UserRepository()
    return _user_repository

