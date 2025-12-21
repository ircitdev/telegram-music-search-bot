"""User repository for database operations."""
import secrets
from datetime import datetime
from typing import Optional, List, Dict, Any
from src.database.connection import db
from src.utils.logger import logger


class UserRepository:
    """Repository for user-related database operations."""

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        row = await db.fetchone(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        )
        return dict(row) if row else None

    async def create_user(
        self,
        user_id: int,
        username: str = None,
        first_name: str = None,
        referrer_id: int = None
    ) -> bool:
        """Create new user or update existing. Returns True if user is new."""
        referral_code = secrets.token_urlsafe(8)

        try:
            # Check if user exists
            existing = await self.get_user(user_id)
            is_new = existing is None

            await db.execute("""
                INSERT INTO users (id, username, first_name, referral_code, referred_by, last_seen)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    username = excluded.username,
                    first_name = excluded.first_name,
                    last_seen = excluded.last_seen
            """, (user_id, username, first_name, referral_code, referrer_id, datetime.now()))

            # Create referral relationship if new user and has referrer
            if is_new and referrer_id and referrer_id != user_id:
                await db.execute("""
                    INSERT INTO referrals (referrer_id, referred_id)
                    VALUES (?, ?)
                """, (referrer_id, user_id))

            await db.commit()
            return is_new
        except Exception as e:
            logger.error(f"Error creating user {user_id}: {e}")
            return False

    async def update_last_seen(self, user_id: int):
        """Update user's last seen timestamp."""
        await db.execute(
            "UPDATE users SET last_seen = ? WHERE id = ?",
            (datetime.now(), user_id)
        )
        await db.commit()

    async def increment_searches(self, user_id: int):
        """Increment user's search count."""
        await db.execute(
            "UPDATE users SET searches = searches + 1 WHERE id = ?",
            (user_id,)
        )
        await db.commit()

    async def increment_downloads(self, user_id: int):
        """Increment user's download count."""
        await db.execute(
            "UPDATE users SET downloads = downloads + 1 WHERE id = ?",
            (user_id,)
        )
        await db.commit()

    async def get_user_count(self) -> int:
        """Get total user count."""
        row = await db.fetchone("SELECT COUNT(*) as cnt FROM users")
        return row["cnt"] if row else 0

    async def get_all_user_ids(self) -> List[int]:
        """Get all user IDs for mailing."""
        rows = await db.fetchall("SELECT id FROM users")
        return [row["id"] for row in rows]

    async def get_active_users(self, minutes: int = 60) -> int:
        """Get count of users active in last N minutes."""
        row = await db.fetchone("""
            SELECT COUNT(*) as cnt FROM users
            WHERE last_seen > datetime('now', ? || ' minutes')
        """, (f"-{minutes}",))
        return row["cnt"] if row else 0

    async def get_top_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top users by downloads."""
        rows = await db.fetchall("""
            SELECT id, username, first_name, searches, downloads, last_seen
            FROM users
            ORDER BY downloads DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in rows]

    async def is_premium(self, user_id: int) -> bool:
        """Check if user has active premium."""
        row = await db.fetchone("""
            SELECT is_premium, premium_until FROM users WHERE id = ?
        """, (user_id,))
        if not row:
            return False
        if not row["is_premium"]:
            return False
        if row["premium_until"]:
            return datetime.fromisoformat(row["premium_until"]) > datetime.now()
        return True

    async def set_premium(self, user_id: int, is_premium: bool = True, premium_until: datetime = None):
        """Set user premium status."""
        await db.execute("""
            UPDATE users SET is_premium = ?, premium_until = ? WHERE id = ?
        """, (1 if is_premium else 0, premium_until, user_id))
        await db.commit()

    async def log_payment(
        self,
        user_id: int,
        amount: int,
        currency: str,
        payment_type: str,
        payload: str
    ):
        """Log a payment to database."""
        try:
            await db.execute("""
                INSERT INTO payments (user_id, amount, currency, payment_type, payload, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, amount, currency, payment_type, payload, datetime.now()))
            await db.commit()
            logger.info(f"Payment logged: user={user_id}, amount={amount}, type={payment_type}")
        except Exception as e:
            logger.error(f"Error logging payment: {e}")

    async def get_by_referral_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Get user by referral code."""
        row = await db.fetchone(
            "SELECT * FROM users WHERE referral_code = ?",
            (code,)
        )
        return dict(row) if row else None

    async def set_referred_by(self, user_id: int, referrer_id: int):
        """Set who referred this user."""
        await db.execute(
            "UPDATE users SET referred_by = ? WHERE id = ?",
            (referrer_id, user_id)
        )
        await db.commit()

    async def add_bonus_downloads(self, user_id: int, count: int):
        """Add bonus downloads to user."""
        await db.execute(
            "UPDATE users SET bonus_downloads = bonus_downloads + ? WHERE id = ?",
            (count, user_id)
        )
        await db.commit()

    async def get_bonus_downloads(self, user_id: int) -> int:
        """Get user's bonus downloads."""
        row = await db.fetchone(
            "SELECT bonus_downloads FROM users WHERE id = ?",
            (user_id,)
        )
        return row["bonus_downloads"] if row else 0

    async def use_bonus_download(self, user_id: int) -> bool:
        """Use one bonus download. Returns True if successful."""
        result = await db.execute("""
            UPDATE users SET bonus_downloads = bonus_downloads - 1
            WHERE id = ? AND bonus_downloads > 0
        """, (user_id,))
        await db.commit()
        return result.rowcount > 0

    async def get_referral_count(self, user_id: int) -> int:
        """Get count of users referred by this user."""
        row = await db.fetchone(
            "SELECT COUNT(*) as cnt FROM users WHERE referred_by = ?",
            (user_id,)
        )
        return row["cnt"] if row else 0

    async def get_active_referral_count(self, user_id: int) -> int:
        """Get count of active referrals (those who made downloads)."""
        row = await db.fetchone(
            "SELECT COUNT(*) as cnt FROM referrals WHERE referrer_id = ? AND is_active = 1",
            (user_id,)
        )
        return row["cnt"] if row else 0

    async def get_stats_summary(self) -> Dict[str, Any]:
        """Get overall statistics."""
        row = await db.fetchone("""
            SELECT
                COUNT(*) as total_users,
                SUM(searches) as total_searches,
                SUM(downloads) as total_downloads
            FROM users
        """)
        return dict(row) if row else {}

    async def get_user_language(self, user_id: int) -> str:
        """Get user's preferred language."""
        row = await db.fetchone(
            "SELECT language FROM users WHERE id = ?",
            (user_id,)
        )
        return row["language"] if row and row["language"] else "ru"

    async def set_user_language(self, user_id: int, language: str):
        """Set user's preferred language."""
        await db.execute(
            "UPDATE users SET language = ? WHERE id = ?",
            (language, user_id)
        )
        await db.commit()
        logger.info(f"User {user_id} set language to {language}")


# Global instance
user_repo = UserRepository()
