"""History command handler."""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from src.database.repositories import download_repo
from src.utils.logger import logger

router = Router()


def format_duration(seconds: int) -> str:
    """Format duration as MM:SS."""
    if not seconds:
        return "0:00"
    minutes, secs = divmod(seconds, 60)
    return f"{minutes}:{secs:02d}"


@router.message(Command("history"))
async def cmd_history(message: Message):
    """Show user's download history."""
    user_id = message.from_user.id

    # Get last 20 downloads
    downloads = await download_repo.get_user_history(user_id, limit=20)

    if not downloads:
        await message.answer(
            "📜 <b>История скачиваний пуста</b>\n\n"
            "Ты ещё не скачивал треки.\n"
            "Отправь название песни, чтобы начать поиск!"
        )
        return

    text = "📜 <b>Последние 20 скачиваний:</b>\n\n"

    for i, d in enumerate(downloads, 1):
        title = d.get('title', 'Unknown')
        artist = d.get('artist', 'Unknown')
        duration = format_duration(d.get('duration', 0))
        downloaded_at = d.get('downloaded_at', '')

        # Format date nicely
        if downloaded_at:
            try:
                # SQLite returns string
                date_str = str(downloaded_at).split(' ')[0]
            except Exception:
                date_str = ""
        else:
            date_str = ""

        text += f"<b>{i}.</b> {artist} - {title}\n"
        text += f"    ⏱ {duration}"
        if date_str:
            text += f" | 📅 {date_str}"
        text += "\n\n"

    total = await download_repo.get_user_download_count(user_id)
    text += f"📊 <b>Всего скачано:</b> {total} треков"

    await message.answer(text)
    logger.info(f"User {user_id} viewed history")
