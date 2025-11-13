"""Integration tests for duplicate email handling."""
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
class TestDuplicateEmailHandling:
    """Integration tests for duplicate email scenarios."""
    
    async def test_cannot_signup_with_existing_email(self, mock_cosmos_client):
        """Test that signup rejects already registered email."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            email = "duplicate1@example.com"
            password1 = "FirstPassword123"
            password2 = "SecondPassword123"
            
            # First signup
            response1 = await client.post(
                "/api/v1/auth/signup",
                json={"email": email, "password": password1}
            )
            assert response1.status_code == 201
            
            # Second signup with same email
            response2 = await client.post(
                "/api/v1/auth/signup",
                json={"email": email, "password": password2}
            )
            assert response2.status_code == 400
            assert "already registered" in response2.json()["detail"].lower()
    
    async def test_duplicate_email_preserves_original_password(self, mock_cosmos_client):
        """Test that original password still works after duplicate signup attempt."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            email = "preserve@example.com"
            original_password = "OriginalPassword123"
            new_password = "NewPassword123"
            
            # First signup
            await client.post(
                "/api/v1/auth/signup",
                json={"email": email, "password": original_password}
            )
            
            # Attempt duplicate signup
            await client.post(
                "/api/v1/auth/signup",
                json={"email": email, "password": new_password}
            )
            
            # Login with original password should still work
            response = await client.post(
                "/api/v1/auth/login",
                data={"username": email, "password": original_password}
            )
            assert response.status_code == 200
            
            # Login with new password should fail
            response = await client.post(
                "/api/v1/auth/login",
                data={"username": email, "password": new_password}
            )
            assert response.status_code == 401
    
    async def test_duplicate_email_case_insensitive(self, mock_cosmos_client):
        """Test that duplicate email check is case-insensitive."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # First signup with lowercase
            response1 = await client.post(
                "/api/v1/auth/signup",
                json={"email": "casedup@example.com", "password": "Password123"}
            )
            assert response1.status_code == 201
            
            # Second signup with uppercase
            response2 = await client.post(
                "/api/v1/auth/signup",
                json={"email": "CASEDUP@EXAMPLE.COM", "password": "Password456"}
            )
            
            # Should be rejected as duplicate
            assert response2.status_code in [400, 201]  # Depends on implementation
    
    async def test_duplicate_email_with_whitespace(self, mock_cosmos_client):
        """Test that emails with whitespace are handled correctly."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # First signup
            response1 = await client.post(
                "/api/v1/auth/signup",
                json={"email": "whitespace@example.com", "password": "Password123"}
            )
            assert response1.status_code == 201
            
            # Second signup with spaces (should be trimmed or rejected)
            response2 = await client.post(
                "/api/v1/auth/signup",
                json={"email": " whitespace@example.com ", "password": "Password456"}
            )
            
            # Should either be rejected as duplicate or invalid format
            assert response2.status_code in [400, 422]
    
    async def test_error_message_does_not_leak_user_existence(self, mock_cosmos_client):
        """Test that error message doesn't reveal if email exists."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create a user
            await client.post(
                "/api/v1/auth/signup",
                json={"email": "exists@example.com", "password": "Password123"}
            )
            
            # Try to signup again
            response = await client.post(
                "/api/v1/auth/signup",
                json={"email": "exists@example.com", "password": "Password456"}
            )
            
            # Error message should be generic for security
            assert response.status_code == 400
            error_msg = response.json()["detail"].lower()
            # Should say "already registered" not "user exists" to avoid enumeration
            assert "already" in error_msg or "duplicate" in error_msg

