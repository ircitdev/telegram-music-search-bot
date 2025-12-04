"""Callback query handlers for inline buttons."""
import os
import asyncio
from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile
from src.downloaders.youtube_dl import youtube_downloader
from src.keyboards import create_track_keyboard
from src.utils.cache import cache
from src.utils.logger import logger
from src.config import settings
from src.database.repositories import user_repo, download_repo, stats_repo


async def check_download_limit(user_id: int) -> tuple[bool, int, int]:
    """
    Check if user can download.

    Returns:
        (can_download, remaining, used_bonus)
    """
    # Check if premium
    is_premium = await user_repo.is_premium(user_id)
    if is_premium:
        return True, -1, 0  # -1 = unlimited

    # Check daily limit
    today_count = await download_repo.get_today_count(user_id)
    remaining = settings.FREE_DAILY_LIMIT - today_count

    if remaining > 0:
        return True, remaining, 0

    # Check bonus downloads
    bonus = await user_repo.get_bonus_downloads(user_id)
    if bonus > 0:
        return True, 0, bonus

    return False, 0, 0

router = Router()


@router.callback_query(F.data.startswith("page:"))
async def pagination_callback_handler(callback: CallbackQuery):
    """Handle pagination button clicks."""
    try:
        page = int(callback.data.split(":")[1])
        user_id = callback.from_user.id

        # Get cached results
        cache_key = f"search:{user_id}"
        tracks = cache.get(cache_key)
        query = cache.get(f"query:{user_id}") or "Результаты поиска"

        if not tracks:
            await callback.answer("❌ Результаты устарели. Поищи заново.", show_alert=True)
            return

        total_tracks = len(tracks)
        start_idx = page * 10
        end_idx = min(start_idx + 10, total_tracks)
        page_tracks = tracks[start_idx:end_idx]

        if not page_tracks:
            await callback.answer("❌ Нет больше результатов")
            return

        # Format page results
        text = f"🎵 <b>{query}</b>\n\n"
        for i, track in enumerate(page_tracks, start_idx + 1):
            icon = "▫️"
            text += (
                f"{icon} <b>{i}.</b> {track.artist}\n"
                f"    📝 {track.title}\n"
                f"    ⏱ <code>{track.formatted_duration}</code>\n\n"
            )

        text += f"👇 <b>Выбери номер трека ({start_idx + 1}-{end_idx})</b>"
        text += f"\n📄 Страница {page + 1}/{(total_tracks + 9) // 10}"

        keyboard = create_track_keyboard(page_tracks, page=page, total_tracks=total_tracks)

        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        logger.info(f"User {user_id} switched to page {page + 1}")

    except Exception as e:
        logger.error(f"Pagination error: {e}")
        await callback.answer("❌ Ошибка")


@router.callback_query(F.data.startswith("track:"))
async def track_callback_handler(callback: CallbackQuery):
    """
    Handle track selection button clicks (1-10).

    User clicks button to select track number, bot downloads and sends MP3.
    """
    try:
        # Parse track number from callback data
        track_num = int(callback.data.split(":")[1])
        user_id = callback.from_user.id
        username = callback.from_user.username or ""

        logger.info(f"User {user_id} selected track #{track_num}")

        # Get search results from cache
        cache_key = f"search:{user_id}"
        tracks = cache.get(cache_key)

        if not tracks:
            logger.warning(
                f"Cache miss for user {user_id}: results expired"
            )
            await callback.answer(
                "❌ Результаты устарели. Поищи заново.",
                show_alert=True
            )
            return

        # Validate track number
        if track_num < 1 or track_num > len(tracks):
            logger.warning(
                f"User {user_id} selected invalid track #{track_num}"
            )
            await callback.answer(
                "❌ Неверный номер трека.",
                show_alert=True
            )
            return

        track = tracks[track_num - 1]

        # Check download limit
        can_download, remaining, bonus = await check_download_limit(user_id)

        if not can_download:
            await callback.answer(
                f"❌ Лимит исчерпан!\n\n"
                f"Бесплатно: {settings.FREE_DAILY_LIMIT} треков/день.\n"
                f"Лимит обновится в полночь.\n\n"
                f"⭐ /premium - безлимитный доступ",
                show_alert=True
            )
            logger.info(f"User {user_id} hit download limit")
            return

        logger.info(
            f"Downloading track for user {user_id}: "
            f"{track.artist} - {track.title}"
        )

        # Show loading message with progress indicator
        loading_text = (
            f"⏳ <b>Загрузка трека...</b>\n\n"
            f"🎵 <b>{track.title}</b>\n"
            f"👤 <i>{track.artist}</i>\n"
            f"⏱️ <code>{track.formatted_duration}</code>\n\n"
            f"<code>[████░░░░░░░░░░░░░░] 20%</code>"
        )
        await callback.message.edit_text(loading_text)

        # Download
        try:
            file_path = await youtube_downloader.download(track.id)
        except Exception as e:
            logger.error(
                f"Download failed for user {user_id}, track {track.id}: {e}"
            )
            error_msg = str(e)
            
            # More detailed error messages
            if "too large" in error_msg.lower():
                error_text = (
                    "❌ <b>Файл слишком большой</b>\n\n"
                    f"Максимальный размер: 50 MB\n"
                    f"Попробуй более короткий трек"
                )
            elif "not available" in error_msg.lower() or "unavailable" in error_msg.lower():
                error_text = (
                    "❌ <b>Трек недоступен</b>\n\n"
                    f"Видео могло быть удалено или закрыто.\n"
                    f"Попробуй другой трек"
                )
            else:
                error_text = (
                    "❌ <b>Ошибка при скачивании</b>\n\n"
                    f"Трек может быть недоступен.\n"
                    f"Попробуй другой трек"
                )
            
            await callback.message.edit_text(error_text)
            await callback.answer()
            return

        # Send audio to user
        try:
            logger.info(f"Sending audio to user {user_id}: {file_path}")

            audio_file = FSInputFile(file_path)

            await callback.message.answer_audio(
                audio=audio_file,
                performer=track.artist,
                title=track.title,
                duration=track.duration,
                caption="🎵 Любая музыка за секунды @UspMusicFinder_bot"
            )

            # Record download in database
            await download_repo.add_download(
                user_id=user_id,
                track_id=track.id,
                title=track.title,
                artist=track.artist,
                duration=track.duration
            )
            await user_repo.increment_downloads(user_id)
            await stats_repo.record_download(track.id, track.title, track.artist)

            # Update daily limit or use bonus
            if bonus > 0:
                await user_repo.use_bonus_download(user_id)
            else:
                await download_repo.increment_daily_count(user_id)

            # Delete "loading..." message
            try:
                await callback.message.delete()
            except Exception as e:
                logger.debug(f"Could not delete loading message: {e}")

            logger.info(f"Audio sent successfully to user {user_id}")

        finally:
            # Clean up temporary file
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.debug(f"Cleaned up temp file: {file_path}")
                except Exception as e:
                    logger.warning(f"Could not delete temp file {file_path}: {e}")

        await callback.answer("✅ Готово!")

    except Exception as e:
        logger.error(f"Callback handler error: {e}", exc_info=True)
        try:
            await callback.message.edit_text(
                "❌ <b>Неожиданная ошибка</b>\n\n"
                "Попробуй еще раз или выполни новый поиск."
            )
        except Exception:
            pass
        await callback.answer()
