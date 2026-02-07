"""Simple demo of rate limiter without Redis - for testing purposes only."""
import time
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


# In-memory storage (for demo only - not for production!)
request_store: Dict[str, list] = defaultdict(list)


class SimpleRateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter for demo purposes."""
    
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
    
    def _get_client_ip(self, request: Request) -> str:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _is_allowed(self, identifier: str) -> Tuple[bool, dict]:
        current_time = time.time()
        window_start = current_time - self.window_seconds
        
        # Clean old requests
        request_store[identifier] = [
            ts for ts in request_store[identifier] if ts > window_start
        ]
        
        request_count = len(request_store[identifier])
        remaining = max(0, self.max_requests - request_count - 1)
        
        metadata = {
            "limit": self.max_requests,
            "remaining": remaining,
            "reset": int(current_time + self.window_seconds),
            "retry_after": self.window_seconds if request_count >= self.max_requests else 0
        }
        
        is_allowed = request_count < self.max_requests
        
        if is_allowed:
            request_store[identifier].append(current_time)
        
        return is_allowed, metadata
    
    async def dispatch(self, request: Request, call_next):
        identifier = self._get_client_ip(request)
        is_allowed, metadata = self._is_allowed(identifier)
        
        if is_allowed:
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(metadata["limit"])
            response.headers["X-RateLimit-Remaining"] = str(metadata["remaining"])
            response.headers["X-RateLimit-Reset"] = str(metadata["reset"])
            return response
        else:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please try again later.",
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


# Create FastAPI app
app = FastAPI(title="Rate Limited API Demo (No Redis)", version="1.0.0")

# Add global rate limiting (10 requests per 10 seconds - for testing)
app.add_middleware(
    SimpleRateLimitMiddleware,
    max_requests=10,
    window_seconds=10
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to the Rate Limited API Demo",
        "note": "This demo uses in-memory storage (no Redis required)",
        "docs": "/docs",
        "endpoints": {
            "/api/public": "Public endpoint (100 req/min)",
            "/api/test": "Test endpoint",
            "/health": "Health check"
        }
    }


@app.get("/api/public")
async def public_endpoint():
    """Public endpoint with rate limiting."""
    return {
        "message": "This is a public endpoint",
        "rate_limit": "100 requests per minute",
        "storage": "in-memory (demo only)"
    }


@app.get("/api/test")
async def test_endpoint():
    """Test endpoint."""
    return {
        "message": "Test successful",
        "timestamp": time.time()
    }


@app.post("/api/data")
async def create_data(request: Request):
    """POST endpoint."""
    try:
        body = await request.json() if request.headers.get("content-type") == "application/json" else {}
    except:
        body = {}
    return {
        "message": "Data received",
        "data": body
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "storage": "in-memory",
        "note": "No Redis required for this demo"
    }


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚀 Starting FastAPI Demo Server (No Redis Required)")
    print("="*60)
    print("\n📝 NOTE: This demo uses in-memory storage")
    print("   For production, use the Redis version in example_fastapi.py")
    print("\n🌐 Server starting at: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("\n⚡ Rate Limit: 10 requests per 10 seconds (Easy Testing!)")
    print("\n💡 Test it:")
    print("   - Visit http://localhost:8000/docs")
    print("   - Try making multiple requests to /api/public")
    print("   - After 10 requests, you'll get 429 errors")
    print("\n" + "="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
