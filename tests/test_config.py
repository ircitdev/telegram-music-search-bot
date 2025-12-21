"""Tests for configuration module."""
import os
import pytest


class TestSettings:
    """Test Settings class."""

    def test_settings_loads(self):
        """Test that settings load without errors."""
        os.environ["BOT_TOKEN"] = "test:token"
        os.environ["ADMIN_IDS"] = "123,456,789"

        from src.config import Settings
        settings = Settings()

        assert settings.BOT_TOKEN == "test:token"

    def test_get_admin_ids_parses_correctly(self):
        """Test admin IDs parsing."""
        os.environ["BOT_TOKEN"] = "test:token"
        os.environ["ADMIN_IDS"] = "123, 456, 789"

        from src.config import Settings
        settings = Settings()
        admin_ids = settings.get_admin_ids()

        assert admin_ids == [123, 456, 789]

    def test_get_admin_ids_empty(self):
        """Test empty admin IDs."""
        os.environ["BOT_TOKEN"] = "test:token"
        os.environ["ADMIN_IDS"] = ""

        from src.config import Settings
        settings = Settings()
        admin_ids = settings.get_admin_ids()

        assert admin_ids == []

    def test_default_limits(self):
        """Test default download limits."""
        os.environ["BOT_TOKEN"] = "test:token"

        from src.config import Settings
        settings = Settings()

        assert settings.DAILY_DOWNLOAD_LIMIT == 10
        assert settings.REFERRAL_BONUS == 5
