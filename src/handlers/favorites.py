"""Favorites command and callback handlers."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from src.database.repositories import favorite_repo
from src.utils.cache import cache
from src.utils.logger import logger

router = Router()


def format_duration(seconds: int) -> str:
    """Format duration as MM:SS."""
    if not seconds:
        return "0:00"
    minutes, secs = divmod(seconds, 60)
    return f"{minutes}:{secs:02d}"


@router.message(Command("favorites"))
async def cmd_favorites(message: Message):
    """Show user's favorites."""
    user_id = message.from_user.id

    favorites = await favorite_repo.get_favorites(user_id, limit=20)

    if not favorites:
        await message.answer(
            "❤️ <b>Избранное пусто</b>\n\n"
            "Добавляй треки в избранное кнопкой ❤️\n"
            "при просмотре результатов поиска."
        )
        return

    text = "❤️ <b>Избранное:</b>\n\n"

    # Store favorites in cache for download buttons
    cache_key = f"favorites:{user_id}"
    cache.set(cache_key, favorites, ttl=600)

    for i, fav in enumerate(favorites, 1):
        title = fav.get('title', 'Unknown')
        artist = fav.get('artist', 'Unknown')
        duration = format_duration(fav.get('duration', 0))

        text += f"<b>{i}.</b> {artist} - {title}\n"
        text += f"    ⏱ {duration}\n\n"

    # Create keyboard with download buttons
    buttons = []
    row = []
    for i in range(1, min(len(favorites) + 1, 11)):
        row.append(InlineKeyboardButton(
            text=str(i),
            callback_data=f"fav_dl:{i}"
        ))
        if len(row) == 5:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    # Add clear all button
    buttons.append([
        InlineKeyboardButton(text="🗑 Очистить всё", callback_data="fav_clear")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    total = await favorite_repo.get_favorites_count(user_id)
    text += f"📊 <b>Всего в избранном:</b> {total}\n\n"
    text += "👇 <b>Нажми номер чтобы скачать</b>"

    await message.answer(text, reply_markup=keyboard)
    logger.info(f"User {user_id} viewed favorites")


@router.callback_query(F.data.startswith("fav:"))
async def add_to_favorites_callback(callback: CallbackQuery):
    """Handle adding track to favorites."""
    user_id = callback.from_user.id

    try:
        track_num = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка")
        return

    # Get tracks from search cache
    cache_key = f"search:{user_id}"
    tracks = cache.get(cache_key)

    if not tracks:
        await callback.answer("❌ Результаты устарели", show_alert=True)
        return

    if track_num < 1 or track_num > len(tracks):
        await callback.answer("❌ Неверный номер")
        return

    track = tracks[track_num - 1]

    # Toggle favorite
    added = await favorite_repo.toggle_favorite(
        user_id=user_id,
        track_id=track.id,
        title=track.title,
        artist=track.artist,
        duration=track.duration
    )

    if added:
        await callback.answer("❤️ Добавлено в избранное!")
        logger.info(f"User {user_id} added to favorites: {track.title}")
    else:
        await callback.answer("💔 Удалено из избранного")
        logger.info(f"User {user_id} removed from favorites: {track.title}")


@router.callback_query(F.data.startswith("fav_dl:"))
async def download_from_favorites_callback(callback: CallbackQuery):
    """Handle download from favorites list."""
    from src.downloaders.youtube_dl import youtube_downloader
    from src.database.repositories import download_repo, user_repo, stats_repo
    from aiogram.types import FSInputFile
    import os

    user_id = callback.from_user.id

    try:
        track_num = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка")
        return

    # Get favorites from cache
    cache_key = f"favorites:{user_id}"
    favorites = cache.get(cache_key)

    if not favorites:
        await callback.answer("❌ Обнови список /favorites", show_alert=True)
        return

    if track_num < 1 or track_num > len(favorites):
        await callback.answer("❌ Неверный номер")
        return

    fav = favorites[track_num - 1]
    track_id = fav.get('track_id')
    title = fav.get('title', 'Unknown')
    artist = fav.get('artist', 'Unknown')
    duration = fav.get('duration', 0)

    # Show loading
    await callback.message.edit_text(
        f"⏳ <b>Загрузка...</b>\n\n"
        f"🎵 {title}\n"
        f"👤 {artist}"
    )

    try:
        file_path = await youtube_downloader.download(track_id)

        audio_file = FSInputFile(file_path)
        await callback.message.answer_audio(
            audio=audio_file,
            performer=artist,
            title=title,
            duration=duration,
            caption="🎵 Любая музыка за секунды @UspMusicFinder_bot"
        )

        # Record download
        await download_repo.add_download(user_id, track_id, title, artist, duration)
        await user_repo.increment_downloads(user_id)
        await stats_repo.record_download(track_id, title, artist)

        # Delete loading message
        try:
            await callback.message.delete()
        except Exception:
            pass

        await callback.answer("✅ Готово!")
        logger.info(f"User {user_id} downloaded from favorites: {title}")

    except Exception as e:
        logger.error(f"Favorites download error: {e}")
        await callback.message.edit_text(
            "❌ <b>Ошибка при скачивании</b>\n\n"
            "Трек недоступен. Попробуй другой."
        )
        await callback.answer()

    finally:
        if 'file_path' in locals() and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass


@router.callback_query(F.data == "fav_clear")
async def clear_favorites_callback(callback: CallbackQuery):
    """Handle clear all favorites."""
    user_id = callback.from_user.id

    # Get all favorites and remove them
    favorites = await favorite_repo.get_favorites(user_id)

    for fav in favorites:
        await favorite_repo.remove_favorite(user_id, fav['track_id'])

    await callback.message.edit_text(
        "🗑 <b>Избранное очищено</b>\n\n"
        "Все треки удалены из избранного."
    )
    await callback.answer("✅ Избранное очищено")
    logger.info(f"User {user_id} cleared favorites")
