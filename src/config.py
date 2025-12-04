"""Configuration module - loads settings from .env file."""
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    # Telegram Bot
    BOT_TOKEN: str
    BOT_USERNAME: str = "UspMusicFinder_bot"

    # Directories
    TEMP_DIR: str = "./data/temp"
    CACHE_DIR: str = "./data/cache"
    LOGS_DIR: str = "./logs"
    DATABASE_PATH: str = "./data/database.db"

    # File size and duration limits
    MAX_FILE_SIZE: int = 52428800  # 50MB (Telegram limit)
    MAX_DURATION: int = 600  # 10 minutes

    # Logging
    LOG_LEVEL: str = "INFO"

    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 5
    RATE_LIMIT_PERIOD: int = 60

    # Features
    ENABLE_CACHE: bool = True
    ENABLE_STATS: bool = True
    ENABLE_INLINE: bool = True

    # APIs (optional)
    LASTFM_API_KEY: str = ""
    AUDD_API_KEY: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Create necessary directories
Path(settings.TEMP_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.CACHE_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.LOGS_DIR).mkdir(parents=True, exist_ok=True)
