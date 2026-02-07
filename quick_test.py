"""Quick start script to test rate limiting with curl."""
import subprocess
import sys
import time


def test_endpoint(url, num_requests=15, endpoint_name="endpoint"):
    """Test an endpoint with multiple requests."""
    print(f"\n{'=' * 60}")
    print(f"Testing {endpoint_name}: {url}")
    print(f"Making {num_requests} requests...")
    print('=' * 60)
    
    for i in range(num_requests):
        try:
            result = subprocess.run(
                ['curl', '-s', '-w', '\\nHTTP Status: %{http_code}\\n', url],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            print(f"\nRequest {i+1}:")
            print(result.stdout)
            
            # Check for rate limit headers in stderr (curl -i output)
            if '429' in result.stdout:
                print("⚠️  RATE LIMITED!")
                
        except subprocess.TimeoutExpired:
            print(f"Request {i+1}: Timeout")
        except FileNotFoundError:
            print("Error: curl not found. Please install curl.")
            return
        
        time.sleep(0.3)


def main():
    """Run quick tests."""
    print("\n" + "=" * 60)
    print("RATE LIMITER QUICK TEST")
    print("=" * 60)
    
    print("\nThis script will test the rate limiter endpoints.")
    print("Make sure either FastAPI or Flask server is running:")
    print("  FastAPI: python example_fastapi.py")
    print("  Flask:   python example_flask.py")
    
    choice = input("\nWhich server are you testing? (fastapi/flask): ").lower()
    
    if choice == 'fastapi':
        base_url = "http://localhost:8000"
        endpoints = [
            (f"{base_url}/api/strict", "Strict Endpoint (10 req/min)"),
            (f"{base_url}/api/public", "Public Endpoint (100 req/min)")
        ]
    elif choice == 'flask':
        base_url = "http://localhost:5000"
        endpoints = [
            (f"{base_url}/api/strict", "Strict Endpoint (10 req/min)"),
            (f"{base_url}/api/public", "Public Endpoint (100 req/min)")
        ]
    else:
        print("Invalid choice. Exiting.")
        return
    
    for url, name in endpoints:
        test_endpoint(url, num_requests=15, endpoint_name=name)
        
        if input("\nContinue to next test? (y/n): ").lower() != 'y':
            break
    
    print("\n" + "=" * 60)
    print("TESTING COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
