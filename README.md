# Scalable Rate Limiter API

A high-performance, production-ready rate limiting solution built with FastAPI and Redis. Provides both global middleware-based and route-specific rate limiting with sliding window algorithm.

## Features

- **Redis-backed Rate Limiting**: Uses Redis for distributed, scalable rate limiting
- **Sliding Window Algorithm**: Accurate rate limiting with smooth request distribution
- **Global Middleware**: Apply rate limits to all endpoints globally
- **Per-Route Limits**: Set custom limits for specific endpoints
- **Proxy-aware**: Handles X-Forwarded-For and X-Real-IP headers
- **HTTP Standards**: Returns proper 429 (Too Many Requests) responses with Retry-After headers
- **Rate Limit Headers**: Includes X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset

## Requirements

- Python 3.8+
- Redis server
- FastAPI
- Redis Python client

## Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/Scalable-Rate-limiter.git
cd Scalable-Rate-limiter
```

2. **Create a virtual environment**
```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables** (optional)
Create a `.env` file in the root directory:
```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
RATE_LIMIT_REQUESTS=50
RATE_LIMIT_WINDOW=60
```

## Running the Application

Start the FastAPI server:
```bash
python app.py
```

The API will be available at `http://localhost:8000`
API documentation: `http://localhost:8000/docs`

## API Endpoints

### Global Rate Limited (50 requests/min)

- `GET /` - Welcome message
- `GET /api/public` - Public endpoint
- `GET /api/user/{user_id}` - User data endpoint
- `GET /health` - Health check with Redis status

### Strict Rate Limited (10 requests/min)

- `GET /api/strict` - Demonstrates route-specific rate limiting

## Configuration

### Global Rate Limiting
The middleware applies a global rate limit to all requests:
```python
app.add_middleware(
    RateLimitMiddleware,
    config=config,
    max_requests=50,
    window_seconds=60
)
```

### Per-Route Rate Limiting
Apply custom limits to specific routes:
```python
@app.get(
    "/api/endpoint",
    dependencies=[Depends(rate_limit_dependency(
        rate_limiter, 
        max_requests=10, 
        window_seconds=60
    ))]
)
async def my_endpoint():
    return {"message": "Limited to 10 requests per minute"}
```

### Custom Identifier Function
By default, rate limiting uses client IP. Customize with:
```python
def get_user_id(request: Request) -> str:
    return request.headers.get("X-User-ID", "anonymous")

app.add_middleware(
    RateLimitMiddleware,
    config=config,
    identifier_func=get_user_id,
    max_requests=100,
    window_seconds=60
)
```

## Rate Limit Headers

Successful requests include:
```
X-RateLimit-Limit: 50
X-RateLimit-Remaining: 42
X-RateLimit-Reset: 1708265440
```

Rate-limited responses (429):
```
X-RateLimit-Limit: 50
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1708265440
Retry-After: 60
```

## Architecture

### RateLimiterConfig
Manages Redis connection configuration and default limits.

### RateLimiter
Core sliding window rate limiter:
- `is_allowed()` - Check if request is allowed
- `reset()` - Reset limits for an identifier
- `get_usage()` - Check current usage count

### RateLimitMiddleware
FastAPI middleware for global rate limiting on all routes.

### rate_limit_dependency
FastAPI dependency for per-route rate limiting.

## Performance

- **Atomic Operations**: Uses Redis pipelines for atomic rate limit checks
- **Distributed**: Works with multiple FastAPI instances
- **Low Latency**: Minimal overhead per request
- **Scalable**: Handles thousands of concurrent clients

## Testing

```bash
# Test with curl
curl http://localhost:8000/api/public

# Test rate limiting (send 51+ requests rapidly)
for i in {1..60}; do curl http://localhost:8000/api/public; done
```

## Development

To run tests:
```bash
pytest test_request_strict.py
```

## License

MIT

## Support

For issues, questions, or contributions, please open an issue or pull request on GitHub.
