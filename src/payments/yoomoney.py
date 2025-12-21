"""YooMoney payment integration.

YooMoney API documentation: https://yoomoney.ru/docs/wallet
Quickpay documentation: https://yoomoney.ru/docs/payment-buttons/using-api/forms
"""
import hashlib
import aiohttp
from typing import Optional, Dict, Any
from dataclasses import dataclass
from urllib.parse import urlencode

from src.config import settings
from src.utils.logger import logger


@dataclass
class YooMoneyPayment:
    """YooMoney payment data."""
    payment_id: str
    payment_url: str
    amount: float
    label: str
    status: str = "pending"


class YooMoneyHandler:
    """YooMoney payment handler using Quickpay forms."""

    # Quickpay form URL
    QUICKPAY_URL = "https://yoomoney.ru/quickpay/confirm.xml"
    PAYMENT_URL = "https://yoomoney.ru/quickpay/confirm"

    # Premium tariffs in RUB
    TARIFFS = {
        "month_1": {
            "title": "Премиум 1 месяц",
            "description": "Безлимитные скачивания на 30 дней",
            "amount": 99.0,  # RUB
            "days": 30
        },
        "month_3": {
            "title": "Премиум 3 месяца",
            "description": "Безлимитные скачивания на 90 дней",
            "amount": 249.0,  # RUB (скидка)
            "days": 90
        },
        "year": {
            "title": "Премиум 1 год",
            "description": "Безлимитные скачивания на 365 дней",
            "amount": 799.0,  # RUB (скидка)
            "days": 365
        }
    }

    # Donation options in RUB
    DONATIONS = {
        "coffee": {"title": "☕ Кофе", "amount": 50.0},
        "pizza": {"title": "🍕 Пицца", "amount": 300.0},
        "server": {"title": "🖥 Сервер на месяц", "amount": 500.0}
    }

    def __init__(self):
        self.wallet = getattr(settings, 'YOOMONEY_WALLET', '')
        self.secret_key = getattr(settings, 'YOOMONEY_SECRET', '')
        self.notification_url = getattr(settings, 'YOOMONEY_NOTIFICATION_URL', '')

    def create_payment_url(
        self,
        amount: float,
        label: str,
        comment: str = "",
        success_url: str = ""
    ) -> str:
        """
        Create Quickpay payment URL.

        Args:
            amount: Payment amount in RUB
            label: Unique payment label for tracking
            comment: Payment comment/description
            success_url: URL to redirect after successful payment

        Returns:
            Payment URL string
        """
        params = {
            "receiver": self.wallet,
            "quickpay-form": "shop",
            "targets": comment or "Оплата услуг",
            "paymentType": "AC",  # Bank card
            "sum": amount,
            "label": label,
            "successURL": success_url or f"https://t.me/{settings.BOT_USERNAME}"
        }

        # Filter out empty values
        params = {k: v for k, v in params.items() if v}

        return f"{self.PAYMENT_URL}?{urlencode(params)}"

    def create_premium_payment(self, user_id: int, tariff_id: str) -> Optional[YooMoneyPayment]:
        """
        Create payment for premium subscription.

        Args:
            user_id: Telegram user ID
            tariff_id: Tariff identifier (month_1, month_3, year)

        Returns:
            YooMoneyPayment or None
        """
        tariff = self.TARIFFS.get(tariff_id)
        if not tariff:
            logger.warning(f"Unknown tariff: {tariff_id}")
            return None

        # Create unique label for tracking
        label = f"premium_{tariff_id}_{user_id}"

        payment_url = self.create_payment_url(
            amount=tariff["amount"],
            label=label,
            comment=tariff["description"]
        )

        logger.info(f"Created YooMoney payment: {label}, amount={tariff['amount']} RUB")

        return YooMoneyPayment(
            payment_id=label,
            payment_url=payment_url,
            amount=tariff["amount"],
            label=label
        )

    def create_donation_payment(self, user_id: int, donation_id: str) -> Optional[YooMoneyPayment]:
        """
        Create payment for donation.

        Args:
            user_id: Telegram user ID
            donation_id: Donation identifier (coffee, pizza, server)

        Returns:
            YooMoneyPayment or None
        """
        donation = self.DONATIONS.get(donation_id)
        if not donation:
            logger.warning(f"Unknown donation: {donation_id}")
            return None

        label = f"donate_{donation_id}_{user_id}"

        payment_url = self.create_payment_url(
            amount=donation["amount"],
            label=label,
            comment=f"Донат: {donation['title']}"
        )

        logger.info(f"Created YooMoney donation: {label}, amount={donation['amount']} RUB")

        return YooMoneyPayment(
            payment_id=label,
            payment_url=payment_url,
            amount=donation["amount"],
            label=label
        )

    def verify_notification(self, data: Dict[str, Any]) -> bool:
        """
        Verify YooMoney notification signature.

        YooMoney sends notifications to the webhook URL when payment is completed.
        The notification contains a SHA-1 hash that must be verified.

        Args:
            data: Notification data from YooMoney

        Returns:
            True if signature is valid
        """
        if not self.secret_key:
            logger.warning("YOOMONEY_SECRET not configured, skipping verification")
            return True

        # Build hash string according to YooMoney docs
        # https://yoomoney.ru/docs/wallet/using-api/notification-p2p-incoming
        hash_string = "&".join([
            data.get("notification_type", ""),
            data.get("operation_id", ""),
            data.get("amount", ""),
            data.get("currency", ""),
            data.get("datetime", ""),
            data.get("sender", ""),
            data.get("codepro", ""),
            self.secret_key,
            data.get("label", "")
        ])

        expected_hash = hashlib.sha1(hash_string.encode()).hexdigest()
        actual_hash = data.get("sha1_hash", "")

        is_valid = expected_hash == actual_hash

        if not is_valid:
            logger.warning(f"Invalid YooMoney notification hash: expected={expected_hash}, got={actual_hash}")

        return is_valid

    def parse_label(self, label: str) -> Optional[Dict[str, Any]]:
        """
        Parse payment label to extract type, tariff/donation ID, and user ID.

        Args:
            label: Payment label (e.g., "premium_month_1_123456789")

        Returns:
            Dict with parsed data or None
        """
        try:
            parts = label.split("_")
            if len(parts) < 3:
                return None

            payment_type = parts[0]  # premium or donate

            if payment_type == "premium":
                # premium_month_1_123456789 or premium_month_3_123456789 or premium_year_123456789
                if parts[1] == "year":
                    tariff_id = "year"
                    user_id = int(parts[2])
                else:
                    tariff_id = f"{parts[1]}_{parts[2]}"
                    user_id = int(parts[3])

                return {
                    "type": "premium",
                    "tariff_id": tariff_id,
                    "user_id": user_id
                }

            elif payment_type == "donate":
                # donate_coffee_123456789
                donation_id = parts[1]
                user_id = int(parts[2])

                return {
                    "type": "donate",
                    "donation_id": donation_id,
                    "user_id": user_id
                }

            return None

        except (ValueError, IndexError) as e:
            logger.error(f"Failed to parse label '{label}': {e}")
            return None

    @classmethod
    def get_tariff(cls, tariff_id: str) -> Optional[Dict]:
        return cls.TARIFFS.get(tariff_id)

    @classmethod
    def get_donation(cls, donation_id: str) -> Optional[Dict]:
        return cls.DONATIONS.get(donation_id)

    @classmethod
    def get_all_tariffs(cls) -> Dict:
        return cls.TARIFFS

    @classmethod
    def get_all_donations(cls) -> Dict:
        return cls.DONATIONS


# Singleton instance
yoomoney = YooMoneyHandler()
