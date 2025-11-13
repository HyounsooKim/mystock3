"""Unit tests for JWT utilities."""
import pytest
from datetime import datetime, timedelta
from jose import jwt, JWTError

from src.utils.jwt import create_access_token, verify_token
from src.config import settings


class TestCreateAccessToken:
    """Tests for create_access_token function."""
    
    def test_create_token_with_user_id(self):
        """Test creating token with user_id."""
        user_id = "user_123"
        token = create_access_token({"sub": user_id})
        
        assert token is not None
        assert isinstance(token, str)
        
        # Decode to verify contents
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert payload["sub"] == user_id
        assert "exp" in payload
    
    def test_token_expiration(self):
        """Test token has correct expiration."""
        user_id = "user_123"
        token = create_access_token({"sub": user_id})
        
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        exp_timestamp = payload["exp"]
        exp_datetime = datetime.utcfromtimestamp(exp_timestamp)
        
        # Should expire in ~7 days (allow 1 minute tolerance)
        expected_exp = datetime.utcnow() + timedelta(days=7)
        time_diff = abs((exp_datetime - expected_exp).total_seconds())
        assert time_diff < 60, "Token expiration should be approximately 7 days"
    
    def test_create_token_with_custom_expiration(self):
        """Test creating token with custom expiration."""
        user_id = "user_123"
        custom_delta = timedelta(hours=1)
        token = create_access_token({"sub": user_id}, expires_delta=custom_delta)
        
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        exp_timestamp = payload["exp"]
        exp_datetime = datetime.utcfromtimestamp(exp_timestamp)
        
        expected_exp = datetime.utcnow() + custom_delta
        time_diff = abs((exp_datetime - expected_exp).total_seconds())
        assert time_diff < 5, "Custom expiration should be respected"


class TestVerifyToken:
    """Tests for verify_token function."""
    
    def test_verify_valid_token(self):
        """Test verifying a valid token."""
        user_id = "user_123"
        token = create_access_token({"sub": user_id})
        
        decoded_user_id = verify_token(token)
        assert decoded_user_id == user_id
    
    def test_verify_invalid_token(self):
        """Test verifying an invalid token."""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(JWTError):
            verify_token(invalid_token)
    
    def test_verify_expired_token(self):
        """Test verifying an expired token."""
        user_id = "user_123"
        # Create token that expires immediately
        token = create_access_token({"sub": user_id}, expires_delta=timedelta(seconds=-1))
        
        with pytest.raises(JWTError):
            verify_token(token)
    
    def test_verify_token_wrong_secret(self):
        """Test verifying token with wrong secret."""
        user_id = "user_123"
        # Create token with different secret
        wrong_token = jwt.encode(
            {"sub": user_id, "exp": datetime.utcnow() + timedelta(days=1)},
            "wrong_secret_key",
            algorithm=settings.algorithm
        )
        
        with pytest.raises(JWTError):
            verify_token(wrong_token)
    
    def test_verify_token_missing_sub(self):
        """Test verifying token without 'sub' claim."""
        # Create token without sub claim
        token = jwt.encode(
            {"exp": datetime.utcnow() + timedelta(days=1)},
            settings.secret_key,
            algorithm=settings.algorithm
        )
        
        with pytest.raises(JWTError):
            verify_token(token)
