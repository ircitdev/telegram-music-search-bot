"""Top tracks handler."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from src.database.repositories import stats_repo
from src.utils.logger import logger
from src.models import Track
from src.utils.cache import cache

router = Router()


def create_period_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for period selection."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📅 Сегодня", callback_data="top:day"),
            InlineKeyboardButton(text="📆 Неделя", callback_data="top:week"),
        ],
        [
            InlineKeyboardButton(text="📊 Месяц", callback_data="top:month"),
            InlineKeyboardButton(text="🏆 Все время", callback_data="top:all"),
        ]
    ])


def create_top_keyboard(tracks: list, offset: int = 0) -> InlineKeyboardMarkup:
    """Create keyboard with numbered buttons for tracks."""
    buttons = []

    # First row: buttons 1-5
    row1 = []
    for i in range(min(5, len(tracks) - offset)):
        row1.append(InlineKeyboardButton(
            text=str(offset + i + 1),
            callback_data=f"top_dl:{offset + i}"
        ))

    # Second row: buttons 6-10
    row2 = []
    for i in range(5, min(10, len(tracks) - offset)):
        row2.append(InlineKeyboardButton(
            text=str(offset + i + 1),
            callback_data=f"top_dl:{offset + i}"
        ))

    if row1:
        buttons.append(row1)
    if row2:
        buttons.append(row2)

    # Navigation row
    nav_row = []
    if offset > 0:
        nav_row.append(InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=f"top_page:{max(0, offset - 10)}"
        ))
    if offset + 10 < len(tracks):
        nav_row.append(InlineKeyboardButton(
            text="Вперед ▶️",
            callback_data=f"top_page:{offset + 10}"
        ))

    if nav_row:
        buttons.append(nav_row)

    # Back to periods button
    buttons.append([
        InlineKeyboardButton(text="🔙 Выбрать период", callback_data="top:menu")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("top"))
async def top_command(message: Message):
    """Show top tracks menu."""
    text = (
        "🏆 <b>ТОП СКАЧИВАЕМЫХ ТРЕКОВ</b>\n\n"
        "Выбери период:"
    )

    keyboard = create_period_keyboard()
    await message.answer(text, reply_markup=keyboard)
    logger.info(f"User {message.from_user.id} requested top tracks")


@router.callback_query(F.data == "top:menu")
async def top_menu_callback(callback: CallbackQuery):
    """Show period selection menu."""
    text = (
        "🏆 <b>ТОП СКАЧИВАЕМЫХ ТРЕКОВ</b>\n\n"
        "Выбери период:"
    )

    keyboard = create_period_keyboard()
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("top:"))
async def top_period_callback(callback: CallbackQuery):
    """Show top tracks for selected period."""
    period = callback.data.split(":")[1]

    if period == "menu":
        return

    # Period names
    period_names = {
        "day": "За сегодня",
        "week": "За неделю",
        "month": "За месяц",
        "all": "За все время"
    }

    await callback.message.edit_text("⏳ Загрузка топа...")

    # Get top tracks
    tracks = await stats_repo.get_top_tracks(limit=20, period=period)

    if not tracks:
        await callback.message.edit_text(
            f"📭 <b>Топ {period_names.get(period, period).lower()}</b>\n\n"
            f"Пока нет скачиваний за этот период."
        )
        await callback.answer()
        return

    # Cache tracks for download
    cache_key = f"top:{callback.from_user.id}:{period}"

    # Convert to Track objects
    track_objects = []
    for t in tracks:
        track = Track(
            id=t["track_id"],
            title=t["title"],
            artist=t.get("artist") or "Unknown",
            duration=t.get("duration") or 0,
            url=f"https://youtube.com/watch?v={t['track_id']}"
        )
        track_objects.append(track)

    cache.set(cache_key, track_objects, ttl=3600)  # 1 hour

    # Format message
    text = f"🏆 <b>ТОП-{len(tracks)} {period_names[period].upper()}</b>\n\n"

    for i, t in enumerate(tracks[:10], 1):
        # Medals for top 3
        if i == 1:
            icon = "🥇"
        elif i == 2:
            icon = "🥈"
        elif i == 3:
            icon = "🥉"
        else:
            icon = f"{i}."

        artist = t.get("artist") or "Unknown"
        title = t["title"]
        count = t["download_count"]

        text += f"{icon} <b>{artist}</b> — {title}\n"
        text += f"    ⬇️ {count} скачиваний\n\n"

    text += "👇 Выбери номер трека для скачивания"

    keyboard = create_top_keyboard(track_objects)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()
    logger.info(f"User {callback.from_user.id} viewed top tracks: {period}")


@router.callback_query(F.data.startswith("top_dl:"))
async def top_download_callback(callback: CallbackQuery):
    """Download track from top list."""
    try:
        track_index = int(callback.data.split(":")[1])

        # Get tracks from cache
        # Try to find in any period cache
        track_objects = None
        period = None
        for p in ["day", "week", "month", "all"]:
            cache_key = f"top:{callback.from_user.id}:{p}"
            cached = cache.get(cache_key)
            if cached:
                track_objects = cached
                period = p
                break

        if not track_objects or track_index >= len(track_objects):
            await callback.answer("❌ Результаты устарели. Выбери период заново.", show_alert=True)
            return

        track = track_objects[track_index]

        # Import here to avoid circular dependency
        from src.handlers.callbacks import download_and_send_track

        await download_and_send_track(callback, track)

    except Exception as e:
        logger.error(f"Top download error: {e}")
        await callback.answer("❌ Ошибка при скачивании", show_alert=True)


@router.callback_query(F.data.startswith("top_page:"))
async def top_page_callback(callback: CallbackQuery):
    """Navigate between pages of top tracks."""
    offset = int(callback.data.split(":")[1])

    # Get tracks from cache
    track_objects = None
    period = None
    period_names = {
        "day": "За сегодня",
        "week": "За неделю",
        "month": "За месяц",
        "all": "За все время"
    }

    for p in ["day", "week", "month", "all"]:
        cache_key = f"top:{callback.from_user.id}:{p}"
        cached = cache.get(cache_key)
        if cached:
            track_objects = cached
            period = p
            break

    if not track_objects:
        await callback.answer("❌ Результаты устарели. Выбери период заново.", show_alert=True)
        return

    # Re-fetch from database to get download counts
    tracks = await stats_repo.get_top_tracks(limit=20, period=period)

    # Format message for this page
    text = f"🏆 <b>ТОП-{len(tracks)} {period_names[period].upper()}</b>\n\n"

    end = min(offset + 10, len(tracks))
    for i in range(offset, end):
        t = tracks[i]
        pos = i + 1

        # Medals for top 3
        if pos == 1:
            icon = "🥇"
        elif pos == 2:
            icon = "🥈"
        elif pos == 3:
            icon = "🥉"
        else:
            icon = f"{pos}."

        artist = t.get("artist") or "Unknown"
        title = t["title"]
        count = t["download_count"]

        text += f"{icon} <b>{artist}</b> — {title}\n"
        text += f"    ⬇️ {count} скачиваний\n\n"

    text += "👇 Выбери номер трека для скачивания"

    keyboard = create_top_keyboard(track_objects, offset)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()
