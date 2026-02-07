"""Example Flask application with rate limiting."""
from flask import Flask, jsonify, request
from middleware_flask import FlaskRateLimiter, create_rate_limit_middleware
from config import RateLimiterConfig

# Create Flask app
app = Flask(__name__)

# Initialize configuration
config = RateLimiterConfig()

# Option 1: Use FlaskRateLimiter extension for decorator-based rate limiting
rate_limiter = FlaskRateLimiter(app, config)

# Option 2: Use global middleware (commented out - uncomment to use instead)
# create_rate_limit_middleware(app, config, max_requests=100, window_seconds=60)


@app.route("/")
def root():
    """Root endpoint."""
    return jsonify({
        "message": "Welcome to the Rate Limited Flask API",
        "endpoints": {
            "/api/public": "Public endpoint with default limits",
            "/api/strict": "Strict endpoint (10 req/min)",
            "/api/premium": "Premium endpoint (1000 req/min)",
            "/health": "Health check"
        }
    })


@app.route("/api/public")
@rate_limiter.limit(max_requests=100, window_seconds=60)
def public_endpoint():
    """Public endpoint - 100 requests per minute."""
    return jsonify({
        "message": "This is a public endpoint",
        "rate_limit": "100 requests per minute"
    })


@app.route("/api/strict")
@rate_limiter.limit(max_requests=10, window_seconds=60)
def strict_endpoint():
    """Strict endpoint - 10 requests per minute."""
    return jsonify({
        "message": "This is a strictly rate-limited endpoint",
        "rate_limit": "10 requests per minute"
    })


@app.route("/api/premium")
@rate_limiter.limit(max_requests=1000, window_seconds=60)
def premium_endpoint():
    """Premium endpoint - 1000 requests per minute."""
    return jsonify({
        "message": "This is a premium endpoint with higher limits",
        "rate_limit": "1000 requests per minute"
    })


@app.route("/api/data", methods=["POST"])
@rate_limiter.limit(max_requests=50, window_seconds=60)
def create_data():
    """POST endpoint - 50 requests per minute."""
    data = request.get_json() if request.is_json else {}
    return jsonify({
        "message": "Data received",
        "data": data
    })


@app.route("/api/user/<user_id>")
@rate_limiter.limit(max_requests=100, window_seconds=60)
def get_user(user_id):
    """User-specific endpoint."""
    return jsonify({
        "user_id": user_id,
        "message": f"User {user_id} data"
    })


@app.route("/health")
def health_check():
    """Health check endpoint - no rate limit."""
    try:
        # Test Redis connection
        rate_limiter.rate_limiter.redis_client.ping()
        return jsonify({
            "status": "healthy",
            "redis": "connected"
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "redis": "disconnected",
            "error": str(e)
        }), 503


@app.errorhandler(429)
def rate_limit_handler(e):
    """Custom handler for rate limit errors."""
    return jsonify({
        "error": "Rate limit exceeded",
        "message": "Too many requests. Please try again later."
    }), 429


if __name__ == "__main__":
    print("Starting Flask server with rate limiting...")
    print("Endpoints have individual rate limits")
    print("Visit http://localhost:5000 for available endpoints")
    app.run(host="0.0.0.0", port=5000, debug=True)
