# Quick Start Guide - Windows (No Docker)

## ✅ Step 1: Virtual Environment Created
The virtual environment is already set up at `env\`

## ✅ Step 2: Dependencies Installed
All packages (redis, fastapi, flask, etc.) are installed in the virtual environment.

## ⚠️ Step 3: Redis Setup (Required)

Since Docker is not available, you have two options:

### Option A: Install Redis on Windows (Recommended)

1. **Download Redis for Windows:**
   - Visit: https://github.com/microsoftarchive/redis/releases
   - Download: `Redis-x64-3.0.504.msi`
   - Install and start Redis service

2. **Or use WSL (Windows Subsystem for Linux):**
   ```bash
   wsl
   sudo apt-get update
   sudo apt-get install redis-server
   redis-server
   ```

### Option B: Use a Cloud Redis Instance

Use a free Redis cloud service like:
- Redis Cloud (https://redis.com/try-free/)
- Upstash (https://upstash.com/)

Then update `.env` file with your Redis connection details.

## 🚀 Step 4: Run the Application

Once Redis is running, start the FastAPI server:

```bash
# Activate virtual environment (if not already active)
.\env\Scripts\activate

# Run FastAPI example
python example_fastapi.py
```

The server will start at: **http://localhost:8000**

## 📝 Step 5: Test the API

### In Browser:
- Visit: http://localhost:8000/docs (Interactive API documentation)
- Try the endpoints and see rate limiting in action!

### With curl (if available):
```bash
# Test strict endpoint (10 requests/min)
for /L %i in (1,1,15) do curl http://localhost:8000/api/strict
```

### With Python test script:
```bash
python test_rate_limiter.py
```

## 🔍 What to Expect

- First 10 requests to `/api/strict` will succeed (200 OK)
- Requests 11+ will be rate limited (429 Too Many Requests)
- Response headers will show:
  - `X-RateLimit-Limit: 10`
  - `X-RateLimit-Remaining: 0`
  - `Retry-After: <seconds>`

## ❌ Troubleshooting

### "Redis connection failed"
- Make sure Redis is running on port 6379
- Check with: `redis-cli ping` (should return "PONG")

### "Module not found"
- Make sure virtual environment is activated
- Run: `.\env\Scripts\activate`

### Server won't start
- Check if port 8000 is already in use
- Change port in `example_fastapi.py` if needed
