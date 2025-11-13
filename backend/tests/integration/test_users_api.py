"""Integration tests for users API endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_current_user(async_client: AsyncClient, auth_headers: dict):
    """Test GET /api/v1/auth/me endpoint."""
    response = await async_client.get("/api/v1/auth/me", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert "email" in data
    assert "dark_mode" in data
    assert "language" in data
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_get_current_user_unauthorized(async_client: AsyncClient):
    """Test GET /api/v1/auth/me without authentication."""
    response = await async_client.get("/api/v1/auth/me")
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_user_preferences_dark_mode(async_client: AsyncClient, auth_headers: dict):
    """Test updating dark mode preference."""
    # Update dark mode to true
    response = await async_client.patch(
        "/api/v1/auth/me",
        json={"dark_mode": True},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["dark_mode"] is True
    
    # Verify the change persisted
    response = await async_client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["dark_mode"] is True
    
    # Update back to false
    response = await async_client.patch(
        "/api/v1/auth/me",
        json={"dark_mode": False},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["dark_mode"] is False


@pytest.mark.asyncio
async def test_update_user_preferences_language(async_client: AsyncClient, auth_headers: dict):
    """Test updating language preference."""
    # Update language to English
    response = await async_client.patch(
        "/api/v1/auth/me",
        json={"language": "en"},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "en"
    
    # Verify the change persisted
    response = await async_client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "en"
    
    # Update back to Korean
    response = await async_client.patch(
        "/api/v1/auth/me",
        json={"language": "ko"},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "ko"


@pytest.mark.asyncio
async def test_update_user_preferences_invalid_language(async_client: AsyncClient, auth_headers: dict):
    """Test updating with invalid language value."""
    response = await async_client.patch(
        "/api/v1/auth/me",
        json={"language": "fr"},  # Only "ko" and "en" are valid
        headers=auth_headers
    )
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_update_user_preferences_multiple_fields(async_client: AsyncClient, auth_headers: dict):
    """Test updating multiple preferences at once."""
    response = await async_client.patch(
        "/api/v1/auth/me",
        json={
            "dark_mode": True,
            "language": "en"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["dark_mode"] is True
    assert data["language"] == "en"


@pytest.mark.asyncio
async def test_update_user_preferences_unauthorized(async_client: AsyncClient):
    """Test PATCH /api/v1/auth/me without authentication."""
    response = await async_client.patch(
        "/api/v1/auth/me",
        json={"dark_mode": True}
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_user_email(async_client: AsyncClient, auth_headers: dict):
    """Test updating user email."""
    new_email = "newemail@example.com"
    
    response = await async_client.patch(
        "/api/v1/auth/me",
        json={"email": new_email},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == new_email


@pytest.mark.asyncio
async def test_update_user_password(async_client: AsyncClient, auth_headers: dict, test_user: dict):
    """Test updating user password."""
    new_password = "NewPassword123"
    
    # Update password
    response = await async_client.patch(
        "/api/v1/auth/me",
        json={"password": new_password},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    
    # Try to login with new password
    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user["email"],
            "password": new_password
        }
    )
    
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_update_user_password_invalid(async_client: AsyncClient, auth_headers: dict):
    """Test updating with invalid password (missing requirements)."""
    # Password without uppercase
    response = await async_client.patch(
        "/api/v1/auth/me",
        json={"password": "weakpass123"},
        headers=auth_headers
    )
    
    assert response.status_code == 422  # Validation error
    
    # Password without digit
    response = await async_client.patch(
        "/api/v1/auth/me",
        json={"password": "WeakPassword"},
        headers=auth_headers
    )
    
    assert response.status_code == 422  # Validation error
    
    # Password too short
    response = await async_client.patch(
        "/api/v1/auth/me",
        json={"password": "Weak1"},
        headers=auth_headers
    )
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_update_user_preferences_empty_body(async_client: AsyncClient, auth_headers: dict):
    """Test PATCH with empty body (should succeed as all fields are optional)."""
    response = await async_client.patch(
        "/api/v1/auth/me",
        json={},
        headers=auth_headers
    )
    
    assert response.status_code == 200
