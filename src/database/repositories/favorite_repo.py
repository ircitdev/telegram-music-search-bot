"""Favorites repository."""
from typing import List, Dict, Any
from src.database.connection import db
from src.utils.logger import logger


class FavoriteRepository:
    """Repository for favorites operations."""

    async def add_favorite(
        self,
        user_id: int,
        track_id: str,
        title: str,
        artist: str = None,
        duration: int = None
    ) -> bool:
        """Add track to favorites. Returns False if already exists."""
        try:
            await db.execute("""
                INSERT INTO favorites (user_id, track_id, title, artist, duration)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, track_id, title, artist, duration))
            await db.commit()
            return True
        except Exception as e:
            # UNIQUE constraint violation = already in favorites
            if "UNIQUE" in str(e):
                return False
            logger.error(f"Error adding favorite: {e}")
            return False

    async def remove_favorite(self, user_id: int, track_id: str) -> bool:
        """Remove track from favorites."""
        result = await db.execute("""
            DELETE FROM favorites WHERE user_id = ? AND track_id = ?
        """, (user_id, track_id))
        await db.commit()
        return result.rowcount > 0

    async def get_favorites(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get user's favorites."""
        rows = await db.fetchall("""
            SELECT track_id, title, artist, duration, added_at
            FROM favorites
            WHERE user_id = ?
            ORDER BY added_at DESC
            LIMIT ? OFFSET ?
        """, (user_id, limit, offset))
        return [dict(row) for row in rows]

    async def is_favorite(self, user_id: int, track_id: str) -> bool:
        """Check if track is in user's favorites."""
        row = await db.fetchone("""
            SELECT id FROM favorites
            WHERE user_id = ? AND track_id = ?
        """, (user_id, track_id))
        return row is not None

    async def get_favorites_count(self, user_id: int) -> int:
        """Get count of user's favorites."""
        row = await db.fetchone(
            "SELECT COUNT(*) as cnt FROM favorites WHERE user_id = ?",
            (user_id,)
        )
        return row["cnt"] if row else 0

    async def toggle_favorite(
        self,
        user_id: int,
        track_id: str,
        title: str,
        artist: str = None,
        duration: int = None
    ) -> bool:
        """Toggle favorite status. Returns True if added, False if removed."""
        if await self.is_favorite(user_id, track_id):
            await self.remove_favorite(user_id, track_id)
            return False
        else:
            await self.add_favorite(user_id, track_id, title, artist, duration)
            return True


# Global instance
favorite_repo = FavoriteRepository()
