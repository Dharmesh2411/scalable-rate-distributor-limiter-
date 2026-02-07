"""Redis-based rate limiter implementation."""
import time
from typing import Optional, Tuple
import redis
from config import RateLimiterConfig


class RateLimiter:
    """Redis-based rate limiter using sliding window algorithm."""
    
    def __init__(self, config: Optional[RateLimiterConfig] = None):
        """
        Initialize rate limiter with Redis connection.
        
        Args:
            config: Rate limiter configuration object
        """
        self.config = config or RateLimiterConfig()
        self.redis_client = redis.from_url(
            self.config.get_redis_url(),
            decode_responses=True
        )
    
    def is_allowed(
        self,
        identifier: str,
        max_requests: Optional[int] = None,
        window_seconds: Optional[int] = None
    ) -> Tuple[bool, dict]:
        """
        Check if a request is allowed based on rate limits.
        
        Args:
            identifier: Unique identifier (e.g., IP address, user ID, API key)
            max_requests: Maximum number of requests allowed in the window
            window_seconds: Time window in seconds
        
        Returns:
            Tuple of (is_allowed, metadata) where metadata contains:
                - limit: Maximum requests allowed
                - remaining: Remaining requests in current window
                - reset: Unix timestamp when the limit resets
        """
        max_requests = max_requests or self.config.default_requests
        window_seconds = window_seconds or self.config.default_window
        
        key = f"rate_limit:{identifier}"
        current_time = time.time()
        window_start = current_time - window_seconds
        
        # Use Redis pipeline for atomic operations
        pipe = self.redis_client.pipeline()
        
        # Remove old entries outside the current window
        pipe.zremrangebyscore(key, 0, window_start)
        
        # Count requests in current window
        pipe.zcard(key)
        
        # Add current request timestamp
        pipe.zadd(key, {str(current_time): current_time})
        
        # Set expiration on the key
        pipe.expire(key, window_seconds)
        
        # Execute pipeline
        results = pipe.execute()
        request_count = results[1]
        
        # Calculate metadata
        reset_time = int(current_time + window_seconds)
        remaining = max(0, max_requests - request_count - 1)
        
        metadata = {
            "limit": max_requests,
            "remaining": remaining,
            "reset": reset_time,
            "retry_after": window_seconds if request_count >= max_requests else 0
        }
        
        is_allowed = request_count < max_requests
        
        # If not allowed, remove the request we just added
        if not is_allowed:
            self.redis_client.zrem(key, str(current_time))
        
        return is_allowed, metadata
    
    def reset(self, identifier: str) -> bool:
        """
        Reset rate limit for a specific identifier.
        
        Args:
            identifier: Unique identifier to reset
        
        Returns:
            True if reset was successful
        """
        key = f"rate_limit:{identifier}"
        return bool(self.redis_client.delete(key))
    
    def get_usage(self, identifier: str, window_seconds: Optional[int] = None) -> int:
        """
        Get current usage count for an identifier.
        
        Args:
            identifier: Unique identifier
            window_seconds: Time window in seconds
        
        Returns:
            Number of requests in the current window
        """
        window_seconds = window_seconds or self.config.default_window
        key = f"rate_limit:{identifier}"
        current_time = time.time()
        window_start = current_time - window_seconds
        
        # Remove old entries and count
        self.redis_client.zremrangebyscore(key, 0, window_start)
        return self.redis_client.zcard(key)
    
    def close(self):
        """Close Redis connection."""
        self.redis_client.close()
