"""Database repositories."""
from src.database.repositories.user_repo import user_repo
from src.database.repositories.download_repo import download_repo
from src.database.repositories.favorite_repo import favorite_repo
from src.database.repositories.stats_repo import stats_repo

__all__ = ["user_repo", "download_repo", "favorite_repo", "stats_repo"]
