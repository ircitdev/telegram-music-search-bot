"""User management - tracking users who started the bot."""
from datetime import datetime
from typing import Set, List, Dict
import logging

logger = logging.getLogger(__name__)


class UserManager:
    """Manage users who have interacted with the bot."""

    def __init__(self):
        """Initialize user manager."""
        self.users: Set[int] = set()
        self.user_info: Dict[int, Dict] = {}

    def add_user(self, user_id: int, username: str = "", first_name: str = "") -> bool:
        """
        Add a user.

        Args:
            user_id: Telegram user ID
            username: Username (without @)
            first_name: First name

        Returns:
            True if user was added, False if already exists
        """
        is_new = user_id not in self.users

        if is_new:
            self.users.add(user_id)
            logger.info(f"New user added: {user_id} (@{username})")
        else:
            logger.debug(f"User already exists: {user_id}")

        # Always update info
        self.user_info[user_id] = {
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "joined_at": self.user_info.get(user_id, {}).get("joined_at", datetime.now()),
            "last_seen": datetime.now(),
        }

        return is_new

    def remove_user(self, user_id: int) -> bool:
        """Remove a user."""
        if user_id in self.users:
            self.users.discard(user_id)
            if user_id in self.user_info:
                del self.user_info[user_id]
            logger.info(f"User removed: {user_id}")
            return True
        return False

    def get_user_count(self) -> int:
        """Get total number of users."""
        return len(self.users)

    def get_all_users(self) -> List[int]:
        """Get list of all user IDs."""
        return list(self.users)

    def user_exists(self, user_id: int) -> bool:
        """Check if user exists."""
        return user_id in self.users

    def get_user_info(self, user_id: int) -> Dict:
        """Get user info."""
        return self.user_info.get(user_id, {})

    def get_all_user_info(self) -> List[Dict]:
        """Get info for all users."""
        return list(self.user_info.values())

    def reset(self) -> None:
        """Reset all users."""
        self.users.clear()
        self.user_info.clear()
        logger.info("User manager reset")


# Global user manager instance
user_manager = UserManager()
