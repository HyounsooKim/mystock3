"""
CSRF (Cross-Site Request Forgery) protection utilities.
Provides token generation and validation for state-changing operations.
"""

import secrets
import hmac
import hashlib
import time
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class CSRFProtection:
    """
    CSRF protection using double-submit cookie pattern.
    
    Features:
    - Cryptographically secure token generation
    - HMAC-based token validation
    - Token expiration (default 1 hour)
    - Constant-time comparison to prevent timing attacks
    """
    
    TOKEN_LENGTH = 32  # bytes
    TOKEN_EXPIRY = 3600  # 1 hour in seconds
    
    def __init__(self, secret_key: str):
        """
        Initialize CSRF protection.
        
        Args:
            secret_key: Secret key for HMAC signing
        """
        if not secret_key or len(secret_key) < 32:
            raise ValueError("CSRF secret key must be at least 32 characters")
        
        self.secret_key = secret_key.encode('utf-8')
    
    def generate_token(self, user_id: Optional[str] = None) -> str:
        """
        Generate a new CSRF token.
        
        Args:
            user_id: Optional user identifier to bind token to user
        
        Returns:
            CSRF token string (hex-encoded)
        """
        # Generate random token
        random_bytes = secrets.token_bytes(self.TOKEN_LENGTH)
        
        # Add timestamp
        timestamp = int(time.time())
        
        # Create payload: random_bytes || timestamp || user_id
        payload = random_bytes + str(timestamp).encode('utf-8')
        if user_id:
            payload += user_id.encode('utf-8')
        
        # Sign with HMAC
        signature = hmac.new(
            self.secret_key,
            payload,
            hashlib.sha256
        ).digest()
        
        # Combine: random_bytes || timestamp || signature
        token_bytes = random_bytes + str(timestamp).encode('utf-8') + b':' + signature
        
        # Return hex-encoded token
        return token_bytes.hex()
    
    def validate_token(
        self,
        token: str,
        user_id: Optional[str] = None,
        max_age: Optional[int] = None
    ) -> bool:
        """
        Validate a CSRF token.
        
        Args:
            token: CSRF token to validate
            user_id: User ID that token should be bound to
            max_age: Maximum token age in seconds (default: TOKEN_EXPIRY)
        
        Returns:
            True if token is valid
        """
        if not token:
            logger.warning("Empty CSRF token provided")
            return False
        
        if max_age is None:
            max_age = self.TOKEN_EXPIRY
        
        try:
            # Decode token
            token_bytes = bytes.fromhex(token)
            
            # Split components
            parts = token_bytes.split(b':')
            if len(parts) != 2:
                logger.warning("Invalid CSRF token format")
                return False
            
            payload_with_timestamp, signature = parts
            
            # Extract random bytes and timestamp
            random_bytes = payload_with_timestamp[:self.TOKEN_LENGTH]
            timestamp_str = payload_with_timestamp[self.TOKEN_LENGTH:].decode('utf-8')
            
            try:
                timestamp = int(timestamp_str)
            except ValueError:
                logger.warning("Invalid CSRF token timestamp")
                return False
            
            # Check expiration
            current_time = int(time.time())
            if current_time - timestamp > max_age:
                logger.warning(
                    f"CSRF token expired (age: {current_time - timestamp}s, max: {max_age}s)"
                )
                return False
            
            # Reconstruct payload
            payload = random_bytes + str(timestamp).encode('utf-8')
            if user_id:
                payload += user_id.encode('utf-8')
            
            # Compute expected signature
            expected_signature = hmac.new(
                self.secret_key,
                payload,
                hashlib.sha256
            ).digest()
            
            # Constant-time comparison
            if not hmac.compare_digest(signature, expected_signature):
                logger.warning("CSRF token signature mismatch")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"CSRF token validation error: {e}")
            return False
    
    def create_cookie_value(self, user_id: Optional[str] = None) -> str:
        """
        Create CSRF token value for cookie.
        
        Args:
            user_id: Optional user identifier
        
        Returns:
            Token string suitable for Set-Cookie header
        """
        return self.generate_token(user_id)
    
    def verify_double_submit(
        self,
        cookie_token: Optional[str],
        header_token: Optional[str],
        user_id: Optional[str] = None
    ) -> bool:
        """
        Verify double-submit CSRF protection.
        
        Both cookie and header tokens must be present, valid, and match.
        
        Args:
            cookie_token: Token from cookie
            header_token: Token from X-CSRF-Token header
            user_id: User ID for bound tokens
        
        Returns:
            True if both tokens are valid and match
        """
        if not cookie_token or not header_token:
            logger.warning("Missing CSRF tokens (cookie or header)")
            return False
        
        # Validate cookie token
        if not self.validate_token(cookie_token, user_id):
            logger.warning("Invalid CSRF cookie token")
            return False
        
        # Validate header token
        if not self.validate_token(header_token, user_id):
            logger.warning("Invalid CSRF header token")
            return False
        
        # Tokens must match (constant-time comparison)
        if not hmac.compare_digest(cookie_token.encode('utf-8'), header_token.encode('utf-8')):
            logger.warning("CSRF tokens do not match")
            return False
        
        return True


# Global CSRF protection instance
_csrf_protection: Optional[CSRFProtection] = None


def get_csrf_protection(secret_key: Optional[str] = None) -> CSRFProtection:
    """
    Get or create the global CSRF protection instance.
    
    Args:
        secret_key: Secret key for HMAC (required on first call)
    
    Returns:
        CSRFProtection instance
    
    Raises:
        ValueError: If secret_key not provided on first call
    """
    global _csrf_protection
    
    if _csrf_protection is None:
        if not secret_key:
            raise ValueError("CSRF secret key required for initialization")
        _csrf_protection = CSRFProtection(secret_key)
    
    return _csrf_protection
