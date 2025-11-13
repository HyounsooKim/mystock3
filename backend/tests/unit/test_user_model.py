"""Unit tests for User model."""
import pytest
from pydantic import ValidationError

from src.models.user import User, UserCreate, UserResponse, UserUpdate


class TestUserCreate:
    """Tests for UserCreate model."""
    
    def test_valid_user_creation(self):
        """Test creating user with valid data."""
        user_data = UserCreate(
            email="test@example.com",
            password="TestPassword123"
        )
        assert user_data.email == "test@example.com"
        assert user_data.password == "TestPassword123"
    
    def test_invalid_email(self):
        """Test validation fails with invalid email."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(email="invalid-email", password="TestPassword123")
        assert "email" in str(exc_info.value)
    
    def test_password_too_short(self):
        """Test validation fails with password less than 8 characters."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(email="test@example.com", password="Test1")
        assert "password" in str(exc_info.value).lower()
    
    def test_password_no_uppercase(self):
        """Test validation fails without uppercase letter."""
        with pytest.raises(ValueError) as exc_info:
            UserCreate(email="test@example.com", password="testpass123")
        assert "uppercase" in str(exc_info.value).lower()
    
    def test_password_no_lowercase(self):
        """Test validation fails without lowercase letter."""
        with pytest.raises(ValueError) as exc_info:
            UserCreate(email="test@example.com", password="TESTPASS123")
        assert "lowercase" in str(exc_info.value).lower()
    
    def test_password_no_digit(self):
        """Test validation fails without digit."""
        with pytest.raises(ValueError) as exc_info:
            UserCreate(email="test@example.com", password="TestPassword")
        assert "digit" in str(exc_info.value).lower()


class TestUser:
    """Tests for User model."""
    
    def test_user_model_creation(self):
        """Test creating full User model."""
        from datetime import datetime
        
        user = User(
            user_id="user_123",
            email="test@example.com",
            hashed_password="$2b$12$...",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_active=True
        )
        assert user.user_id == "user_123"
        assert user.email == "test@example.com"
        assert user.is_active is True


class TestUserResponse:
    """Tests for UserResponse model."""
    
    def test_user_response_excludes_password(self):
        """Test UserResponse doesn't include password fields."""
        from datetime import datetime
        
        user_response = UserResponse(
            user_id="user_123",
            email="test@example.com",
            created_at=datetime.utcnow(),
            is_active=True
        )
        
        # Verify password-related fields don't exist
        assert not hasattr(user_response, 'password')
        assert not hasattr(user_response, 'hashed_password')


class TestUserUpdate:
    """Tests for UserUpdate model."""
    
    def test_update_with_all_fields(self):
        """Test updating all fields."""
        update_data = UserUpdate(
            email="newemail@example.com",
            password="NewPassword123",
            is_active=False
        )
        assert update_data.email == "newemail@example.com"
        assert update_data.password == "NewPassword123"
        assert update_data.is_active is False
    
    def test_update_with_partial_fields(self):
        """Test updating only some fields."""
        update_data = UserUpdate(email="newemail@example.com")
        assert update_data.email == "newemail@example.com"
        assert update_data.password is None
        assert update_data.is_active is None
    
    def test_update_password_validation(self):
        """Test password validation in update."""
        with pytest.raises((ValueError, ValidationError)) as exc_info:
            UserUpdate(password="short")
        # Password validation should fail (either too short or missing requirements)
        assert "password" in str(exc_info.value).lower() or "8 characters" in str(exc_info.value).lower()
