"""Unit tests for Authentication Service."""
import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.services.auth_service import AuthService
from src.models.auth import SignupRequest, LoginRequest, AuthResponse
from src.models.user import User


@pytest.fixture
def mock_user_repository():
    """Mock UserRepository for testing."""
    return AsyncMock()


@pytest.fixture
def auth_service(mock_user_repository):
    """Create AuthService with mocked repository."""
    return AuthService(mock_user_repository)


@pytest.fixture
def sample_user():
    """Sample user for testing."""
    return User(
        user_id="user_123",
        email="test@example.com",
        hashed_password="$2b$12$hashed_password",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        is_active=True
    )


class TestSignup:
    """Tests for signup method."""
    
    @pytest.mark.asyncio
    async def test_successful_signup(self, auth_service, mock_user_repository):
        """Test successful user signup."""
        mock_user = User(
            user_id="user_new",
            email="newuser@example.com",
            hashed_password="$2b$12$hashed",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_active=True
        )
        
        mock_user_repository.create.return_value = mock_user
        
        signup_request = SignupRequest(
            email="newuser@example.com",
            password="NewPassword123"
        )
        
        result = await auth_service.signup(signup_request)
        
        assert result is not None
        assert isinstance(result, AuthResponse)
        assert result.user.email == signup_request.email
        assert result.access_token is not None
        assert result.token_type == "bearer"
        mock_user_repository.create.assert_called_once()


class TestLogin:
    """Tests for login method."""
    
    @pytest.mark.asyncio
    async def test_successful_login(self, auth_service, mock_user_repository, sample_user):
        """Test successful user login."""
        mock_user_repository.get_by_email.return_value = sample_user
        
        login_request = LoginRequest(
            email=sample_user.email,
            password="TestPassword123"
        )
        
        result = await auth_service.login(login_request)
        
        assert result is not None
        assert isinstance(result, AuthResponse)
        assert result.user.email == sample_user.email
        assert result.access_token is not None
        mock_user_repository.get_by_email.assert_called_once_with(sample_user.email)
    
    @pytest.mark.asyncio
    async def test_login_user_not_found(self, auth_service, mock_user_repository):
        """Test login with non-existent user."""
        mock_user_repository.get_by_email.return_value = None
        
        login_request = LoginRequest(
            email="nonexistent@example.com",
            password="TestPassword123"
        )
        
        with pytest.raises(ValueError) as exc_info:
            await auth_service.login(login_request)
        
        assert "invalid" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_login_inactive_user(self, auth_service, mock_user_repository, sample_user):
        """Test login with inactive user."""
        sample_user.is_active = False
        mock_user_repository.get_by_email.return_value = sample_user
        
        login_request = LoginRequest(
            email=sample_user.email,
            password="TestPassword123"
        )
        
        with pytest.raises(ValueError) as exc_info:
            await auth_service.login(login_request)
        
        assert "inactive" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_login_wrong_password(self, auth_service, mock_user_repository, sample_user):
        """Test login with wrong password."""
        mock_user_repository.get_by_email.return_value = sample_user
        
        login_request = LoginRequest(
            email=sample_user.email,
            password="WrongPassword123"
        )
        
        with pytest.raises(ValueError) as exc_info:
            await auth_service.login(login_request)
        
        assert "invalid" in str(exc_info.value).lower()


class TestGetUserById:
    """Tests for get_user_by_id method."""
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_found(self, auth_service, mock_user_repository, sample_user):
        """Test getting user by ID when user exists."""
        mock_user_repository.get_by_id.return_value = sample_user
        
        result = await auth_service.get_user_by_id(sample_user.user_id)
        
        assert result is not None
        assert result.user_id == sample_user.user_id
        assert result.email == sample_user.email
        mock_user_repository.get_by_id.assert_called_once_with(sample_user.user_id)
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, auth_service, mock_user_repository):
        """Test getting user by ID when user doesn't exist."""
        mock_user_repository.get_by_id.return_value = None
        
        result = await auth_service.get_user_by_id("nonexistent_id")
        
        assert result is None
        mock_user_repository.get_by_id.assert_called_once_with("nonexistent_id")
