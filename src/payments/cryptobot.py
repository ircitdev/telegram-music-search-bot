"""CryptoBot payment integration.

CryptoBot API documentation: https://help.crypt.bot/crypto-pay-api
"""
import aiohttp
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

from src.config import settings
from src.utils.logger import logger


class CryptoCurrency(str, Enum):
    """Supported cryptocurrencies."""
    USDT = "USDT"
    TON = "TON"
    BTC = "BTC"
    ETH = "ETH"
    LTC = "LTC"
    BNB = "BNB"
    TRX = "TRX"
    USDC = "USDC"


@dataclass
class CryptoInvoice:
    """CryptoBot invoice data."""
    invoice_id: int
    bot_invoice_url: str
    mini_app_invoice_url: str
    web_app_invoice_url: str
    status: str
    hash: str
    asset: str
    amount: str
    description: str
    paid_at: Optional[str] = None


class CryptoBotPayment:
    """CryptoBot payment handler."""

    API_URL = "https://pay.crypt.bot/api"

    # Premium tariffs in USDT
    TARIFFS = {
        "month_1": {
            "title": "Премиум 1 месяц",
            "description": "Безлимитные скачивания на 30 дней",
            "amount": "1.99",  # USDT
            "days": 30
        },
        "month_3": {
            "title": "Премиум 3 месяца",
            "description": "Безлимитные скачивания на 90 дней",
            "amount": "4.99",  # USDT
            "days": 90
        },
        "year": {
            "title": "Премиум 1 год",
            "description": "Безлимитные скачивания на 365 дней",
            "amount": "14.99",  # USDT
            "days": 365
        }
    }

    # Donation options in USDT
    DONATIONS = {
        "coffee": {"title": "☕ Кофе", "amount": "1.00"},
        "pizza": {"title": "🍕 Пицца", "amount": "5.00"},
        "server": {"title": "🖥 Сервер на месяц", "amount": "10.00"}
    }

    def __init__(self):
        self.token = getattr(settings, 'CRYPTOBOT_TOKEN', '')

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Crypto-Pay-API-Token": self.token,
            "Content-Type": "application/json"
        }

    async def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Make API request to CryptoBot."""
        url = f"{self.API_URL}/{endpoint}"

        try:
            async with aiohttp.ClientSession() as session:
                if method == "GET":
                    async with session.get(url, headers=self.headers, params=data) as resp:
                        result = await resp.json()
                else:
                    async with session.post(url, headers=self.headers, json=data) as resp:
                        result = await resp.json()

                if result.get("ok"):
                    return result.get("result")
                else:
                    logger.error(f"CryptoBot API error: {result}")
                    return None

        except Exception as e:
            logger.error(f"CryptoBot request error: {e}")
            return None

    async def get_me(self) -> Optional[Dict]:
        """Get bot info."""
        return await self._request("GET", "getMe")

    async def create_invoice(
        self,
        amount: str,
        asset: str = "USDT",
        description: str = "",
        payload: str = "",
        expires_in: int = 3600
    ) -> Optional[CryptoInvoice]:
        """
        Create payment invoice.

        Args:
            amount: Payment amount
            asset: Cryptocurrency (USDT, TON, BTC, etc.)
            description: Invoice description
            payload: Custom payload for tracking
            expires_in: Expiration time in seconds

        Returns:
            CryptoInvoice or None
        """
        data = {
            "asset": asset,
            "amount": amount,
            "description": description,
            "payload": payload,
            "expires_in": expires_in,
            "paid_btn_name": "callback",
            "paid_btn_url": f"https://t.me/{settings.BOT_USERNAME}"
        }

        result = await self._request("POST", "createInvoice", data)

        if result:
            return CryptoInvoice(
                invoice_id=result["invoice_id"],
                bot_invoice_url=result["bot_invoice_url"],
                mini_app_invoice_url=result.get("mini_app_invoice_url", ""),
                web_app_invoice_url=result.get("web_app_invoice_url", ""),
                status=result["status"],
                hash=result["hash"],
                asset=result["asset"],
                amount=result["amount"],
                description=result.get("description", "")
            )

        return None

    async def get_invoices(
        self,
        asset: Optional[str] = None,
        invoice_ids: Optional[list] = None,
        status: Optional[str] = None,
        offset: int = 0,
        count: int = 100
    ) -> Optional[list]:
        """Get list of invoices."""
        data = {"offset": offset, "count": count}

        if asset:
            data["asset"] = asset
        if invoice_ids:
            data["invoice_ids"] = ",".join(map(str, invoice_ids))
        if status:
            data["status"] = status

        result = await self._request("GET", "getInvoices", data)
        return result.get("items") if result else None

    async def get_invoice(self, invoice_id: int) -> Optional[Dict]:
        """Get single invoice by ID."""
        invoices = await self.get_invoices(invoice_ids=[invoice_id])
        return invoices[0] if invoices else None

    async def create_premium_invoice(self, user_id: int, tariff_id: str) -> Optional[CryptoInvoice]:
        """Create invoice for premium subscription."""
        tariff = self.TARIFFS.get(tariff_id)
        if not tariff:
            return None

        return await self.create_invoice(
            amount=tariff["amount"],
            asset="USDT",
            description=tariff["description"],
            payload=f"premium:{tariff_id}:{user_id}"
        )

    async def create_donation_invoice(self, user_id: int, donation_id: str) -> Optional[CryptoInvoice]:
        """Create invoice for donation."""
        donation = self.DONATIONS.get(donation_id)
        if not donation:
            return None

        return await self.create_invoice(
            amount=donation["amount"],
            asset="USDT",
            description=f"Донат: {donation['title']}",
            payload=f"donate:{donation_id}:{user_id}"
        )

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
cryptobot = CryptoBotPayment()
