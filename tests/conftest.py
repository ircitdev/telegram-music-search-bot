"""Pytest configuration and fixtures."""
import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment
os.environ.setdefault("BOT_TOKEN", "test:token")
os.environ.setdefault("ADMIN_IDS", "123456789")
os.environ.setdefault("DATA_DIR", "/tmp/test_data")
os.environ.setdefault("TEMP_DIR", "/tmp/test_temp")
os.environ.setdefault("CACHE_DIR", "/tmp/test_cache")
os.environ.setdefault("LOGS_DIR", "/tmp/test_logs")


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_message():
    """Create a mock Telegram message."""
    message = MagicMock()
    message.from_user = MagicMock()
    message.from_user.id = 123456789
    message.from_user.username = "testuser"
    message.from_user.first_name = "Test"
    message.from_user.language_code = "ru"
    message.chat = MagicMock()
    message.chat.id = 123456789
    message.chat.type = "private"
    message.text = "/start"
    message.answer = AsyncMock()
    message.reply = AsyncMock()
    return message


@pytest.fixture
def mock_callback():
    """Create a mock callback query."""
    callback = MagicMock()
    callback.from_user = MagicMock()
    callback.from_user.id = 123456789
    callback.from_user.username = "testuser"
    callback.message = MagicMock()
    callback.message.chat = MagicMock()
    callback.message.chat.id = 123456789
    callback.message.edit_text = AsyncMock()
    callback.message.delete = AsyncMock()
    callback.answer = AsyncMock()
    callback.data = "test_callback"
    return callback


@pytest.fixture
def mock_bot():
    """Create a mock bot instance."""
    bot = MagicMock()
    bot.send_message = AsyncMock()
    bot.send_audio = AsyncMock()
    bot.send_document = AsyncMock()
    bot.send_invoice = AsyncMock()
    bot.download = AsyncMock()
    return bot


@pytest.fixture
async def test_db(tmp_path):
    """Create a test database."""
    import aiosqlite

    db_path = tmp_path / "test.db"

    async with aiosqlite.connect(str(db_path)) as db:
        await db.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                is_premium INTEGER DEFAULT 0,
                premium_until TEXT,
                downloads INTEGER DEFAULT 0,
                searches INTEGER DEFAULT 0,
                bonus_downloads INTEGER DEFAULT 0,
                referred_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_seen TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                video_id TEXT,
                title TEXT,
                artist TEXT,
                downloaded_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                currency TEXT,
                payment_type TEXT,
                payload TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

    yield str(db_path)
