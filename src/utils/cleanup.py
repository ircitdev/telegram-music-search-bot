"""File cleanup utility for removing old temporary files - Day 7."""
import asyncio
import os
from pathlib import Path
from datetime import datetime, timedelta
import logging

from src.config import settings

logger = logging.getLogger(__name__)


async def cleanup_old_files(max_age_seconds: int = 3600) -> int:
    """
    Remove files older than max_age_seconds from temp directory.

    Args:
        max_age_seconds: Maximum file age in seconds (default: 1 hour)

    Returns:
        Number of files deleted
    """
    temp_dir = Path(settings.TEMP_DIR)
    deleted_count = 0

    if not temp_dir.exists():
        logger.debug(f"Temp directory does not exist: {temp_dir}")
        return 0

    try:
        current_time = datetime.now()
        max_age = timedelta(seconds=max_age_seconds)

        for file_path in temp_dir.iterdir():
            if not file_path.is_file():
                continue

            try:
                # Get file modification time
                mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                age = current_time - mod_time

                if age > max_age:
                    try:
                        file_path.unlink()
                        file_size = file_path.stat().st_size if file_path.exists() else 0
                        logger.info(
                            f"Deleted old temp file: {file_path.name} "
                            f"(age: {age.total_seconds():.0f}s)"
                        )
                        deleted_count += 1
                    except Exception as e:
                        logger.error(f"Failed to delete {file_path.name}: {e}")

            except Exception as e:
                logger.error(f"Error processing {file_path.name}: {e}")
                continue

        if deleted_count > 0:
            logger.info(f"Cleanup complete: deleted {deleted_count} files")

    except Exception as e:
        logger.error(f"Cleanup failed: {e}")

    return deleted_count


async def cleanup_task(interval_seconds: int = 3600, max_age_seconds: int = 3600):
    """
    Background task for periodic file cleanup.

    Runs cleanup every interval_seconds.

    Args:
        interval_seconds: Cleanup interval in seconds (default: 1 hour)
        max_age_seconds: File age threshold in seconds (default: 1 hour)
    """
    logger.info(
        f"Starting cleanup task: interval={interval_seconds}s, "
        f"max_age={max_age_seconds}s"
    )

    while True:
        try:
            await asyncio.sleep(interval_seconds)
            deleted = await cleanup_old_files(max_age_seconds)
            if deleted > 0:
                logger.info(f"Cleanup task: removed {deleted} files")

        except asyncio.CancelledError:
            logger.info("Cleanup task cancelled")
            break
        except Exception as e:
            logger.error(f"Cleanup task error: {e}")
            await asyncio.sleep(60)  # Retry after 1 minute


def create_cleanup_task(
    interval_seconds: int = 3600,
    max_age_seconds: int = 3600
) -> asyncio.Task:
    """
    Create and return cleanup task.

    Args:
        interval_seconds: Cleanup interval in seconds
        max_age_seconds: File age threshold in seconds

    Returns:
        asyncio.Task that can be cancelled
    """
    return asyncio.create_task(cleanup_task(interval_seconds, max_age_seconds))
