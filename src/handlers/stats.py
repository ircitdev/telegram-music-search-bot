"""User statistics command handler."""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from datetime import datetime

from src.database.repositories import download_repo, user_repo
from src.utils.logger import logger

router = Router()


def format_duration_hours(seconds: int) -> str:
    """Format duration as hours and minutes."""
    if not seconds:
        return "0 минут"

    hours, remainder = divmod(seconds, 3600)
    minutes = remainder // 60

    if hours > 0:
        return f"{hours} ч {minutes} мин"
    else:
        return f"{minutes} мин"


@router.message(Command("my_stats"))
async def cmd_my_stats(message: Message):
    """Show user's listening statistics."""
    user_id = message.from_user.id

    try:
        # Get total downloads
        total_downloads = await download_repo.get_user_download_count(user_id)

        if total_downloads == 0:
            await message.answer(
                "📊 <b>ТВОЯ СТАТИСТИКА</b>\n\n"
                "У тебя пока нет скачиваний.\n"
                "Отправь название песни, чтобы начать поиск!"
            )
            return

        # Get user info
        user = await user_repo.get_user(user_id)
        is_premium = await user_repo.is_premium(user_id)

        # Get top artists
        top_artists = await download_repo.get_user_top_artists(user_id, limit=5)

        # Get total listening time
        total_seconds = await download_repo.get_user_total_duration(user_id)
        total_time = format_duration_hours(total_seconds)

        # Build stats message
        text = "📊 <b>ТВОЯ СТАТИСТИКА</b>\n\n"

        # Basic stats
        text += f"🎵 Треков скачано: <b>{total_downloads}</b>\n"
        text += f"⏱ Всего времени: <b>{total_time}</b>\n\n"

        # Top artists
        if top_artists:
            text += "🎤 <b>Топ артистов:</b>\n"
            for i, artist_data in enumerate(top_artists, 1):
                artist = artist_data['artist']
                count = artist_data['count']
                text += f"{i}. {artist} ({count} треков)\n"
            text += "\n"

        # Account info
        if user:
            created_at = user.get('created_at', '')
            if created_at:
                try:
                    # Parse date
                    date_str = str(created_at).split(' ')[0]
                    text += f"📅 С нами с: <b>{date_str}</b>\n"
                except Exception:
                    pass

        # Premium status
        if is_premium:
            premium_until = user.get('premium_until', '') if user else ''
            if premium_until:
                try:
                    date_str = str(premium_until).split(' ')[0]
                    text += f"👑 Статус: <b>Premium до {date_str}</b>\n"
                except Exception:
                    text += "👑 Статус: <b>Premium</b>\n"
            else:
                text += "👑 Статус: <b>Premium</b>\n"
        else:
            text += "🆓 Статус: <b>Free</b>\n"

        await message.answer(text)
        logger.info(f"User {user_id} viewed their stats")

    except Exception as e:
        logger.error(f"Error showing stats for user {user_id}: {e}")
        await message.answer(
            "❌ Произошла ошибка при загрузке статистики.\n"
            "Попробуй позже."
        )
