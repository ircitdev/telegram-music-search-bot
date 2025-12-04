"""YouTube downloader module for MP3 files."""
import os
import asyncio
from pathlib import Path
from yt_dlp import YoutubeDL
from src.config import settings
from src.utils.logger import logger


class YouTubeDownloader:
    """Download tracks from YouTube and convert to MP3."""

    def __init__(self):
        """Initialize YouTubeDownloader."""
        Path(settings.TEMP_DIR).mkdir(parents=True, exist_ok=True)

        self.ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{settings.TEMP_DIR}/%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

    async def download(self, video_id: str) -> str:
        """
        Download track from YouTube and convert to MP3.

        Args:
            video_id: YouTube video ID

        Returns:
            Path to downloaded MP3 file

        Raises:
            Exception: If download fails or file too large
        """
        try:
            logger.info(f"Starting download for video: {video_id}")

            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            file_path = await loop.run_in_executor(
                None, self._download_sync, video_id
            )

            logger.info(f"Successfully downloaded: {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"Download error for {video_id}: {e}")
            raise

    def _download_sync(self, video_id: str) -> str:
        """Synchronous download (runs in executor)."""
        try:
            url = f"https://youtube.com/watch?v={video_id}"
            logger.info(f"Downloading from: {url}")

            with YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

                # Get filename
                filename = ydl.prepare_filename(info)
                mp3_file = filename.rsplit('.', 1)[0] + '.mp3'

                # Check if file exists
                if not os.path.exists(mp3_file):
                    raise Exception("MP3 file was not created")

                # Check file size
                file_size = os.path.getsize(mp3_file)
                logger.info(f"Downloaded file size: {file_size} bytes")

                if file_size > settings.MAX_FILE_SIZE:
                    os.remove(mp3_file)
                    raise Exception(
                        f"File too large: {file_size} bytes "
                        f"(limit: {settings.MAX_FILE_SIZE})"
                    )

                logger.info(f"Download complete: {mp3_file}")
                return mp3_file

        except Exception as e:
            logger.error(f"Download sync error: {e}")
            raise


# Singleton instance
youtube_downloader = YouTubeDownloader()
