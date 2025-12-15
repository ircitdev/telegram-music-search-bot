"""Telegram Stars payment integration."""
from aiogram.types import LabeledPrice


class StarsPayment:
    """Telegram Stars payment handler."""

    # Tariff plans (price in Telegram Stars)
    # 1 Star ≈ $0.02, so ~50 stars = $1
    TARIFFS = {
        "month_1": {
            "title": "Премиум на 1 месяц",
            "description": "Безлимитные скачивания на 1 месяц",
            "days": 30,
            "stars": 50,  # ~$1
            "label": "1 месяц"
        },
        "month_3": {
            "title": "Премиум на 3 месяца",
            "description": "Безлимитные скачивания на 3 месяца (скидка 20%)",
            "days": 90,
            "stars": 120,  # ~$2.40 (вместо $3)
            "label": "3 месяца"
        },
        "year": {
            "title": "Премиум на 1 год",
            "description": "Безлимитные скачивания на 1 год (скидка 40%)",
            "days": 365,
            "stars": 360,  # ~$7.20 (вместо $12)
            "label": "1 год"
        }
    }

    # Donation amounts
    DONATIONS = {
        "coffee": {
            "title": "Кофе для разработчика ☕",
            "description": "Поддержать проект",
            "stars": 25
        },
        "pizza": {
            "title": "Пицца для команды 🍕",
            "description": "Спасибо за поддержку!",
            "stars": 100
        },
        "server": {
            "title": "Оплата сервера 🖥",
            "description": "Помощь с оплатой хостинга",
            "stars": 250
        }
    }

    @classmethod
    def get_tariff(cls, tariff_id: str) -> dict | None:
        """Get tariff by ID."""
        return cls.TARIFFS.get(tariff_id)

    @classmethod
    def get_donation(cls, donation_id: str) -> dict | None:
        """Get donation by ID."""
        return cls.DONATIONS.get(donation_id)

    @classmethod
    def create_invoice_prices(cls, stars: int) -> list[LabeledPrice]:
        """Create prices for invoice."""
        return [LabeledPrice(label="XTR", amount=stars)]

    @classmethod
    def get_all_tariffs(cls) -> dict:
        """Get all available tariffs."""
        return cls.TARIFFS

    @classmethod
    def get_all_donations(cls) -> dict:
        """Get all donation options."""
        return cls.DONATIONS
