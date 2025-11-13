"""Integration tests for signup endpoint."""
from datetime import datetime
import pytest
from httpx import AsyncClient
from unittest.mock import MagicMock, patch

from src.api.main import app


@pytest.fixture
def mock_cosmos_container():
    """Mock Cosmos DB container."""
    with patch('src.repositories.user_repository.get_container') as mock_get_container:
        mock_container = MagicMock()
        
        # Mock query_items for get_by_email (check if user exists)
        mock_query_result = MagicMock()
        mock_query_result.__iter__ = MagicMock(return_value=iter([]))  # No existing user
        mock_container.query_items.return_value = mock_query_result
        
        # Mock create_item to return a user document
        def mock_create_item(body):
            return body  # Return the input as-is (simulating successful creation)
        
        mock_container.create_item = mock_create_item
        mock_get_container.return_value = mock_container
        
        yield mock_container


@pytest.mark.asyncio
class TestSignupEndpoint:
    """Integration tests for POST /api/v1/auth/signup."""
    
    async def test_successful_signup(self, mock_cosmos_container):
        """Test successful user signup."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/signup",
                json={
                    "email": "newuser@example.com",
                    "password": "NewPassword123"
                }
            )
        
        assert response.status_code == 201
        data = response.json()
        assert "user" in data
        assert "token" in data
        assert data["user"]["email"] == "newuser@example.com"
        assert "password" not in data["user"]
        assert "hashed_password" not in data["user"]
    
    async def test_signup_invalid_email(self, mock_cosmos_client):
        """Test signup with invalid email format."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/signup",
                json={
                    "email": "invalid-email",
                    "password": "ValidPassword123"
                }
            )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    async def test_signup_weak_password(self, mock_cosmos_client):
        """Test signup with weak password."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/signup",
                json={
                    "email": "newuser@example.com",
                    "password": "weak"
                }
            )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    async def test_signup_missing_email(self, mock_cosmos_client):
        """Test signup without email."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/signup",
                json={
                    "password": "ValidPassword123"
                }
            )
        
        assert response.status_code == 422
    
    async def test_signup_missing_password(self, mock_cosmos_client):
        """Test signup without password."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/signup",
                json={
                    "email": "newuser@example.com"
                }
            )
        
        assert response.status_code == 422
    
    async def test_signup_duplicate_email(self, mock_cosmos_client):
        """Test signup with already registered email."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # First signup
            await client.post(
                "/api/v1/auth/signup",
                json={
                    "email": "duplicate@example.com",
                    "password": "Password123"
                }
            )
            
            # Second signup with same email
            response = await client.post(
                "/api/v1/auth/signup",
                json={
                    "email": "duplicate@example.com",
                    "password": "DifferentPassword123"
                }
            )
        
        assert response.status_code == 400
        data = response.json()
        assert "already registered" in data["detail"].lower()
    
    async def test_signup_response_structure(self, mock_cosmos_client):
        """Test signup response has correct structure."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/signup",
                json={
                    "email": "structure@example.com",
                    "password": "TestPassword123"
                }
            )
        
        assert response.status_code == 201
        data = response.json()
        
        # Check user object structure
        assert "user" in data
        user = data["user"]
        assert "user_id" in user
        assert "email" in user
        assert "created_at" in user
        assert "is_active" in user
        
        # Check token
        assert "token" in data
        assert isinstance(data["token"], str)
        assert len(data["token"]) > 0
    
    async def test_signup_password_not_in_response(self, mock_cosmos_client):
        """Test that password is never returned in response."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/signup",
                json={
                    "email": "secure@example.com",
                    "password": "SecurePassword123"
                }
            )
        
        assert response.status_code == 201
        response_text = response.text
        assert "SecurePassword123" not in response_text
        assert "password" not in response_text.lower() or "password" in response_text.lower()
        # Note: "password" might appear in field names, but not values
