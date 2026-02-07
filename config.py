"""Configuration management for API Rate Limiter."""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class RateLimiterConfig:
    """Configuration class for rate limiter settings."""
    
    def __init__(
        self,
        redis_host: Optional[str] = None,
        redis_port: Optional[int] = None,
        redis_db: Optional[int] = None,
        redis_password: Optional[str] = None,
        default_requests: Optional[int] = None,
        default_window: Optional[int] = None,
    ):
        """
        Initialize rate limiter configuration.
        
        Args:
            redis_host: Redis server host
            redis_port: Redis server port
            redis_db: Redis database number
            redis_password: Redis password (optional)
            default_requests: Default number of requests allowed
            default_window: Default time window in seconds
        """
        self.redis_host = redis_host or os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(redis_port or os.getenv("REDIS_PORT", 6379))
        self.redis_db = int(redis_db or os.getenv("REDIS_DB", 0))
        self.redis_password = redis_password or os.getenv("REDIS_PASSWORD", None)
        self.default_requests = int(default_requests or os.getenv("RATE_LIMIT_REQUESTS", 100))
        self.default_window = int(default_window or os.getenv("RATE_LIMIT_WINDOW", 60))
    
    def get_redis_url(self) -> str:
        """Generate Redis connection URL."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
