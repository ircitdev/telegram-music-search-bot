"""Rate limiter for controlling user requests - Day 7."""
from datetime import datetime, timedelta
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter with per-user request tracking."""

    def __init__(self, max_requests: int = 5, time_window: int = 60):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = timedelta(seconds=time_window)
        self.requests: Dict[int, list] = {}

    def is_allowed(self, user_id: int) -> Tuple[bool, int]:
        """
        Check if user is allowed to make a request.

        Args:
            user_id: Telegram user ID

        Returns:
            Tuple (allowed: bool, wait_seconds: int)
            - allowed: True if request is allowed
            - wait_seconds: Seconds to wait if not allowed (0 if allowed)
        """
        now = datetime.now()

        # Initialize user if not exists
        if user_id not in self.requests:
            self.requests[user_id] = []

        # Remove old requests outside time window
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if now - req_time < self.time_window
        ]

        # Check if allowed
        if len(self.requests[user_id]) < self.max_requests:
            self.requests[user_id].append(now)
            
            logger.info(
                f"Rate limit check passed for user {user_id}: "
                f"{len(self.requests[user_id])}/{self.max_requests} requests"
            )
            return True, 0

        # Not allowed - calculate wait time
        oldest_request = self.requests[user_id][0]
        wait_until = oldest_request + self.time_window
        wait_seconds = max(1, int((wait_until - now).total_seconds()))

        logger.warning(
            f"Rate limit exceeded for user {user_id}: "
            f"Wait {wait_seconds} seconds"
        )
        return False, wait_seconds

    def reset_user(self, user_id: int) -> None:
        """Reset rate limit for specific user."""
        if user_id in self.requests:
            del self.requests[user_id]
            logger.info(f"Rate limit reset for user {user_id}")

    def clear_all(self) -> None:
        """Clear all rate limit data."""
        self.requests.clear()
        logger.info("All rate limits cleared")

    def get_stats(self, user_id: int) -> Dict:
        """Get rate limit stats for user."""
        if user_id not in self.requests:
            return {
                "user_id": user_id,
                "requests": 0,
                "max_requests": self.max_requests,
                "allowed": True
            }

        now = datetime.now()
        # Remove old requests
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if now - req_time < self.time_window
        ]

        request_count = len(self.requests[user_id])
        allowed, wait_seconds = self.is_allowed(user_id)

        return {
            "user_id": user_id,
            "requests": request_count,
            "max_requests": self.max_requests,
            "time_window": self.time_window.total_seconds(),
            "allowed": allowed,
            "wait_seconds": wait_seconds
        }


# Global rate limiter instance
rate_limiter = RateLimiter(max_requests=5, time_window=60)
