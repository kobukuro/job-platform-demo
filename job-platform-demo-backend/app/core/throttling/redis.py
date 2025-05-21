from typing import Optional
from ninja.throttling import BaseThrottle
import redis
from django.conf import settings
from datetime import datetime
from django.http import HttpRequest

redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD,
    decode_responses=True,
    socket_timeout=5,
    retry_on_timeout=True,
    ssl=settings.REDIS_SSL if hasattr(settings, 'REDIS_SSL') else False
)


class RedisThrottle(BaseThrottle):
    """
    Redis-based throttling implementation for Django Ninja.
    Supports rate limiting based on various time periods (second, minute, hour, day).

    Usage:
        @router.post("", throttle_classes=[RedisThrottle("100/hour")])
        def my_endpoint(request):
            ...
    """

    def __init__(self, rate: str):
        """
        Initialize the throttle with a rate string.

        Args:
            rate (str): Rate string in format "number/period" (e.g., "100/hour")

        Raises:
            ValueError: If the rate string format is invalid
        """
        try:
            num, period = rate.split('/')
            self.num_requests = int(num)
            self.period = period.lower()

            # Convert period to seconds
            self.period_seconds = {
                'second': 1,
                'minute': 60,
                'hour': 3600,
                'day': 86400,
                'week': 604800,
                'month': 2592000,  # 30 days
            }.get(self.period)

            if self.period_seconds is None:
                raise ValueError(f"Invalid period: {period}")

        except ValueError as e:
            raise ValueError(f"Invalid rate format. Expected 'number/period', got '{rate}'. {str(e)}")

    def get_cache_key(self, request: HttpRequest, key: Optional[str] = None) -> str:
        """
        Generate a unique cache key for the request.

        Args:
            request: The HTTP request object
            key: Optional custom key

        Returns:
            str: Cache key for Redis
        """
        if key is None:
            key = self.get_client_ip(request)
        return f"throttle:{key}:{self.period}:{self._get_time_window()}"

    def _get_time_window(self) -> int:
        """
        Get the current time window for the rate limit.

        Returns:
            int: Current time window in seconds
        """
        now = datetime.now().timestamp()
        window = int(now / self.period_seconds) * self.period_seconds
        return window

    def allow_request(self, request: HttpRequest, key: Optional[str] = None) -> bool:
        """
        Check if the request should be allowed based on the rate limit.

        Args:
            request: The HTTP request object
            key: Optional custom key

        Returns:
            bool: True if request is allowed, False otherwise
        """
        cache_key = self.get_cache_key(request, key)

        try:
            current = redis_client.get(cache_key)

            if current is None:
                # First request, set count to 1
                redis_client.setex(cache_key, self.period_seconds, 1)
                return True

            current = int(current)
            if current >= self.num_requests:
                return False

            # Increment count
            redis_client.incr(cache_key)
            return True

        except redis.RedisError as e:
            # Log the error here if you have logging configured
            print(f"Redis error: {e}")
            # In case of Redis errors, we'll allow the request to prevent blocking users
            return True

    def get_client_ip(self, request: HttpRequest) -> str:
        """
        Get the client IP address from the request.

        Args:
            request: The HTTP request object

        Returns:
            str: Client IP address
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Get the first IP in case of multiple proxies
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')

    def wait(self) -> Optional[int]:
        """
        Get the number of seconds to wait before the next request is allowed.

        Returns:
            Optional[int]: Number of seconds to wait, or None if no waiting is needed
        """
        current_window = self._get_time_window()
        return current_window + self.period_seconds - datetime.now().timestamp()
