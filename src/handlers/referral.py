"""Referral system handler."""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from src.database.repositories import user_repo
from src.utils.logger import logger
from src.config import settings

router = Router()


@router.message(Command("referral"))
async def referral_command(message: Message):
    """Show referral info and link."""
    user_id = message.from_user.id

    # Get user stats
    user = await user_repo.get_user(user_id)
    if not user:
        await message.answer("❌ Произошла ошибка. Попробуй /start")
        return

    # Get referral stats
    referred_count = await user_repo.get_referral_count(user_id)
    active_count = await user_repo.get_active_referral_count(user_id)
    bonus = user.get("bonus_downloads", 0)

    # Generate referral link
    bot_username = settings.BOT_USERNAME
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"

    text = (
        "👥 <b>РЕФЕРАЛЬНАЯ ПРОГРАММА</b>\n\n"

        "Приглашай друзей и получай бонусы!\n\n"

        "🎁 <b>Награды:</b>\n"
        "• +5 скачиваний за каждого приглашённого\n"
        "• +10 скачиваний когда он скачает 5 треков\n\n"

        "📊 <b>Твоя статистика:</b>\n"
        f"• Приглашено: {referred_count}\n"
        f"• Активных: {active_count}\n"
        f"• Бонусов: {bonus}\n\n"

        "🔗 <b>Твоя реферальная ссылка:</b>\n"
        f"<code>{referral_link}</code>\n\n"

        "👇 Нажми кнопку чтобы поделиться!"
    )

    # Share button
    share_text = f"🎵 Скачивай музыку бесплатно с {bot_username}!"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📤 Поделиться ссылкой",
            url=f"https://t.me/share/url?url={referral_link}&text={share_text}"
        )]
    ])

    await message.answer(text, reply_markup=keyboard)
    logger.info(f"User {user_id} viewed referral info")
