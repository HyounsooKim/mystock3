"""
Rate limiting middleware using token bucket algorithm.
Protects API endpoints from abuse and excessive requests.
"""

import time
import logging
from typing import Dict, Tuple, Optional
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)


class TokenBucket:
    """
    Token bucket algorithm for rate limiting.
    
    Tokens are added at a constant rate up to a maximum capacity.
    Each request consumes one token. If no tokens available, request is rejected.
    """
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.
        
        Args:
            capacity: Maximum number of tokens (burst size)
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill = time.time()
        self.lock = asyncio.Lock()
    
    async def consume(self, tokens: int = 1) -> bool:
        """
        Attempt to consume tokens from bucket.
        
        Args:
            tokens: Number of tokens to consume
        
        Returns:
            True if tokens consumed, False if insufficient tokens
        """
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_refill
            
            # Refill tokens based on elapsed time
            self.tokens = min(
                self.capacity,
                self.tokens + elapsed * self.refill_rate
            )
            self.last_refill = now
            
            # Try to consume
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            return False
    
    def available_tokens(self) -> float:
        """Get current number of available tokens."""
        return self.tokens


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware with configurable limits per client.
    
    Features:
    - Token bucket algorithm per client IP
    - Different limits for authenticated vs anonymous users
    - Automatic bucket cleanup for inactive clients
    - Rate limit headers in responses
    """
    
    # Rate limits: (capacity, refill_rate per second)
    ANONYMOUS_LIMIT = (50, 10.0)  # 50 requests burst, 10 req/sec sustained
    AUTHENTICATED_LIMIT = (100, 20.0)  # 100 requests burst, 20 req/sec sustained
    
    # Cleanup settings
    CLEANUP_INTERVAL = 300  # 5 minutes
    BUCKET_EXPIRY = 600  # 10 minutes of inactivity
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.buckets: Dict[str, Tuple[TokenBucket, float]] = {}
        self.last_cleanup = time.time()
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request with rate limiting.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler
        
        Returns:
            HTTP response with rate limit headers
        """
        # Skip rate limiting for health check
        if request.url.path == "/health":
            return await call_next(request)
        
        # Get client identifier
        client_id = self._get_client_id(request)
        is_authenticated = self._is_authenticated(request)
        
        # Get or create token bucket
        bucket = await self._get_bucket(client_id, is_authenticated)
        
        # Try to consume token
        allowed = await bucket.consume(1)
        
        if not allowed:
            # Rate limit exceeded
            logger.warning(
                f"Rate limit exceeded for client: {client_id}",
                extra={"extra_fields": {
                    "client_id": client_id,
                    "authenticated": is_authenticated,
                    "path": request.url.path
                }}
            )
            
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": 1  # seconds
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        capacity = (
            self.AUTHENTICATED_LIMIT[0] if is_authenticated 
            else self.ANONYMOUS_LIMIT[0]
        )
        remaining = int(bucket.available_tokens())
        
        response.headers["X-RateLimit-Limit"] = str(capacity)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))
        
        # Periodic cleanup
        await self._cleanup_expired_buckets()
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """
        Get unique identifier for client.
        
        Prefers authenticated user ID, falls back to IP address.
        
        Args:
            request: HTTP request
        
        Returns:
            Client identifier string
        """
        # Try to get user ID from auth token
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            # Use token as identifier (could extract user_id if needed)
            return f"token:{auth_header[7:20]}"  # First 13 chars of token
        
        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        
        # Check for forwarded IP (behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        return f"ip:{client_ip}"
    
    def _is_authenticated(self, request: Request) -> bool:
        """
        Check if request has valid authentication.
        
        Args:
            request: HTTP request
        
        Returns:
            True if authenticated
        """
        auth_header = request.headers.get("Authorization", "")
        return auth_header.startswith("Bearer ") and len(auth_header) > 20
    
    async def _get_bucket(self, client_id: str, is_authenticated: bool) -> TokenBucket:
        """
        Get or create token bucket for client.
        
        Args:
            client_id: Client identifier
            is_authenticated: Whether client is authenticated
        
        Returns:
            TokenBucket instance
        """
        now = time.time()
        
        # Check if bucket exists and is not expired
        if client_id in self.buckets:
            bucket, last_access = self.buckets[client_id]
            if now - last_access < self.BUCKET_EXPIRY:
                # Update last access time
                self.buckets[client_id] = (bucket, now)
                return bucket
        
        # Create new bucket with appropriate limits
        capacity, refill_rate = (
            self.AUTHENTICATED_LIMIT if is_authenticated 
            else self.ANONYMOUS_LIMIT
        )
        
        bucket = TokenBucket(capacity, refill_rate)
        self.buckets[client_id] = (bucket, now)
        
        logger.debug(
            f"Created token bucket for client: {client_id}",
            extra={"extra_fields": {
                "client_id": client_id,
                "authenticated": is_authenticated,
                "capacity": capacity,
                "refill_rate": refill_rate
            }}
        )
        
        return bucket
    
    async def _cleanup_expired_buckets(self):
        """Remove expired token buckets to free memory."""
        now = time.time()
        
        # Only cleanup periodically
        if now - self.last_cleanup < self.CLEANUP_INTERVAL:
            return
        
        self.last_cleanup = now
        expired_clients = []
        
        for client_id, (bucket, last_access) in self.buckets.items():
            if now - last_access > self.BUCKET_EXPIRY:
                expired_clients.append(client_id)
        
        for client_id in expired_clients:
            del self.buckets[client_id]
        
        if expired_clients:
            logger.info(
                f"Cleaned up {len(expired_clients)} expired rate limit buckets",
                extra={"extra_fields": {"count": len(expired_clients)}}
            )


def get_rate_limit_middleware() -> RateLimitMiddleware:
    """
    Factory function to create rate limit middleware instance.
    
    Returns:
        RateLimitMiddleware class
    """
    return RateLimitMiddleware
