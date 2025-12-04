"""Callback query handlers for inline buttons."""
import os
import asyncio
from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile
from src.downloaders.youtube_dl import youtube_downloader
from src.utils.cache import cache
from src.utils.logger import logger
from src.utils.stats import bot_stats

router = Router()


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
        logger.info(
            f"Downloading track for user {user_id}: "
            f"{track.artist} - {track.title}"
        )

        # Show loading message
        loading_text = (
            f"⏳ <b>Загрузка...</b>\n\n"
            f"🎵 {track.title}\n"
            f"👤 {track.artist}\n"
            f"⏱ {track.formatted_duration}"
        )
        await callback.message.edit_text(loading_text)

        # Download
        try:
            file_path = await youtube_downloader.download(track.id)
        except Exception as e:
            logger.error(
                f"Download failed for user {user_id}, track {track.id}: {e}"
            )
            await callback.message.edit_text(
                "❌ <b>Ошибка при скачивании</b>\n\n"
                f"Трек может быть недоступен или слишком большой.\n"
                f"Попробуй другой трек."
            )
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
                duration=track.duration
            )

            # Send promotional message
            promo_text = (
                "🎵 <b>Найди любую музыку за секунды!</b>\n\n"
                "Этот трек скачан с помощью бота @UspMusicFinder_bot\n\n"
                "✨ Поищи свою любимую музыку:\n"
                "/search [название трека]\n\n"
                "👉 <a href=\"https://t.me/UspMusicFinder_bot\">Открыть бота</a>"
            )
            try:
                await callback.message.answer(promo_text)
            except Exception as e:
                logger.debug(f"Could not send promotional message: {e}")

            # Record download in stats
            bot_stats.record_download(user_id, username)

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
