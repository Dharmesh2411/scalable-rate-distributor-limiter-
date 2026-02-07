# API Rate Limiter with Redis

A production-ready, Redis-based API rate limiting middleware for Python web applications. Supports both **FastAPI** and **Flask** frameworks with flexible configuration options.

## Features

✨ **Sliding Window Algorithm** - Accurate rate limiting using Redis sorted sets  
🚀 **Framework Support** - Works with FastAPI and Flask  
⚙️ **Flexible Configuration** - Environment variables or programmatic setup  
🎯 **Multiple Strategies** - Global middleware or route-specific decorators  
📊 **Rate Limit Headers** - Standard `X-RateLimit-*` headers in responses  
🔧 **Customizable Identifiers** - Rate limit by IP, user ID, API key, or custom logic  
💾 **Redis-Backed** - Distributed rate limiting across multiple servers  

## Installation

### 1. Clone or copy the project files

```bash
# Install dependencies
pip install -r requirements.txt
```

### 2. Set up Redis

Make sure you have Redis running locally or use a remote Redis instance:

```bash
# Using Docker
docker run -d -p 6379:6379 redis:latest

# Or install Redis locally
# Windows: https://redis.io/docs/getting-started/installation/install-redis-on-windows/
# Linux: sudo apt-get install redis-server
# macOS: brew install redis
```

### 3. Configure environment variables

Copy `.env.example` to `.env` and update values:

```bash
cp .env.example .env
```

Edit `.env`:
```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

## Usage

### FastAPI Example

#### Global Middleware (All Routes)

```python
from fastapi import FastAPI
from middleware_fastapi import RateLimitMiddleware
from config import RateLimiterConfig

app = FastAPI()

# Apply rate limiting to all routes
app.add_middleware(
    RateLimitMiddleware,
    config=RateLimiterConfig(),
    max_requests=100,  # 100 requests
    window_seconds=60   # per 60 seconds
)

@app.get("/api/endpoint")
async def endpoint():
    return {"message": "Success"}
```

#### Route-Specific Rate Limiting

```python
from fastapi import FastAPI, Depends
from middleware_fastapi import rate_limit_dependency
from rate_limiter import RateLimiter
from config import RateLimiterConfig

app = FastAPI()
rate_limiter = RateLimiter(RateLimiterConfig())

@app.get(
    "/api/strict",
    dependencies=[Depends(rate_limit_dependency(
        rate_limiter,
        max_requests=10,
        window_seconds=60
    ))]
)
async def strict_endpoint():
    return {"message": "Limited to 10 requests per minute"}
```

#### Run FastAPI Example

```bash
python example_fastapi.py
# Visit http://localhost:8000/docs
```

### Flask Example

#### Decorator-Based Rate Limiting

```python
from flask import Flask
from middleware_flask import FlaskRateLimiter
from config import RateLimiterConfig

app = Flask(__name__)
rate_limiter = FlaskRateLimiter(app, RateLimiterConfig())

@app.route("/api/endpoint")
@rate_limiter.limit(max_requests=100, window_seconds=60)
def endpoint():
    return {"message": "Success"}
```

#### Global Middleware

```python
from flask import Flask
from middleware_flask import create_rate_limit_middleware
from config import RateLimiterConfig

app = Flask(__name__)

# Apply to all routes
create_rate_limit_middleware(
    app,
    config=RateLimiterConfig(),
    max_requests=100,
    window_seconds=60
)
```

#### Run Flask Example

```bash
python example_flask.py
# Visit http://localhost:5000
```

## Advanced Configuration

### Custom Identifier Function

Rate limit by user ID, API key, or custom logic:

```python
# FastAPI
def get_user_id(request: Request) -> str:
    return request.headers.get("X-User-ID", "anonymous")

app.add_middleware(
    RateLimitMiddleware,
    identifier_func=get_user_id,
    max_requests=100,
    window_seconds=60
)

# Flask
def get_user_id() -> str:
    return request.headers.get("X-User-ID", "anonymous")

rate_limiter = FlaskRateLimiter(
    app,
    identifier_func=get_user_id
)
```

### Programmatic Configuration

```python
from config import RateLimiterConfig

config = RateLimiterConfig(
    redis_host="redis.example.com",
    redis_port=6380,
    redis_password="secret",
    default_requests=200,
    default_window=120
)
```

### Direct Rate Limiter Usage

```python
from rate_limiter import RateLimiter
from config import RateLimiterConfig

limiter = RateLimiter(RateLimiterConfig())

# Check if request is allowed
is_allowed, metadata = limiter.is_allowed(
    identifier="user_123",
    max_requests=10,
    window_seconds=60
)

if is_allowed:
    print(f"Request allowed. Remaining: {metadata['remaining']}")
else:
    print(f"Rate limit exceeded. Reset at: {metadata['reset']}")

# Get current usage
usage = limiter.get_usage("user_123", window_seconds=60)
print(f"Current usage: {usage}")

# Reset rate limit for a user
limiter.reset("user_123")
```

## Response Headers

The middleware automatically adds standard rate limit headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1738515600
```

When rate limit is exceeded (429 response):

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1738515600
Retry-After: 45
```

## Error Response Format

```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Please try again later.",
  "limit": 100,
  "reset": 1738515600,
  "retry_after": 45
}
```

## Project Structure

```
.
├── config.py                 # Configuration management
├── rate_limiter.py          # Core rate limiter logic
├── middleware_fastapi.py    # FastAPI middleware
├── middleware_flask.py      # Flask middleware
├── example_fastapi.py       # FastAPI example app
├── example_flask.py         # Flask example app
├── requirements.txt         # Python dependencies
├── .env.example            # Environment template
└── README.md               # This file
```

## How It Works

The rate limiter uses Redis **sorted sets** with a **sliding window** algorithm:

1. Each request adds a timestamp to a Redis sorted set
2. Old timestamps outside the window are removed
3. Current request count is checked against the limit
4. If allowed, the request proceeds; otherwise, returns 429

This approach provides:
- **Accurate rate limiting** (no bucket edge cases)
- **Distributed support** (works across multiple servers)
- **Automatic cleanup** (Redis TTL removes old data)

## Testing

Test the rate limiter with curl:

```bash
# Test FastAPI endpoint
for i in {1..15}; do
  curl -i http://localhost:8000/api/strict
  echo "Request $i"
done

# Test Flask endpoint
for i in {1..15}; do
  curl -i http://localhost:5000/api/strict
  echo "Request $i"
done
```

You should see successful responses until the limit is reached, then 429 errors.

## Production Considerations

1. **Redis Persistence** - Configure Redis with AOF or RDB for data persistence
2. **Redis Clustering** - Use Redis Cluster for high availability
3. **Connection Pooling** - The redis-py client handles this automatically
4. **Monitoring** - Track rate limit metrics in your observability platform
5. **Whitelist/Blacklist** - Add IP whitelisting for trusted clients
6. **Different Limits** - Set different limits for authenticated vs anonymous users

## License

MIT License - feel free to use in your projects!

## Contributing

Contributions welcome! Feel free to submit issues or pull requests.
