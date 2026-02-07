"""FastAPI middleware for rate limiting."""
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from rate_limiter import RateLimiter
from config import RateLimiterConfig


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
        identifier = identifier_getter(request)
        is_allowed, metadata = rate_limiter.is_allowed(
            identifier,
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
