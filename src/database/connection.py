"""Database connection and initialization."""
import aiosqlite
from pathlib import Path
from src.config import settings
from src.utils.logger import logger


class Database:
    """Async SQLite database manager."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection: aiosqlite.Connection = None

    async def connect(self):
        """Connect to database and create tables."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = await aiosqlite.connect(self.db_path)
        self.connection.row_factory = aiosqlite.Row
        await self._create_tables()
        logger.info(f"Database connected: {self.db_path}")

    async def disconnect(self):
        """Close database connection."""
        if self.connection:
            await self.connection.close()
            logger.info("Database disconnected")

    async def _create_tables(self):
        """Create all tables if not exist."""
        await self.connection.executescript("""
            -- Users table
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                is_premium INTEGER DEFAULT 0,
                premium_until TIMESTAMP,
                referral_code TEXT UNIQUE,
                referred_by INTEGER,
                bonus_downloads INTEGER DEFAULT 0,
                searches INTEGER DEFAULT 0,
                downloads INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Downloads history
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                track_id TEXT NOT NULL,
                title TEXT NOT NULL,
                artist TEXT,
                duration INTEGER,
                downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            -- Favorites
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                track_id TEXT NOT NULL,
                title TEXT NOT NULL,
                artist TEXT,
                duration INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, track_id)
            );

            -- Track statistics (for top charts)
            CREATE TABLE IF NOT EXISTS track_stats (
                track_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                artist TEXT,
                download_count INTEGER DEFAULT 0,
                last_downloaded TIMESTAMP
            );

            -- Daily downloads (for limits)
            CREATE TABLE IF NOT EXISTS daily_downloads (
                user_id INTEGER NOT NULL,
                download_date DATE NOT NULL,
                count INTEGER DEFAULT 1,
                UNIQUE(user_id, download_date)
            );

            -- Payments
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'RUB',
                payment_type TEXT,
                payment_system TEXT,
                status TEXT DEFAULT 'pending',
                external_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            -- Indexes for performance
            CREATE INDEX IF NOT EXISTS idx_downloads_user_id ON downloads(user_id);
            CREATE INDEX IF NOT EXISTS idx_downloads_date ON downloads(downloaded_at);
            CREATE INDEX IF NOT EXISTS idx_favorites_user_id ON favorites(user_id);
            CREATE INDEX IF NOT EXISTS idx_daily_downloads_user_date
                ON daily_downloads(user_id, download_date);
            CREATE INDEX IF NOT EXISTS idx_track_stats_count
                ON track_stats(download_count DESC);
            CREATE INDEX IF NOT EXISTS idx_users_referral ON users(referral_code);
        """)
        await self.connection.commit()

    async def execute(self, query: str, params: tuple = ()):
        """Execute a query and return cursor."""
        return await self.connection.execute(query, params)

    async def executemany(self, query: str, params_list: list):
        """Execute query for multiple parameter sets."""
        return await self.connection.executemany(query, params_list)

    async def fetchone(self, query: str, params: tuple = ()):
        """Execute query and fetch one row."""
        cursor = await self.connection.execute(query, params)
        return await cursor.fetchone()

    async def fetchall(self, query: str, params: tuple = ()):
        """Execute query and fetch all rows."""
        cursor = await self.connection.execute(query, params)
        return await cursor.fetchall()

    async def commit(self):
        """Commit transaction."""
        await self.connection.commit()


# Global database instance
db = Database(settings.DATABASE_PATH)
