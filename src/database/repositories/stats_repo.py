"""Track statistics repository."""
from datetime import datetime
from typing import List, Dict, Any
from src.database.connection import db
from src.utils.logger import logger


class StatsRepository:
    """Repository for track statistics."""

    async def record_download(
        self,
        track_id: str,
        title: str,
        artist: str = None
    ):
        """Record/increment track download count."""
        try:
            await db.execute("""
                INSERT INTO track_stats (track_id, title, artist, download_count, last_downloaded)
                VALUES (?, ?, ?, 1, ?)
                ON CONFLICT(track_id) DO UPDATE SET
                    download_count = download_count + 1,
                    last_downloaded = excluded.last_downloaded
            """, (track_id, title, artist, datetime.now()))
            await db.commit()
        except Exception as e:
            logger.error(f"Error recording track stats: {e}")

    async def get_top_tracks(
        self,
        limit: int = 20,
        period: str = "all"
    ) -> List[Dict[str, Any]]:
        """
        Get top downloaded tracks.

        Args:
            limit: Number of tracks to return
            period: "day", "week", "month", or "all"
        """
        if period == "all":
            # Get from track_stats (all time)
            rows = await db.fetchall("""
                SELECT track_id, title, artist, download_count, last_downloaded
                FROM track_stats
                ORDER BY download_count DESC
                LIMIT ?
            """, (limit,))
        else:
            # Count from downloads table for specific period
            if period == "day":
                date_filter = "datetime('now', '-1 day')"
            elif period == "week":
                date_filter = "datetime('now', '-7 days')"
            elif period == "month":
                date_filter = "datetime('now', '-30 days')"
            else:
                date_filter = "datetime('now', '-1 day')"

            rows = await db.fetchall(f"""
                SELECT
                    track_id,
                    title,
                    artist,
                    duration,
                    COUNT(*) as download_count,
                    MAX(downloaded_at) as last_downloaded
                FROM downloads
                WHERE downloaded_at > {date_filter}
                GROUP BY track_id
                ORDER BY download_count DESC
                LIMIT ?
            """, (limit,))

        return [dict(row) for row in rows]

    async def get_track_stats(self, track_id: str) -> Dict[str, Any]:
        """Get stats for a specific track."""
        row = await db.fetchone(
            "SELECT * FROM track_stats WHERE track_id = ?",
            (track_id,)
        )
        return dict(row) if row else None

    async def get_recommendations(
        self,
        user_id: int,
        track_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get recommendations based on what other users downloaded.

        Finds users who downloaded the same track and returns
        other tracks they downloaded.
        """
        rows = await db.fetchall("""
            SELECT
                d.track_id,
                d.title,
                d.artist,
                d.duration,
                COUNT(*) as popularity
            FROM downloads d
            WHERE d.user_id IN (
                SELECT DISTINCT user_id FROM downloads
                WHERE track_id = ? AND user_id != ?
            )
            AND d.track_id != ?
            GROUP BY d.track_id
            ORDER BY popularity DESC
            LIMIT ?
        """, (track_id, user_id, track_id, limit))
        return [dict(row) for row in rows]

    async def get_total_unique_tracks(self) -> int:
        """Get count of unique tracks downloaded."""
        row = await db.fetchone("SELECT COUNT(*) as cnt FROM track_stats")
        return row["cnt"] if row else 0

    async def get_tracks_by_artist(self, artist: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get popular tracks by specific artist."""
        rows = await db.fetchall("""
            SELECT track_id, title, artist, download_count, last_downloaded
            FROM track_stats
            WHERE artist LIKE ?
            ORDER BY download_count DESC
            LIMIT ?
        """, (f"%{artist}%", limit))
        return [dict(row) for row in rows]


# Global instance
stats_repo = StatsRepository()
