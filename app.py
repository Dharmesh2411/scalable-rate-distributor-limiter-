import os
import time
from typing import Optional, Tuple, Callable

import redis
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

load_dotenv()

class RateLimiterConfig:
    """Configuration for rate limiter and Redis connection."""
    
    def __init__(
        self,
        redis_host: Optional[str] = None,
        redis_port: Optional[int] = None,
        redis_db: Optional[int] = None,
        redis_password: Optional[str] = None,
        default_requests: Optional[int] = None,
        default_window: Optional[int] = None,
    ):
        """
        Initialize configuration from parameters or environment variables.
        
        Args:
            redis_host: Redis host address
            redis_port: Redis port
            redis_db: Redis database number
            redis_password: Redis password
            default_requests: Default maximum requests per window
            default_window: Default time window in seconds
        """
        self.redis_host = redis_host or os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(redis_port or os.getenv("REDIS_PORT", 6379))
        self.redis_db = int(redis_db or os.getenv("REDIS_DB", 0))
        self.redis_password = redis_password or os.getenv("REDIS_PASSWORD", None)
        self.default_requests = int(default_requests or os.getenv("RATE_LIMIT_REQUESTS", 100))
        self.default_window = int(default_window or os.getenv("RATE_LIMIT_WINDOW", 60))
    
    def get_redis_url(self) -> str:
        """Generate Redis connection URL."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

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
                - retry_after: Seconds to wait before retrying (if rate limited)
        """
        max_requests = max_requests or self.config.default_requests
        window_seconds = window_seconds or self.config.default_window
        
        key = f"rate_limit:{identifier}"
        current_time = time.time()
        window_start = current_time - window_seconds - 0.00001
        
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
        window_start = current_time - window_seconds - 0.00001
        
        # Remove old entries and count
        self.redis_client.zremrangebyscore(key, 0, window_start)
        return self.redis_client.zcard(key)
    
    def close(self):
        """Close Redis connection."""
        self.redis_client.close()

class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting requests."""
    
    def __init__(
        self,
        app: ASGIApp,
        config: Optional[RateLimiterConfig] = None,
        identifier_func: Optional[Callable[[Request], str]] = None,
        max_requests: Optional[int] = None,
        window_seconds: Optional[int] = None,
    ):
        """
        Initialize rate limit middleware.
        
        Args:
            app: FastAPI application
            config: Rate limiter configuration
            identifier_func: Function to extract identifier from request (default: uses client IP)
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds
        """
        super().__init__(app)
        self.rate_limiter = RateLimiter(config)
        self.identifier_func = identifier_func or self._default_identifier
        self.max_requests = max_requests
        self.window_seconds = window_seconds
    
    def _default_identifier(self, request: Request) -> str:
        """Extract client IP as default identifier."""
        # Try to get real IP from headers (for proxy/load balancer scenarios)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"
    
    async def dispatch(self, request: Request, call_next):
        """Process request through rate limiter."""
        # Extract identifier
        identifier = self.identifier_func(request)
        
        # Check rate limit
        is_allowed, metadata = self.rate_limiter.is_allowed(
            identifier,
            max_requests=self.max_requests,
            window_seconds=self.window_seconds
        )
        
        # Add rate limit headers to response
        if is_allowed:
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(metadata["limit"])
            response.headers["X-RateLimit-Remaining"] = str(metadata["remaining"])
            response.headers["X-RateLimit-Reset"] = str(metadata["reset"])
            return response
        else:
            # Return 429 Too Many Requests
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Please try again later.",
                    "limit": metadata["limit"],
                    "reset": metadata["reset"],
                    "retry_after": metadata["retry_after"]
                },
                headers={
                    "X-RateLimit-Limit": str(metadata["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(metadata["reset"]),
                    "Retry-After": str(metadata["retry_after"])
                }
            )


def rate_limit_dependency(
    rate_limiter: RateLimiter,
    max_requests: Optional[int] = None,
    window_seconds: Optional[int] = None,
    identifier_func: Optional[Callable[[Request], str]] = None
):
    """
    FastAPI dependency for route-specific rate limiting.
    
    Usage:
        @app.get("/api/endpoint", dependencies=[Depends(rate_limit_dependency(...))])
    """
    def _default_identifier(request: Request) -> str:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    identifier_getter = identifier_func or _default_identifier
    
    async def dependency(request: Request):
        # Build a namespaced identifier for route-specific limits so
        # they don't collide with global middleware counters.
        base_identifier = identifier_getter(request)
        route_identifier = f"route:{request.url.path}:{base_identifier}"

        is_allowed, metadata = rate_limiter.is_allowed(
            route_identifier,
            max_requests=max_requests,
            window_seconds=window_seconds
        )
        
        if not is_allowed:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "limit": metadata["limit"],
                    "reset": metadata["reset"],
                    "retry_after": metadata["retry_after"]
                },
                headers={
                    "X-RateLimit-Limit": str(metadata["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(metadata["reset"]),
                    "Retry-After": str(metadata["retry_after"])
                }
            )
        
        return metadata
    
    return dependency

# Creating FastAPI app
app = FastAPI(title="Rate Limited API", version="1.0.0")

# Initializing config
config = RateLimiterConfig()

# Adding global rate limiting middleware (50 requests per 60 seconds)
app.add_middleware(
    RateLimitMiddleware,
    config=config,
    max_requests=50,
    window_seconds=60
)

# For custom endpoints rate limiter
rate_limiter = RateLimiter(config)


@app.get("/")
async def root():
    """Root endpoint - uses global rate limit."""
    return {
        "message": "Welcome to the Rate Limited API",
        "docs": "/docs"
    }


@app.get("/api/public")
async def public_endpoint():
    """Public endpoint - uses global rate limit (50 req/min)."""
    return {
        "message": "This is a public endpoint",
        "rate_limit": "50 requests per minute (global)"
    }


@app.get(
    "/api/strict",
    dependencies=[Depends(rate_limit_dependency(rate_limiter, max_requests=10, window_seconds=60))]
)
async def strict_endpoint():
    """Strict endpoint - custom rate limit (10 req/min)."""
    return {
        "message": "This is a strictly rate-limited endpoint",
        "rate_limit": "10 requests per minute"
    }


@app.get("/api/user/{user_id}")
async def get_user(user_id: str):
    """User-specific endpoint - uses global rate limit."""
    return {
        "user_id": user_id,
        "message": f"User {user_id} data"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint - uses global rate limit."""
    try:
        # testing redis connection
        rate_limiter.redis_client.ping()
        return {
            "status": "healthy",
            "redis": "connected"
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "redis": "disconnected",
                "error": str(e)
            }
        )


if __name__ == "__main__":
    print("Starting FastAPI server with rate limiting...")
    print("Global rate limit: 50 requests per 60 seconds")
    print("Visit http://localhost:8000/docs for API documentation")
    uvicorn.run(app, host="0.0.0.0", port=8000)
