"""Example FastAPI application with rate limiting."""
from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse
from middleware_fastapi import RateLimitMiddleware, rate_limit_dependency
from rate_limiter import RateLimiter
from config import RateLimiterConfig

# Create FastAPI app
app = FastAPI(title="Rate Limited API", version="1.0.0")

# Initialize configuration
config = RateLimiterConfig()

# Add global rate limiting middleware (100 requests per 60 seconds)
app.add_middleware(
    RateLimitMiddleware,
    config=config,
    max_requests=100,
    window_seconds=60
)

# Create rate limiter instance for custom endpoints
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
    """Public endpoint - uses global rate limit (100 req/min)."""
    return {
        "message": "This is a public endpoint",
        "rate_limit": "100 requests per minute (global)"
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


@app.get(
    "/api/premium",
    dependencies=[Depends(rate_limit_dependency(rate_limiter, max_requests=1000, window_seconds=60))]
)
async def premium_endpoint():
    """Premium endpoint - higher rate limit (1000 req/min)."""
    return {
        "message": "This is a premium endpoint with higher limits",
        "rate_limit": "1000 requests per minute"
    }


@app.post("/api/data")
async def create_data(request: Request):
    """POST endpoint - uses global rate limit."""
    body = await request.json() if request.headers.get("content-type") == "application/json" else {}
    return {
        "message": "Data received",
        "data": body
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
        # Test Redis connection
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
    import uvicorn
    print("Starting FastAPI server with rate limiting...")
    print("Global rate limit: 100 requests per 60 seconds")
    print("Visit http://localhost:8000/docs for API documentation")
    uvicorn.run(app, host="0.0.0.0", port=8000)
