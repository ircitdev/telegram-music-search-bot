"""Download history repository."""
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from src.database.connection import db
from src.utils.logger import logger


class DownloadRepository:
    """Repository for download history operations."""

    async def add_download(
        self,
        user_id: int,
        track_id: str,
        title: str,
        artist: str = None,
        duration: int = None
    ) -> bool:
        """Record a download."""
        try:
            await db.execute("""
                INSERT INTO downloads (user_id, track_id, title, artist, duration)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, track_id, title, artist, duration))
            await db.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding download: {e}")
            return False

    async def get_user_history(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get user's download history."""
        rows = await db.fetchall("""
            SELECT track_id, title, artist, duration, downloaded_at
            FROM downloads
            WHERE user_id = ?
            ORDER BY downloaded_at DESC
            LIMIT ? OFFSET ?
        """, (user_id, limit, offset))
        return [dict(row) for row in rows]

    async def get_today_count(self, user_id: int) -> int:
        """Get user's download count for today."""
        today = date.today().isoformat()
        row = await db.fetchone("""
            SELECT count FROM daily_downloads
            WHERE user_id = ? AND download_date = ?
        """, (user_id, today))
        return row["count"] if row else 0

    async def increment_daily_count(self, user_id: int) -> int:
        """Increment daily download count and return new value."""
        today = date.today().isoformat()
        await db.execute("""
            INSERT INTO daily_downloads (user_id, download_date, count)
            VALUES (?, ?, 1)
            ON CONFLICT(user_id, download_date) DO UPDATE SET
                count = count + 1
        """, (user_id, today))
        await db.commit()

        row = await db.fetchone("""
            SELECT count FROM daily_downloads
            WHERE user_id = ? AND download_date = ?
        """, (user_id, today))
        return row["count"] if row else 1

    async def get_user_download_count(self, user_id: int) -> int:
        """Get total download count for user."""
        row = await db.fetchone(
            "SELECT COUNT(*) as cnt FROM downloads WHERE user_id = ?",
            (user_id,)
        )
        return row["cnt"] if row else 0

    async def get_total_downloads(self) -> int:
        """Get total downloads across all users."""
        row = await db.fetchone("SELECT COUNT(*) as cnt FROM downloads")
        return row["cnt"] if row else 0

    async def user_has_downloaded(self, user_id: int, track_id: str) -> bool:
        """Check if user has downloaded this track before."""
        row = await db.fetchone("""
            SELECT id FROM downloads
            WHERE user_id = ? AND track_id = ?
            LIMIT 1
        """, (user_id, track_id))
        return row is not None

    async def cleanup_old_daily_counts(self, days: int = 7):
        """Remove daily count records older than N days."""
        await db.execute("""
            DELETE FROM daily_downloads
            WHERE download_date < date('now', ? || ' days')
        """, (f"-{days}",))
        await db.commit()


# Global instance
download_repo = DownloadRepository()
