"""Callback query handlers for inline buttons."""
import os
import asyncio
from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from src.downloaders.youtube_dl import youtube_downloader
from src.keyboards import create_track_keyboard
from src.utils.cache import cache
from src.utils.logger import logger
from src.config import settings
from src.database.repositories import user_repo, download_repo, stats_repo


def create_after_download_keyboard(query: str = None) -> InlineKeyboardMarkup:
    """Create keyboard with actions after download."""
    buttons = []

    # Search again button
    if query:
        buttons.append([InlineKeyboardButton(
            text="🔍 Искать ещё",
            callback_data=f"search_again"
        )])

    # Popular commands
    buttons.append([
        InlineKeyboardButton(text="🏆 Топ треков", callback_data="quick:top"),
        InlineKeyboardButton(text="❤️ Избранное", callback_data="quick:favorites")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


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


async def download_and_send_track(callback: CallbackQuery, track):
    """
    Download and send track to user.

    This function is reusable for both search results and top tracks.
    """
    user_id = callback.from_user.id

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

    # Show loading message
    loading_text = (
        f"⏳ <b>Загрузка трека...</b>\n\n"
        f"🎵 <b>{track.title}</b>\n"
        f"👤 <i>{track.artist}</i>\n"
        f"⏱️ <code>{track.formatted_duration}</code>\n\n"
        f"<code>[████░░░░░░░░░░░░░░] 20%</code>"
    )

    # Edit or send new message
    try:
        await callback.message.edit_text(loading_text)
    except:
        await callback.message.answer(loading_text)

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

        try:
            await callback.message.edit_text(error_text)
        except:
            await callback.message.answer(error_text)
        await callback.answer()
        return

    # Send audio to user
    try:
        logger.info(f"Sending audio to user {user_id}: {file_path}")

        audio_file = FSInputFile(file_path)

        # Get search query for "search again" button
        query = cache.get(f"query:{user_id}")

        await callback.message.answer_audio(
            audio=audio_file,
            performer=track.artist,
            title=track.title,
            duration=track.duration,
            caption="🎵 Любая музыка за секунды @UspMusicFinder_bot",
            reply_markup=create_after_download_keyboard(query)
        )

        # Record download in database
        await download_repo.add_download(
            user_id=user_id,
            track_id=track.id,
            title=track.title,
            artist=track.artist,
            duration=track.duration
        )

        # Record in stats
        await stats_repo.record_download(
            track_id=track.id,
            title=track.title,
            artist=track.artist
        )

        # Use bonus if needed
        if bonus > 0:
            await user_repo.use_bonus_download(user_id)
            logger.info(f"Used bonus download for user {user_id}")

        # Delete loading message
        try:
            await callback.message.delete()
        except:
            pass

        await callback.answer("✅ Готово!")
        logger.info(f"Audio sent successfully to user {user_id}")

    except Exception as e:
        logger.error(f"Error sending audio: {e}")
        error_text = (
            "❌ <b>Ошибка при отправке</b>\n\n"
            f"Попробуй скачать другой трек"
        )
        try:
            await callback.message.edit_text(error_text)
        except:
            await callback.message.answer(error_text)
        await callback.answer()

    finally:
        # Clean up file
        if 'file_path' in locals() and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.debug(f"Cleaned up file: {file_path}")
            except:
                pass


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
                    f"🎵 <b>{track.title}</b>\n"
                    f"👤 <i>{track.artist}</i>\n\n"
                    f"Максимальный размер: 50 MB\n"
                    f"Попробуй более короткий трек из списка ниже"
                )
            elif "unavailable" in error_msg.lower() or "deleted" in error_msg.lower():
                error_text = (
                    "❌ <b>Трек недоступен</b>\n\n"
                    f"🎵 <b>{track.title}</b>\n"
                    f"👤 <i>{track.artist}</i>\n\n"
                    f"Видео удалено или закрыто для доступа.\n"
                    f"Попробуй другой трек из списка ниже"
                )
            elif "private" in error_msg.lower():
                error_text = (
                    "❌ <b>Видео скрыто</b>\n\n"
                    f"🎵 <b>{track.title}</b>\n"
                    f"👤 <i>{track.artist}</i>\n\n"
                    f"Это приватное видео.\n"
                    f"Попробуй другой трек из списка ниже"
                )
            elif "geo" in error_msg.lower() or "region" in error_msg.lower():
                error_text = (
                    "❌ <b>Региональные ограничения</b>\n\n"
                    f"🎵 <b>{track.title}</b>\n"
                    f"👤 <i>{track.artist}</i>\n\n"
                    f"Видео недоступно в твоем регионе.\n"
                    f"Попробуй другой трек из списка ниже"
                )
            elif "copyright" in error_msg.lower():
                error_text = (
                    "❌ <b>Защита авторских прав</b>\n\n"
                    f"🎵 <b>{track.title}</b>\n"
                    f"👤 <i>{track.artist}</i>\n\n"
                    f"Видео заблокировано правообладателем.\n"
                    f"Попробуй другой трек из списка ниже"
                )
            else:
                error_text = (
                    "❌ <b>Ошибка при скачивании</b>\n\n"
                    f"🎵 <b>{track.title}</b>\n"
                    f"👤 <i>{track.artist}</i>\n\n"
                    f"Не удалось скачать трек.\n"
                    f"Попробуй другой трек из списка ниже"
                )

            # Show search results again with error message
            cache_key = f"search:{user_id}"
            tracks = cache.get(cache_key)

            if tracks:
                error_text += f"\n\n<i>Или выполни новый поиск командой /start</i>"
                # Get query for keyboard
                query = cache.get(f"query:{user_id}")
                keyboard = create_track_keyboard(tracks[:10], page=0, total_tracks=len(tracks))
                await callback.message.edit_text(error_text, reply_markup=keyboard)
            else:
                await callback.message.edit_text(error_text)

            await callback.answer()
            return

        # Send audio to user
        try:
            logger.info(f"Sending audio to user {user_id}: {file_path}")

            audio_file = FSInputFile(file_path)

            # Get search query for "search again" button
            query = cache.get(f"query:{user_id}")

            await callback.message.answer_audio(
                audio=audio_file,
                performer=track.artist,
                title=track.title,
                duration=track.duration,
                caption="🎵 Любая музыка за секунды @UspMusicFinder_bot",
                reply_markup=create_after_download_keyboard(query)
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


@router.callback_query(F.data == "search_again")
async def search_again_callback(callback: CallbackQuery):
    """Handle 'Search again' button - show previous search results."""
    user_id = callback.from_user.id

    # Get cached results
    cache_key = f"search:{user_id}"
    tracks = cache.get(cache_key)
    query = cache.get(f"query:{user_id}") or "Результаты поиска"

    if not tracks:
        await callback.answer("🔍 Введи название трека для поиска", show_alert=True)
        return

    # Show first page of results
    total_tracks = len(tracks)
    page_tracks = tracks[:10]

    text = f"🎵 <b>{query}</b>\n\n"
    for i, track in enumerate(page_tracks, 1):
        text += (
            f"▫️ <b>{i}.</b> {track.artist}\n"
            f"    📝 {track.title}\n"
            f"    ⏱ <code>{track.formatted_duration}</code>\n\n"
        )

    text += f"👇 <b>Выбери номер трека (1-{len(page_tracks)})</b>"
    if total_tracks > 10:
        text += f"\n📄 Страница 1/{(total_tracks + 9) // 10}"

    keyboard = create_track_keyboard(page_tracks, page=0, total_tracks=total_tracks)

    await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()
    logger.info(f"User {user_id} used 'search again' button")


@router.callback_query(F.data.startswith("quick:"))
async def quick_command_callback(callback: CallbackQuery):
    """Handle quick command buttons."""
    command = callback.data.split(":")[1]
    user_id = callback.from_user.id

    if command == "top":
        # Show top tracks menu
        from src.handlers.top import create_period_keyboard
        text = (
            "🏆 <b>ТОП СКАЧИВАЕМЫХ ТРЕКОВ</b>\n\n"
            "Выбери период:"
        )
        keyboard = create_period_keyboard()
        await callback.message.answer(text, reply_markup=keyboard)
        await callback.answer()
        logger.info(f"User {user_id} clicked quick:top")

    elif command == "favorites":
        # Show favorites
        from src.database.repositories import favorites_repo
        favorites = await favorites_repo.get_favorites(user_id, limit=10)

        if not favorites:
            await callback.answer("❤️ У тебя пока нет избранных треков", show_alert=True)
            return

        text = "❤️ <b>ИЗБРАННОЕ</b>\n\n"
        for i, fav in enumerate(favorites, 1):
            text += f"{i}. <b>{fav['artist']}</b> — {fav['title']}\n"

        text += "\n/favorites - показать всё"
        await callback.message.answer(text)
        await callback.answer()
        logger.info(f"User {user_id} clicked quick:favorites")

    elif command == "history":
        # Show history
        from src.database.repositories import download_repo
        downloads = await download_repo.get_user_downloads(user_id, limit=10)

        if not downloads:
            await callback.answer("📜 История пуста", show_alert=True)
            return

        text = "📜 <b>ПОСЛЕДНИЕ СКАЧИВАНИЯ</b>\n\n"
        for i, d in enumerate(downloads, 1):
            text += f"{i}. <b>{d['artist']}</b> — {d['title']}\n"

        text += "\n/history - показать всё"
        await callback.message.answer(text)
        await callback.answer()
        logger.info(f"User {user_id} clicked quick:history")
