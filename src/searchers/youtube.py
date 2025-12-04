"""YouTube Music searcher module."""
import asyncio
from typing import List
from yt_dlp import YoutubeDL
from src.models import Track
from src.utils.logger import logger


class YouTubeSearcher:
    """Search tracks on YouTube Music."""

    def __init__(self):
        """Initialize YouTubeSearcher."""
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'default_search': 'ytsearch10',
        }

    async def search(self, query: str) -> List[Track]:
        """
        Search for tracks on YouTube.

        Args:
            query: Search query (song title or artist name)

        Returns:
            List of Track objects (up to 10 results)
        """
        try:
            logger.info(f"Searching YouTube for: {query}")

            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._search_sync, query
            )

            return result

        except Exception as e:
            logger.error(f"YouTube search error for '{query}': {e}")
            return []

    def _search_sync(self, query: str) -> List[Track]:
        """Synchronous YouTube search (runs in executor)."""
        try:
            with YoutubeDL(self.ydl_opts) as ydl:
                result = ydl.extract_info(f"ytsearch10:{query}", download=False)

                if not result or 'entries' not in result:
                    logger.warning(f"No results found for: {query}")
                    return []

                tracks = []
                for entry in result['entries']:
                    if not entry:
                        continue

                    # Parse title (usually "Artist - Title" or just "Title")
                    title = entry.get('title', 'Unknown')
                    artist = "Unknown"

                    if ' - ' in title:
                        parts = title.split(' - ', 1)
                        artist = parts[0].strip()
                        title = parts[1].strip()

                    track = Track(
                        id=entry['id'],
                        title=title,
                        artist=artist,
                        duration=entry.get('duration', 0),
                        url=f"https://youtube.com/watch?v={entry['id']}"
                    )
                    tracks.append(track)

                logger.info(f"Found {len(tracks)} tracks for: {query}")
                return tracks[:10]

        except Exception as e:
            logger.error(f"YouTube search sync error: {e}")
            return []


# Singleton instance
youtube_searcher = YouTubeSearcher()
