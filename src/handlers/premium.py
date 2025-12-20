"""Premium subscription and payments handler."""
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    PreCheckoutQuery, ContentType
)

from src.bot import bot
from src.config import settings
from src.database.repositories import user_repo
from src.payments.stars import StarsPayment
from src.payments.cryptobot import cryptobot, CryptoBotPayment
from src.utils.logger import logger

router = Router()


def create_premium_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard with premium tariffs."""
    tariffs = StarsPayment.get_all_tariffs()

    buttons = []
    for tariff_id, tariff in tariffs.items():
        buttons.append([InlineKeyboardButton(
            text=f"⭐ {tariff['label']} - {tariff['stars']} Stars",
            callback_data=f"buy_premium:{tariff_id}"
        )])

    # CryptoBot option
    if settings.CRYPTOBOT_TOKEN:
        buttons.append([InlineKeyboardButton(
            text="💎 Оплатить криптой (USDT/TON)",
            callback_data="crypto_premium"
        )])

    # Add donate button
    buttons.append([InlineKeyboardButton(
        text="☕ Поддержать проект",
        callback_data="show_donate"
    )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_donate_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard with donation options."""
    donations = StarsPayment.get_all_donations()

    buttons = []
    for donation_id, donation in donations.items():
        buttons.append([InlineKeyboardButton(
            text=f"{donation['title']} - {donation['stars']} ⭐",
            callback_data=f"donate:{donation_id}"
        )])

    buttons.append([InlineKeyboardButton(
        text="🔙 Назад к премиуму",
        callback_data="show_premium"
    )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("premium"))
async def premium_command(message: Message):
    """Show premium info and purchase options."""
    user_id = message.from_user.id

    # Check current premium status
    user = await user_repo.get_user(user_id)
    is_premium = user.get("is_premium", False) if user else False
    premium_until = user.get("premium_until") if user else None

    if is_premium and premium_until:
        # Parse date if string
        if isinstance(premium_until, str):
            premium_until = datetime.fromisoformat(premium_until)

        status_text = (
            f"✅ <b>У тебя активен Премиум!</b>\n"
            f"📅 Действует до: {premium_until.strftime('%d.%m.%Y %H:%M')}\n\n"
        )
    else:
        status_text = "❌ <b>У тебя нет Премиум подписки</b>\n\n"

    text = (
        f"⭐ <b>ПРЕМИУМ ПОДПИСКА</b>\n\n"
        f"{status_text}"
        f"<b>Преимущества Премиум:</b>\n"
        f"• ♾ Безлимитные скачивания\n"
        f"• 🚀 Приоритет в очереди\n"
        f"• 🎵 Распознавание музыки без лимитов\n"
        f"• ❤️ Безлимитное избранное\n"
        f"• 🎁 Бонусы за рефералов x2\n\n"
        f"<b>Выбери тариф:</b>"
    )

    keyboard = create_premium_keyboard()
    await message.answer(text, reply_markup=keyboard)
    logger.info(f"User {user_id} opened premium menu")


@router.callback_query(F.data == "show_premium")
async def show_premium_callback(callback: CallbackQuery):
    """Show premium menu."""
    user_id = callback.from_user.id

    user = await user_repo.get_user(user_id)
    is_premium = user.get("is_premium", False) if user else False
    premium_until = user.get("premium_until") if user else None

    if is_premium and premium_until:
        if isinstance(premium_until, str):
            premium_until = datetime.fromisoformat(premium_until)

        status_text = (
            f"✅ <b>У тебя активен Премиум!</b>\n"
            f"📅 Действует до: {premium_until.strftime('%d.%m.%Y %H:%M')}\n\n"
        )
    else:
        status_text = "❌ <b>У тебя нет Премиум подписки</b>\n\n"

    text = (
        f"⭐ <b>ПРЕМИУМ ПОДПИСКА</b>\n\n"
        f"{status_text}"
        f"<b>Преимущества Премиум:</b>\n"
        f"• ♾ Безлимитные скачивания\n"
        f"• 🚀 Приоритет в очереди\n"
        f"• 🎵 Распознавание музыки без лимитов\n"
        f"• ❤️ Безлимитное избранное\n"
        f"• 🎁 Бонусы за рефералов x2\n\n"
        f"<b>Выбери тариф:</b>"
    )

    keyboard = create_premium_keyboard()
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "show_donate")
async def show_donate_callback(callback: CallbackQuery):
    """Show donation options."""
    text = (
        "☕ <b>ПОДДЕРЖАТЬ ПРОЕКТ</b>\n\n"
        "Твоя поддержка помогает развивать бота!\n\n"
        "Все донаты идут на:\n"
        "• 🖥 Оплату сервера\n"
        "• 🛠 Разработку новых функций\n"
        "• 🐛 Исправление багов\n\n"
        "<b>Выбери сумму:</b>"
    )

    keyboard = create_donate_keyboard()
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.message(Command("donate"))
async def donate_command(message: Message):
    """Show donation options."""
    text = (
        "☕ <b>ПОДДЕРЖАТЬ ПРОЕКТ</b>\n\n"
        "Твоя поддержка помогает развивать бота!\n\n"
        "Все донаты идут на:\n"
        "• 🖥 Оплату сервера\n"
        "• 🛠 Разработку новых функций\n"
        "• 🐛 Исправление багов\n\n"
        "<b>Выбери сумму:</b>"
    )

    keyboard = create_donate_keyboard()
    await message.answer(text, reply_markup=keyboard)
    logger.info(f"User {message.from_user.id} opened donate menu")


@router.callback_query(F.data.startswith("buy_premium:"))
async def buy_premium_callback(callback: CallbackQuery):
    """Process premium purchase."""
    tariff_id = callback.data.split(":")[1]
    tariff = StarsPayment.get_tariff(tariff_id)

    if not tariff:
        await callback.answer("❌ Тариф не найден", show_alert=True)
        return

    try:
        # Create invoice using Telegram Stars
        await bot.send_invoice(
            chat_id=callback.from_user.id,
            title=tariff["title"],
            description=tariff["description"],
            payload=f"premium:{tariff_id}",
            currency="XTR",  # Telegram Stars
            prices=StarsPayment.create_invoice_prices(tariff["stars"]),
            provider_token=""  # Empty for Stars
        )

        await callback.answer()
        logger.info(f"User {callback.from_user.id} initiated premium purchase: {tariff_id}")

    except Exception as e:
        logger.error(f"Failed to create invoice: {e}")
        await callback.answer("❌ Ошибка при создании платежа", show_alert=True)


@router.callback_query(F.data.startswith("donate:"))
async def donate_callback(callback: CallbackQuery):
    """Process donation."""
    donation_id = callback.data.split(":")[1]
    donation = StarsPayment.get_donation(donation_id)

    if not donation:
        await callback.answer("❌ Опция не найдена", show_alert=True)
        return

    try:
        await bot.send_invoice(
            chat_id=callback.from_user.id,
            title=donation["title"],
            description=donation["description"],
            payload=f"donate:{donation_id}",
            currency="XTR",
            prices=StarsPayment.create_invoice_prices(donation["stars"]),
            provider_token=""
        )

        await callback.answer()
        logger.info(f"User {callback.from_user.id} initiated donation: {donation_id}")

    except Exception as e:
        logger.error(f"Failed to create donation invoice: {e}")
        await callback.answer("❌ Ошибка при создании платежа", show_alert=True)


@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout: PreCheckoutQuery):
    """Handle pre-checkout query - always approve for Stars."""
    await pre_checkout.answer(ok=True)
    logger.info(f"Pre-checkout approved for user {pre_checkout.from_user.id}: {pre_checkout.invoice_payload}")


@router.message(F.content_type == ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment_handler(message: Message):
    """Handle successful payment."""
    user_id = message.from_user.id
    payment = message.successful_payment
    payload = payment.invoice_payload

    logger.info(f"Successful payment from {user_id}: {payload}, {payment.total_amount} {payment.currency}")

    if payload.startswith("premium:"):
        # Premium purchase
        tariff_id = payload.split(":")[1]
        tariff = StarsPayment.get_tariff(tariff_id)

        if tariff:
            days = tariff["days"]

            # Check if user already has premium - extend it
            user = await user_repo.get_user(user_id)
            current_until = None

            if user and user.get("is_premium") and user.get("premium_until"):
                current_until = user["premium_until"]
                if isinstance(current_until, str):
                    current_until = datetime.fromisoformat(current_until)

            # Calculate new expiry date
            if current_until and current_until > datetime.now():
                new_until = current_until + timedelta(days=days)
            else:
                new_until = datetime.now() + timedelta(days=days)

            # Grant premium
            await user_repo.set_premium(user_id, True, new_until)

            # Log payment
            await user_repo.log_payment(
                user_id=user_id,
                amount=payment.total_amount,
                currency=payment.currency,
                payment_type="premium",
                payload=payload
            )

            await message.answer(
                f"🎉 <b>Спасибо за покупку!</b>\n\n"
                f"✅ Премиум активирован!\n"
                f"📅 Действует до: {new_until.strftime('%d.%m.%Y %H:%M')}\n\n"
                f"Наслаждайся безлимитными скачиваниями! 🎵"
            )

            logger.info(f"Premium granted to {user_id} until {new_until}")

    elif payload.startswith("donate:"):
        # Donation
        donation_id = payload.split(":")[1]
        donation = StarsPayment.get_donation(donation_id)

        # Log payment
        await user_repo.log_payment(
            user_id=user_id,
            amount=payment.total_amount,
            currency=payment.currency,
            payment_type="donate",
            payload=payload
        )

        await message.answer(
            f"❤️ <b>Огромное спасибо за поддержку!</b>\n\n"
            f"Твой донат поможет развитию бота!\n"
            f"Мы очень ценим твою помощь! 🙏"
        )

        logger.info(f"Donation received from {user_id}: {donation_id}")

# ============== CryptoBot Payments ==============

def create_crypto_tariffs_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard with crypto tariffs."""
    tariffs = CryptoBotPayment.get_all_tariffs()

    buttons = []
    for tariff_id, tariff in tariffs.items():
        buttons.append([InlineKeyboardButton(
            text=f"💎 {tariff['title']} - ${tariff['amount']}",
            callback_data=f"crypto_buy:{tariff_id}"
        )])

    buttons.append([InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="show_premium"
    )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_crypto_donate_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard with crypto donation options."""
    donations = CryptoBotPayment.get_all_donations()

    buttons = []
    for donation_id, donation in donations.items():
        buttons.append([InlineKeyboardButton(
            text=f"{donation['title']} - ${donation['amount']}",
            callback_data=f"crypto_donate_pay:{donation_id}"
        )])

    buttons.append([InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="show_donate"
    )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data == "crypto_premium")
async def crypto_premium_callback(callback: CallbackQuery):
    """Show crypto tariffs."""
    text = (
        "💎 <b>ОПЛАТА КРИПТОЙ</b>\n\n"
        "Принимаем: USDT, TON, BTC, ETH и другие\n\n"
        "<b>Выбери тариф:</b>"
    )

    keyboard = create_crypto_tariffs_keyboard()
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("crypto_buy:"))
async def crypto_buy_callback(callback: CallbackQuery):
    """Create CryptoBot invoice for premium."""
    tariff_id = callback.data.split(":")[1]
    user_id = callback.from_user.id

    invoice = await cryptobot.create_premium_invoice(user_id, tariff_id)

    if invoice:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="💎 Оплатить",
                url=invoice.bot_invoice_url
            )],
            [InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="crypto_premium"
            )]
        ])

        tariff = CryptoBotPayment.get_tariff(tariff_id)
        await callback.message.edit_text(
            f"💎 <b>{tariff['title']}</b>\n\n"
            f"💰 Сумма: <b>${tariff['amount']} USDT</b>\n"
            f"📅 Срок: {tariff['days']} дней\n\n"
            f"Нажми кнопку ниже для оплаты.\n"
            f"После оплаты премиум активируется автоматически.",
            reply_markup=keyboard
        )
        await callback.answer()

        logger.info(f"User {user_id} created crypto invoice: {invoice.invoice_id}")
    else:
        await callback.answer("❌ Ошибка создания платежа", show_alert=True)


@router.callback_query(F.data == "crypto_donate")
async def crypto_donate_callback(callback: CallbackQuery):
    """Show crypto donation options."""
    text = (
        "💎 <b>ДОНАТ КРИПТОЙ</b>\n\n"
        "Поддержи проект криптовалютой!\n\n"
        "<b>Выбери сумму:</b>"
    )

    keyboard = create_crypto_donate_keyboard()
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("crypto_donate_pay:"))
async def crypto_donate_pay_callback(callback: CallbackQuery):
    """Create CryptoBot invoice for donation."""
    donation_id = callback.data.split(":")[1]
    user_id = callback.from_user.id

    invoice = await cryptobot.create_donation_invoice(user_id, donation_id)

    if invoice:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="💎 Оплатить",
                url=invoice.bot_invoice_url
            )],
            [InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="crypto_donate"
            )]
        ])

        donation = CryptoBotPayment.get_donation(donation_id)
        await callback.message.edit_text(
            f"💎 <b>Донат: {donation['title']}</b>\n\n"
            f"💰 Сумма: <b>${donation['amount']} USDT</b>\n\n"
            f"Нажми кнопку ниже для оплаты.",
            reply_markup=keyboard
        )
        await callback.answer()

        logger.info(f"User {user_id} created crypto donation invoice: {invoice.invoice_id}")
    else:
        await callback.answer("❌ Ошибка создания платежа", show_alert=True)
