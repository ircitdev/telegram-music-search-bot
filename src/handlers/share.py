"""Share track functionality with deep linking."""
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from src.utils.logger import logger
from src.config import settings

router = Router()


def create_share_button(track_id: str, artist: str, title: str) -> InlineKeyboardMarkup:
    """
    Create share button for a track.

    Uses Telegram deep linking: t.me/bot?start=track_{track_id}
    """
    bot_username = settings.BOT_USERNAME
    share_link = f"https://t.me/{bot_username}?start=track_{track_id}"

    # Create shareable message text
    share_text = f"🎵 {artist} - {title}\n\nСкачай эту песню через @{bot_username}!"

    # Create share button using Telegram's share URL API
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📤 Поделиться треком",
            url=f"https://t.me/share/url?url={share_link}&text={share_text}"
        )]
    ])

    return keyboard


@router.callback_query(F.data.startswith("share:"))
async def share_track_callback(callback: CallbackQuery):
    """Handle share track button."""
    try:
        # Parse track data from callback
        # Format: share:track_id:artist:title
        parts = callback.data.split(":", 3)

        if len(parts) < 4:
            await callback.answer("❌ Ошибка данных трека", show_alert=True)
            return

        track_id = parts[1]
        artist = parts[2]
        title = parts[3]

        bot_username = settings.BOT_USERNAME
        share_link = f"https://t.me/{bot_username}?start=track_{track_id}"

        # Show share info
        text = (
            f"📤 <b>ПОДЕЛИТЬСЯ ТРЕКОМ</b>\n\n"
            f"🎵 <b>{artist}</b> — {title}\n\n"
            f"Отправь эту ссылку друзьям:\n"
            f"<code>{share_link}</code>\n\n"
            f"Или используй кнопку ниже для быстрого шаринга!"
        )

        share_text = f"🎵 {artist} - {title}\n\nСкачай эту песню через @{bot_username}!"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="📤 Поделиться в Telegram",
                url=f"https://t.me/share/url?url={share_link}&text={share_text}"
            )]
        ])

        await callback.message.answer(text, reply_markup=keyboard)
        await callback.answer()

        logger.info(f"User {callback.from_user.id} requested share for track {track_id}")

    except Exception as e:
        logger.error(f"Share track error: {e}")
        await callback.answer("❌ Ошибка при создании ссылки", show_alert=True)
