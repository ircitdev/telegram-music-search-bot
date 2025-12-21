"""Tests for database operations."""
import pytest
import aiosqlite
from datetime import datetime, timedelta


class TestUserRepository:
    """Test user repository operations."""

    @pytest.mark.asyncio
    async def test_create_user(self, test_db):
        """Test creating a new user."""
        async with aiosqlite.connect(test_db) as db:
            db.row_factory = aiosqlite.Row

            # Insert user
            await db.execute("""
                INSERT INTO users (id, username, first_name)
                VALUES (?, ?, ?)
            """, (123456789, "testuser", "Test"))
            await db.commit()

            # Verify
            cursor = await db.execute("SELECT * FROM users WHERE id = ?", (123456789,))
            user = await cursor.fetchone()

            assert user is not None
            assert user["username"] == "testuser"
            assert user["first_name"] == "Test"
            assert user["is_premium"] == 0

    @pytest.mark.asyncio
    async def test_update_premium_status(self, test_db):
        """Test updating user premium status."""
        async with aiosqlite.connect(test_db) as db:
            db.row_factory = aiosqlite.Row

            # Create user
            await db.execute("""
                INSERT INTO users (id, username)
                VALUES (?, ?)
            """, (123456789, "testuser"))

            # Update premium
            premium_until = (datetime.now() + timedelta(days=30)).isoformat()
            await db.execute("""
                UPDATE users SET is_premium = 1, premium_until = ?
                WHERE id = ?
            """, (premium_until, 123456789))
            await db.commit()

            # Verify
            cursor = await db.execute("SELECT * FROM users WHERE id = ?", (123456789,))
            user = await cursor.fetchone()

            assert user["is_premium"] == 1
            assert user["premium_until"] is not None

    @pytest.mark.asyncio
    async def test_increment_downloads(self, test_db):
        """Test incrementing download count."""
        async with aiosqlite.connect(test_db) as db:
            db.row_factory = aiosqlite.Row

            # Create user
            await db.execute("""
                INSERT INTO users (id, downloads)
                VALUES (?, 0)
            """, (123456789,))

            # Increment
            await db.execute("""
                UPDATE users SET downloads = downloads + 1
                WHERE id = ?
            """, (123456789,))
            await db.commit()

            # Verify
            cursor = await db.execute("SELECT downloads FROM users WHERE id = ?", (123456789,))
            user = await cursor.fetchone()

            assert user["downloads"] == 1

    @pytest.mark.asyncio
    async def test_log_download(self, test_db):
        """Test logging a download."""
        async with aiosqlite.connect(test_db) as db:
            db.row_factory = aiosqlite.Row

            # Log download
            await db.execute("""
                INSERT INTO downloads (user_id, video_id, title, artist)
                VALUES (?, ?, ?, ?)
            """, (123456789, "abc123", "Test Song", "Test Artist"))
            await db.commit()

            # Verify
            cursor = await db.execute("SELECT * FROM downloads WHERE user_id = ?", (123456789,))
            download = await cursor.fetchone()

            assert download is not None
            assert download["title"] == "Test Song"
            assert download["artist"] == "Test Artist"

    @pytest.mark.asyncio
    async def test_referral_count(self, test_db):
        """Test counting referrals."""
        async with aiosqlite.connect(test_db) as db:
            db.row_factory = aiosqlite.Row

            # Create referrer
            await db.execute("""
                INSERT INTO users (id, username)
                VALUES (?, ?)
            """, (111, "referrer"))

            # Create referred users
            for i in range(3):
                await db.execute("""
                    INSERT INTO users (id, username, referred_by)
                    VALUES (?, ?, ?)
                """, (200 + i, f"user{i}", 111))

            await db.commit()

            # Count referrals
            cursor = await db.execute("""
                SELECT COUNT(*) as count FROM users WHERE referred_by = ?
            """, (111,))
            result = await cursor.fetchone()

            assert result["count"] == 3


class TestPaymentRepository:
    """Test payment repository operations."""

    @pytest.mark.asyncio
    async def test_log_payment(self, test_db):
        """Test logging a payment."""
        async with aiosqlite.connect(test_db) as db:
            db.row_factory = aiosqlite.Row

            # Log payment
            await db.execute("""
                INSERT INTO payments (user_id, amount, currency, payment_type, payload)
                VALUES (?, ?, ?, ?, ?)
            """, (123456789, 50, "XTR", "premium", "premium:month_1"))
            await db.commit()

            # Verify
            cursor = await db.execute("SELECT * FROM payments WHERE user_id = ?", (123456789,))
            payment = await cursor.fetchone()

            assert payment is not None
            assert payment["amount"] == 50
            assert payment["currency"] == "XTR"
            assert payment["payment_type"] == "premium"

    @pytest.mark.asyncio
    async def test_total_revenue(self, test_db):
        """Test calculating total revenue."""
        async with aiosqlite.connect(test_db) as db:
            db.row_factory = aiosqlite.Row

            # Create payments
            for amount in [50, 100, 200]:
                await db.execute("""
                    INSERT INTO payments (user_id, amount, currency, payment_type)
                    VALUES (?, ?, 'XTR', 'premium')
                """, (123456789, amount))
            await db.commit()

            # Calculate total
            cursor = await db.execute("SELECT SUM(amount) as total FROM payments")
            result = await cursor.fetchone()

            assert result["total"] == 350
