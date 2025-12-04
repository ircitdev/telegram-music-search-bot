"""Bot statistics tracking - User searches, downloads, active users."""
from datetime import datetime, timedelta
from typing import Dict, Set, List, Tuple
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class UserStats:
    """User statistics."""
    user_id: int
    username: str = ""
    searches: int = 0
    downloads: int = 0
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)

    def update_search(self):
        """Record a search action."""
        self.searches += 1
        self.last_seen = datetime.now()

    def update_download(self):
        """Record a download action."""
        self.downloads += 1
        self.last_seen = datetime.now()

    def get_uptime(self) -> str:
        """Get user uptime formatted."""
        delta = datetime.now() - self.first_seen
        days = delta.days
        hours = (delta.seconds // 3600)
        return f"{days}d {hours}h" if days > 0 else f"{hours}h"


class BotStats:
    """Bot statistics tracker."""

    def __init__(self):
        """Initialize stats tracker."""
        self.users: Dict[int, UserStats] = {}
        self.total_searches: int = 0
        self.total_downloads: int = 0
        self.start_time: datetime = datetime.now()

    def record_search(self, user_id: int, username: str = "") -> None:
        """Record a user search."""
        if user_id not in self.users:
            self.users[user_id] = UserStats(user_id=user_id, username=username)
        else:
            if username:
                self.users[user_id].username = username

        self.users[user_id].update_search()
        self.total_searches += 1

        logger.debug(
            f"Recorded search for user {user_id}: "
            f"{self.users[user_id].searches} total"
        )

    def record_download(self, user_id: int, username: str = "") -> None:
        """Record a user download."""
        if user_id not in self.users:
            self.users[user_id] = UserStats(user_id=user_id, username=username)
        else:
            if username:
                self.users[user_id].username = username

        self.users[user_id].update_download()
        self.total_downloads += 1

        logger.debug(
            f"Recorded download for user {user_id}: "
            f"{self.users[user_id].downloads} total"
        )

    def get_user_count(self) -> int:
        """Get total unique users."""
        return len(self.users)

    def get_active_users(self, minutes: int = 60) -> int:
        """Get users active in last N minutes."""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        return sum(1 for u in self.users.values() if u.last_seen > cutoff)

    def get_top_users(self, limit: int = 10) -> List[UserStats]:
        """Get top users by downloads."""
        sorted_users = sorted(
            self.users.values(),
            key=lambda u: u.downloads,
            reverse=True
        )
        return sorted_users[:limit]

    def get_bot_uptime(self) -> str:
        """Get bot uptime formatted."""
        delta = datetime.now() - self.start_time
        days = delta.days
        hours = (delta.seconds // 3600) % 24
        minutes = (delta.seconds // 60) % 60
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

    def get_stats_text(self) -> str:
        """Get formatted stats text."""
        uptime = self.get_bot_uptime()
        active = self.get_active_users(minutes=60)
        avg_downloads = (
            self.total_downloads / self.get_user_count()
            if self.get_user_count() > 0
            else 0
        )

        text = (
            "📊 <b>СТАТИСТИКА БОТА</b>\n\n"
            f"⏱ <b>Время работы:</b> {uptime}\n"
            f"👥 <b>Всего пользователей:</b> {self.get_user_count()}\n"
            f"🟢 <b>Активных (60 мин):</b> {active}\n"
            f"🔍 <b>Всего поисков:</b> {self.total_searches}\n"
            f"⬇️ <b>Всего скачиваний:</b> {self.total_downloads}\n"
            f"📈 <b>Avg скачиваний/пользователя:</b> {avg_downloads:.1f}\n"
        )

        return text

    def get_user_stats(self, user_id: int) -> str:
        """Get formatted stats for specific user."""
        if user_id not in self.users:
            return "❌ Пользователь не найден"

        user = self.users[user_id]
        uptime = user.get_uptime()

        text = (
            f"👤 <b>Статистика пользователя {user.user_id}</b>\n\n"
            f"📝 <b>Юзернейм:</b> @{user.username or 'не указан'}\n"
            f"🔍 <b>Поисков:</b> {user.searches}\n"
            f"⬇️ <b>Скачиваний:</b> {user.downloads}\n"
            f"⏱ <b>Активен:</b> {uptime}\n"
            f"🕐 <b>Первый визит:</b> {user.first_seen.strftime('%Y-%m-%d %H:%M')}\n"
            f"⏰ <b>Последний визит:</b> {user.last_seen.strftime('%Y-%m-%d %H:%M')}\n"
        )

        return text

    def get_top_users_text(self, limit: int = 10) -> str:
        """Get formatted top users text."""
        top = self.get_top_users(limit)

        if not top:
            return "❌ Нет данных"

        text = f"🏆 <b>ТОП {limit} ПОЛЬЗОВАТЕЛЕЙ ПО СКАЧИВАНИЯМ</b>\n\n"

        for i, user in enumerate(top, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            text += (
                f"{medal} @{user.username or f'user_{user.user_id}'}\n"
                f"   ⬇️ {user.downloads} скачиваний | 🔍 {user.searches} поисков\n\n"
            )

        return text

    def reset(self) -> None:
        """Reset all stats."""
        self.users.clear()
        self.total_searches = 0
        self.total_downloads = 0
        self.start_time = datetime.now()
        logger.info("Stats reset")

    def get_summary(self) -> Dict:
        """Get stats summary as dict."""
        return {
            "total_users": self.get_user_count(),
            "active_users": self.get_active_users(minutes=60),
            "total_searches": self.total_searches,
            "total_downloads": self.total_downloads,
            "bot_uptime": self.get_bot_uptime(),
            "avg_downloads_per_user": (
                self.total_downloads / self.get_user_count()
                if self.get_user_count() > 0
                else 0
            ),
        }


# Global stats instance
bot_stats = BotStats()
