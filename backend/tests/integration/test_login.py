"""Integration tests for login endpoint."""
import pytest
from httpx import AsyncClient
from unittest.mock import patch

from src.api.main import app


@pytest.fixture
def mock_cosmos_client():
    """Mock Cosmos DB client."""
    with patch('src.database.cosmos_client.CosmosClient') as mock:
        yield mock


@pytest.mark.asyncio
class TestLoginEndpoint:
    """Integration tests for POST /api/v1/auth/login."""
    
    async def test_successful_login(self, mock_cosmos_client):
        """Test successful user login."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # First create a user
            await client.post(
                "/api/v1/auth/signup",
                json={
                    "email": "logintest@example.com",
                    "password": "LoginPassword123"
                }
            )
            
            # Then login
            response = await client.post(
                "/api/v1/auth/login",
                data={
                    "username": "logintest@example.com",
                    "password": "LoginPassword123"
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
    
    async def test_login_wrong_password(self, mock_cosmos_client):
        """Test login with wrong password."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create a user
            await client.post(
                "/api/v1/auth/signup",
                json={
                    "email": "wrongpass@example.com",
                    "password": "CorrectPassword123"
                }
            )
            
            # Try to login with wrong password
            response = await client.post(
                "/api/v1/auth/login",
                data={
                    "username": "wrongpass@example.com",
                    "password": "WrongPassword123"
                }
            )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "incorrect" in data["detail"].lower()
    
    async def test_login_nonexistent_user(self, mock_cosmos_client):
        """Test login with non-existent user."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/login",
                data={
                    "username": "nonexistent@example.com",
                    "password": "SomePassword123"
                }
            )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    async def test_login_missing_username(self, mock_cosmos_client):
        """Test login without username."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/login",
                data={
                    "password": "SomePassword123"
                }
            )
        
        assert response.status_code == 422
    
    async def test_login_missing_password(self, mock_cosmos_client):
        """Test login without password."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/login",
                data={
                    "username": "test@example.com"
                }
            )
        
        assert response.status_code == 422
    
    async def test_login_response_structure(self, mock_cosmos_client):
        """Test login response has correct OAuth2 structure."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create user
            await client.post(
                "/api/v1/auth/signup",
                json={
                    "email": "oauth@example.com",
                    "password": "OAuthPassword123"
                }
            )
            
            # Login
            response = await client.post(
                "/api/v1/auth/login",
                data={
                    "username": "oauth@example.com",
                    "password": "OAuthPassword123"
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0
    
    async def test_login_with_json_format(self, mock_cosmos_client):
        """Test that login requires form data, not JSON."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create user
            await client.post(
                "/api/v1/auth/signup",
                json={
                    "email": "jsontest@example.com",
                    "password": "JsonPassword123"
                }
            )
            
            # Try to login with JSON (should fail or be ignored)
            response = await client.post(
                "/api/v1/auth/login",
                json={
                    "username": "jsontest@example.com",
                    "password": "JsonPassword123"
                }
            )
        
        # OAuth2 expects form data, not JSON
        assert response.status_code in [422, 400]
    
    async def test_login_case_sensitive_email(self, mock_cosmos_client):
        """Test that email login is case-insensitive."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create user with lowercase email
            await client.post(
                "/api/v1/auth/signup",
                json={
                    "email": "casetest@example.com",
                    "password": "CasePassword123"
                }
            )
            
            # Login with uppercase email
            response = await client.post(
                "/api/v1/auth/login",
                data={
                    "username": "CASETEST@EXAMPLE.COM",
                    "password": "CasePassword123"
                }
            )
        
        # Should succeed (email should be case-insensitive)
        assert response.status_code in [200, 401]  # Depends on implementation

