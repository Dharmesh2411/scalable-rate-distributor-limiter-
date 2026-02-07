"""Test script for rate limiter functionality."""
import time
from rate_limiter import RateLimiter
from config import RateLimiterConfig


def test_basic_rate_limiting():
    """Test basic rate limiting functionality."""
    print("=" * 60)
    print("Test 1: Basic Rate Limiting")
    print("=" * 60)
    
    limiter = RateLimiter(RateLimiterConfig())
    identifier = "test_user_1"
    
    # Test with 5 requests per 10 seconds
    max_requests = 5
    window = 10
    
    print(f"\nLimit: {max_requests} requests per {window} seconds")
    print(f"Identifier: {identifier}\n")
    
    for i in range(7):
        is_allowed, metadata = limiter.is_allowed(identifier, max_requests, window)
        
        status = "✓ ALLOWED" if is_allowed else "✗ BLOCKED"
        print(f"Request {i+1}: {status}")
        print(f"  Remaining: {metadata['remaining']}/{metadata['limit']}")
        print(f"  Reset in: {metadata['reset'] - int(time.time())} seconds")
        
        if not is_allowed:
            print(f"  Retry after: {metadata['retry_after']} seconds")
        print()
        
        time.sleep(0.5)
    
    # Reset and verify
    print("Resetting rate limit...")
    limiter.reset(identifier)
    is_allowed, metadata = limiter.is_allowed(identifier, max_requests, window)
    print(f"After reset: {'✓ ALLOWED' if is_allowed else '✗ BLOCKED'}")
    print(f"Remaining: {metadata['remaining']}/{metadata['limit']}\n")
    
    limiter.close()


def test_sliding_window():
    """Test sliding window behavior."""
    print("=" * 60)
    print("Test 2: Sliding Window Algorithm")
    print("=" * 60)
    
    limiter = RateLimiter(RateLimiterConfig())
    identifier = "test_user_2"
    
    max_requests = 3
    window = 5
    
    print(f"\nLimit: {max_requests} requests per {window} seconds")
    print(f"Testing sliding window behavior...\n")
    
    # Make 3 requests (should all succeed)
    for i in range(3):
        is_allowed, _ = limiter.is_allowed(identifier, max_requests, window)
        print(f"Request {i+1}: {'✓ ALLOWED' if is_allowed else '✗ BLOCKED'}")
    
    # 4th request should fail
    is_allowed, _ = limiter.is_allowed(identifier, max_requests, window)
    print(f"Request 4: {'✓ ALLOWED' if is_allowed else '✗ BLOCKED'} (expected: BLOCKED)")
    
    # Wait for window to pass
    print(f"\nWaiting {window + 1} seconds for window to expire...")
    time.sleep(window + 1)
    
    # Should be allowed again
    is_allowed, metadata = limiter.is_allowed(identifier, max_requests, window)
    print(f"Request 5 (after window): {'✓ ALLOWED' if is_allowed else '✗ BLOCKED'} (expected: ALLOWED)")
    print(f"Remaining: {metadata['remaining']}/{metadata['limit']}\n")
    
    limiter.close()


def test_multiple_identifiers():
    """Test rate limiting with multiple identifiers."""
    print("=" * 60)
    print("Test 3: Multiple Identifiers")
    print("=" * 60)
    
    limiter = RateLimiter(RateLimiterConfig())
    
    max_requests = 3
    window = 10
    
    print(f"\nLimit: {max_requests} requests per {window} seconds")
    print("Testing independent rate limits for different users...\n")
    
    # User 1 makes 3 requests
    for i in range(3):
        is_allowed, _ = limiter.is_allowed("user_1", max_requests, window)
        print(f"User 1 - Request {i+1}: {'✓ ALLOWED' if is_allowed else '✗ BLOCKED'}")
    
    # User 1's 4th request should fail
    is_allowed, _ = limiter.is_allowed("user_1", max_requests, window)
    print(f"User 1 - Request 4: {'✓ ALLOWED' if is_allowed else '✗ BLOCKED'} (expected: BLOCKED)")
    
    print()
    
    # User 2 should still have full quota
    for i in range(3):
        is_allowed, metadata = limiter.is_allowed("user_2", max_requests, window)
        print(f"User 2 - Request {i+1}: {'✓ ALLOWED' if is_allowed else '✗ BLOCKED'}")
        print(f"  Remaining: {metadata['remaining']}/{metadata['limit']}")
    
    print("\n✓ Users have independent rate limits\n")
    
    limiter.close()


def test_usage_tracking():
    """Test usage tracking functionality."""
    print("=" * 60)
    print("Test 4: Usage Tracking")
    print("=" * 60)
    
    limiter = RateLimiter(RateLimiterConfig())
    identifier = "test_user_4"
    
    max_requests = 10
    window = 10
    
    print(f"\nLimit: {max_requests} requests per {window} seconds\n")
    
    # Make some requests
    for i in range(5):
        limiter.is_allowed(identifier, max_requests, window)
    
    # Check usage
    usage = limiter.get_usage(identifier, window)
    print(f"Current usage: {usage} requests")
    print(f"Expected: 5 requests")
    print(f"Match: {'✓ YES' if usage == 5 else '✗ NO'}\n")
    
    limiter.close()


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("REDIS RATE LIMITER TEST SUITE")
    print("=" * 60)
    print("\nMake sure Redis is running on localhost:6379")
    print("Press Enter to continue or Ctrl+C to cancel...")
    input()
    
    try:
        test_basic_rate_limiting()
        test_sliding_window()
        test_multiple_identifiers()
        test_usage_tracking()
        
        print("=" * 60)
        print("ALL TESTS COMPLETED SUCCESSFULLY! ✓")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Run FastAPI example: python example_fastapi.py")
        print("2. Run Flask example: python example_flask.py")
        print("3. Test with curl or browser")
        print()
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        print("\nMake sure Redis is running:")
        print("  docker run -d -p 6379:6379 redis:latest")
        print("  OR install Redis locally")


if __name__ == "__main__":
    main()
