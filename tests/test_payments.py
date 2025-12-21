"""Tests for payment systems."""
import pytest


class TestStarsPayment:
    """Test Telegram Stars payment system."""

    def test_get_all_tariffs(self):
        """Test getting all tariffs."""
        from src.payments.stars import StarsPayment

        tariffs = StarsPayment.get_all_tariffs()

        assert len(tariffs) >= 3
        assert "month_1" in tariffs
        assert "month_3" in tariffs
        assert "year_1" in tariffs

    def test_get_tariff(self):
        """Test getting specific tariff."""
        from src.payments.stars import StarsPayment

        tariff = StarsPayment.get_tariff("month_1")

        assert tariff is not None
        assert "stars" in tariff
        assert "days" in tariff
        assert tariff["days"] == 30

    def test_get_nonexistent_tariff(self):
        """Test getting non-existent tariff."""
        from src.payments.stars import StarsPayment

        tariff = StarsPayment.get_tariff("nonexistent")

        assert tariff is None

    def test_create_invoice_prices(self):
        """Test creating invoice prices."""
        from src.payments.stars import StarsPayment

        prices = StarsPayment.create_invoice_prices(50)

        assert len(prices) == 1
        assert prices[0].amount == 50

    def test_get_all_donations(self):
        """Test getting all donation options."""
        from src.payments.stars import StarsPayment

        donations = StarsPayment.get_all_donations()

        assert len(donations) >= 3


class TestCryptoBotPayment:
    """Test CryptoBot payment system."""

    def test_get_all_tariffs(self):
        """Test getting crypto tariffs."""
        from src.payments.cryptobot import CryptoBotPayment

        tariffs = CryptoBotPayment.get_all_tariffs()

        assert len(tariffs) >= 3
        assert "month_1" in tariffs

    def test_get_tariff(self):
        """Test getting specific crypto tariff."""
        from src.payments.cryptobot import CryptoBotPayment

        tariff = CryptoBotPayment.get_tariff("month_1")

        assert tariff is not None
        assert "amount" in tariff
        assert "days" in tariff

    def test_get_all_donations(self):
        """Test getting crypto donation options."""
        from src.payments.cryptobot import CryptoBotPayment

        donations = CryptoBotPayment.get_all_donations()

        assert len(donations) >= 3
