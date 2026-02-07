# Setup and Run Instructions

## Step 1: Create Virtual Environment

```bash
# Create virtual environment
python -m venv env

# Activate virtual environment
# On Windows:
env\Scripts\activate

# On Linux/Mac:
# source env/bin/activate
```

## Step 2: Install Dependencies

```bash
# Install all required packages in the virtual environment
pip install -r requirements.txt
```

## Step 3: Set Up Environment Variables

```bash
# Copy the example environment file
copy .env.example .env

# The default settings work for local Redis
# Edit .env if you need custom Redis settings
```

## Step 4: Start Redis

### Option A: Using Docker (Recommended)
```bash
docker run -d -p 6379:6379 redis:latest
```

### Option B: Install Redis Locally
- Windows: https://redis.io/docs/getting-started/installation/install-redis-on-windows/
- Or use WSL and install Redis there

## Step 5: Run Tests

```bash
# Test the core rate limiter
python test_rate_limiter.py
```

## Step 6: Run Example Applications

### FastAPI Example
```bash
# Start FastAPI server
python example_fastapi.py

# Visit in browser:
# http://localhost:8000/docs (API documentation)
# http://localhost:8000 (root endpoint)
```

### Flask Example
```bash
# Start Flask server
python example_flask.py

# Visit in browser:
# http://localhost:5000
```

## Step 7: Test Rate Limiting

### Option A: Use Quick Test Script
```bash
python quick_test.py
```

### Option B: Manual Testing with curl
```bash
# Test strict endpoint (10 requests/minute limit)
for /L %i in (1,1,15) do (
  curl http://localhost:8000/api/strict
  echo Request %i
)
```

### Option C: Test in Browser
1. Open http://localhost:8000/docs (FastAPI)
2. Try the `/api/strict` endpoint multiple times
3. After 10 requests, you'll get a 429 error

## Troubleshooting

### Redis Connection Error
```
Error: Redis connection failed
```
**Solution**: Make sure Redis is running on port 6379

### Module Not Found Error
```
ModuleNotFoundError: No module named 'redis'
```
**Solution**: Make sure virtual environment is activated and dependencies are installed

### Port Already in Use
```
Address already in use
```
**Solution**: Change the port in the example files or stop the other service
