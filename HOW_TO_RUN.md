# 🚀 How to Run and Test the API Rate Limiter

## ✅ What's Already Done

1. ✅ Virtual environment created at `env\`
2. ✅ All dependencies installed (redis, fastapi, flask, uvicorn, etc.)
3. ✅ Environment file created (`.env`)
4. ✅ Project files ready

## 🎯 Two Ways to Run

### Option 1: Demo Version (NO Redis Required) ⭐ EASIEST

This version uses in-memory storage - perfect for testing immediately!

```bash
# Activate virtual environment
.\env\Scripts\activate

# Run the demo
python demo_no_redis.py
```

Then open your browser to:
- **http://localhost:8000** - Homepage
- **http://localhost:8000/docs** - Interactive API docs

### Option 2: Full Version (WITH Redis) 🔥 PRODUCTION

This is the full Redis-backed version for production use.

**Step 1: Install Redis**

Choose one method:

**A) Using WSL (Windows Subsystem for Linux):**
```bash
wsl
sudo apt-get update
sudo apt-get install redis-server
redis-server
```

**B) Download Redis for Windows:**
- Visit: https://github.com/microsoftarchive/redis/releases
- Download: `Redis-x64-3.0.504.msi`
- Install and start the service

**C) Use Cloud Redis (Free):**
- Upstash: https://upstash.com/
- Redis Cloud: https://redis.com/try-free/
- Update `.env` with connection details

**Step 2: Run the application**
```bash
# Activate virtual environment
.\env\Scripts\activate

# Run FastAPI example
python example_fastapi.py
```

Visit: **http://localhost:8000/docs**

## 🧪 Testing Rate Limiting

### Method 1: Browser Testing

1. Go to http://localhost:8000/docs
2. Find the `/api/strict` endpoint (10 requests/min limit)
3. Click "Try it out" → "Execute"
4. Keep clicking Execute
5. After 10 requests, you'll see a **429 error** (rate limited!)

### Method 2: Python Test Script

```bash
# Make sure server is running first
python test_rate_limiter.py
```

This will run comprehensive tests showing:
- ✅ Basic rate limiting
- ✅ Sliding window algorithm
- ✅ Multiple users
- ✅ Usage tracking

### Method 3: Manual curl Testing

```powershell
# Test strict endpoint (10 req/min)
for ($i=1; $i -le 15; $i++) {
    curl http://localhost:8000/api/strict
    Write-Host "Request $i"
}
```

## 📊 What You'll See

### Successful Request (200 OK)
```json
{
  "message": "This is a strictly rate-limited endpoint",
  "rate_limit": "10 requests per minute"
}
```

**Response Headers:**
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 5
X-RateLimit-Reset: 1738516200
```

### Rate Limited (429 Too Many Requests)
```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Please try again later.",
  "limit": 10,
  "reset": 1738516200,
  "retry_after": 45
}
```

## 🎨 Available Endpoints

| Endpoint | Rate Limit | Description |
|----------|------------|-------------|
| `/` | 100/min | Homepage |
| `/api/public` | 100/min | Public endpoint |
| `/api/strict` | 10/min | Strict rate limit |
| `/api/premium` | 1000/min | High limit |
| `/health` | 100/min | Health check |

## 🔧 Troubleshooting

### "Module not found" error
```bash
# Make sure virtual environment is activated
.\env\Scripts\activate
```

### "Redis connection failed"
- Use `demo_no_redis.py` instead (no Redis needed)
- OR install Redis (see Option 2 above)

### Port 8000 already in use
- Change port in the Python file
- Or stop the other service using port 8000

## 📝 Quick Commands Cheat Sheet

```bash
# Activate virtual environment
.\env\Scripts\activate

# Run demo (no Redis)
python demo_no_redis.py

# Run full version (needs Redis)
python example_fastapi.py

# Run Flask version
python example_flask.py

# Run tests
python test_rate_limiter.py

# Deactivate virtual environment
deactivate
```

## 🎉 That's It!

Your API rate limiter is ready to use. Start with `demo_no_redis.py` to see it in action immediately!
