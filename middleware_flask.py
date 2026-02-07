"""Flask middleware for rate limiting."""
from typing import Callable, Optional
from functools import wraps
from flask import Flask, request, jsonify, make_response
from rate_limiter import RateLimiter
from config import RateLimiterConfig


class FlaskRateLimiter:
    """Flask extension for rate limiting."""
    
    def __init__(
        self,
        app: Optional[Flask] = None,
        config: Optional[RateLimiterConfig] = None,
        identifier_func: Optional[Callable] = None,
    ):
        """
        Initialize Flask rate limiter.
        
        Args:
            app: Flask application
            config: Rate limiter configuration
            identifier_func: Function to extract identifier from request
        """
        self.rate_limiter = RateLimiter(config)
        self.identifier_func = identifier_func or self._default_identifier
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize with Flask app."""
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        app.extensions = getattr(app, 'extensions', {})
        app.extensions['rate_limiter'] = self
    
    def _default_identifier(self) -> str:
        """Extract client IP as default identifier."""
        # Try to get real IP from headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.remote_addr or "unknown"
    
    def _before_request(self):
        """Check rate limit before processing request."""
        # Skip if endpoint has custom rate limit
        if hasattr(request, '_rate_limit_checked'):
            return None
        return None
    
    def _after_request(self, response):
        """Add rate limit headers to response."""
        if hasattr(request, '_rate_limit_metadata'):
            metadata = request._rate_limit_metadata
            response.headers['X-RateLimit-Limit'] = str(metadata['limit'])
            response.headers['X-RateLimit-Remaining'] = str(metadata['remaining'])
            response.headers['X-RateLimit-Reset'] = str(metadata['reset'])
        return response
    
    def limit(
        self,
        max_requests: Optional[int] = None,
        window_seconds: Optional[int] = None,
        identifier_func: Optional[Callable] = None
    ):
        """
        Decorator for rate limiting specific routes.
        
        Usage:
            @app.route('/api/endpoint')
            @rate_limiter.limit(max_requests=10, window_seconds=60)
            def endpoint():
                return {"message": "Success"}
        """
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                request._rate_limit_checked = True
                
                # Get identifier
                identifier_getter = identifier_func or self.identifier_func
                identifier = identifier_getter()
                
                # Check rate limit
                is_allowed, metadata = self.rate_limiter.is_allowed(
                    identifier,
                    max_requests=max_requests,
                    window_seconds=window_seconds
                )
                
                # Store metadata for after_request
                request._rate_limit_metadata = metadata
                
                if not is_allowed:
                    response = make_response(
                        jsonify({
                            "error": "Rate limit exceeded",
                            "message": "Too many requests. Please try again later.",
                            "limit": metadata["limit"],
                            "reset": metadata["reset"],
                            "retry_after": metadata["retry_after"]
                        }),
                        429
                    )
                    response.headers['X-RateLimit-Limit'] = str(metadata['limit'])
                    response.headers['X-RateLimit-Remaining'] = '0'
                    response.headers['X-RateLimit-Reset'] = str(metadata['reset'])
                    response.headers['Retry-After'] = str(metadata['retry_after'])
                    return response
                
                return f(*args, **kwargs)
            
            return decorated_function
        return decorator


def create_rate_limit_middleware(
    app: Flask,
    config: Optional[RateLimiterConfig] = None,
    max_requests: Optional[int] = None,
    window_seconds: Optional[int] = None,
    identifier_func: Optional[Callable] = None
):
    """
    Create global rate limiting middleware for Flask.
    
    Args:
        app: Flask application
        config: Rate limiter configuration
        max_requests: Maximum requests per window
        window_seconds: Time window in seconds
        identifier_func: Function to extract identifier
    """
    rate_limiter = RateLimiter(config)
    identifier_getter = identifier_func or (lambda: request.remote_addr or "unknown")
    
    @app.before_request
    def check_rate_limit():
        identifier = identifier_getter()
        is_allowed, metadata = rate_limiter.is_allowed(
            identifier,
            max_requests=max_requests,
            window_seconds=window_seconds
        )
        
        request._rate_limit_metadata = metadata
        
        if not is_allowed:
            response = make_response(
                jsonify({
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please try again later.",
                    "limit": metadata["limit"],
                    "reset": metadata["reset"],
                    "retry_after": metadata["retry_after"]
                }),
                429
            )
            response.headers['X-RateLimit-Limit'] = str(metadata['limit'])
            response.headers['X-RateLimit-Remaining'] = '0'
            response.headers['X-RateLimit-Reset'] = str(metadata['reset'])
            response.headers['Retry-After'] = str(metadata['retry_after'])
            return response
    
    @app.after_request
    def add_rate_limit_headers(response):
        if hasattr(request, '_rate_limit_metadata'):
            metadata = request._rate_limit_metadata
            response.headers['X-RateLimit-Limit'] = str(metadata['limit'])
            response.headers['X-RateLimit-Remaining'] = str(metadata['remaining'])
            response.headers['X-RateLimit-Reset'] = str(metadata['reset'])
        return response
    
    return rate_limiter
