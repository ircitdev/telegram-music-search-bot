"""Start command handlers."""
import os
from aiogram import Router, F
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton

from src.database.repositories import user_repo, download_repo, stats_repo
from src.utils.logger import logger
from src.searchers.youtube import youtube_searcher
from src.downloaders.youtube_dl import youtube_downloader
from src.config import settings

router = Router()


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Create main reply keyboard with popular commands."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🏆 Топ треков"),
                KeyboardButton(text="🎵 Рекомендации"),
            ],
            [
                KeyboardButton(text="📜 История"),
                KeyboardButton(text="❤️ Избранное"),
            ],
            [
                KeyboardButton(text="⭐ Премиум"),
                KeyboardButton(text="👥 Рефералы"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="🔍 Введи название песни..."
    )


async def check_download_limit(user_id: int) -> tuple[bool, int, int]:
    """
    Check if user can download.
    Returns: (can_download, remaining, used_bonus)
    """
    is_premium = await user_repo.is_premium(user_id)
    if is_premium:
        return True, -1, 0

    today_count = await download_repo.get_today_count(user_id)
    remaining = settings.FREE_DAILY_LIMIT - today_count

    if remaining > 0:
        return True, remaining, 0

    bonus = await user_repo.get_bonus_downloads(user_id)
    if bonus > 0:
        return True, 0, bonus

    return False, 0, 0


async def auto_search_and_download(message: Message, query: str, source: str = "deep_link"):
    """
    Автоматический поиск и скачивание первого трека.
    Используется для deep link интеграций (Mira Bot и др.)
    """
    user_id = message.from_user.id

    # Show searching message
    source_text = "⚡ Быстрое скачивание" if source == "get_command" else "Запрос от интеграции"
    status_msg = await message.answer(
        f"🔍 <b>Ищу:</b> <code>{query}</code>\n"
        f"<i>{source_text}</i>",
        reply_markup=get_main_keyboard()
    )

    # Check download limit
    can_download, remaining, bonus = await check_download_limit(user_id)
    if not can_download:
        await status_msg.edit_text(
            f"❌ <b>Лимит исчерпан!</b>\n\n"
            f"Бесплатно: {settings.FREE_DAILY_LIMIT} треков/день.\n"
            f"Лимит обновится в полночь.\n\n"
            f"⭐ /premium - безлимитный доступ"
        )
        return

    # Search
    try:
        tracks = await youtube_searcher.search(query)
    except Exception as e:
        logger.error(f"Search error for deep link query '{query}': {e}")
        await status_msg.edit_text(
            f"❌ <b>Ошибка поиска</b>\n\n"
            f"Попробуй написать название вручную."
        )
        return

    if not tracks:
        await status_msg.edit_text(
            f"😔 <b>Не удалось найти:</b> {query}\n\n"
            f"💡 Попробуй написать название иначе или найти вручную."
        )
        return

    # Take first track
    track = tracks[0]
    logger.info(f"Deep link auto-download for {user_id}: {track.artist} - {track.title}")

    # Update status
    await status_msg.edit_text(
        f"⏳ <b>Загрузка трека...</b>\n\n"
        f"🎵 <b>{track.title}</b>\n"
        f"👤 <i>{track.artist}</i>\n"
        f"⏱️ <code>{track.formatted_duration}</code>\n\n"
        f"<code>[████░░░░░░░░░░░░░░] 20%</code>"
    )

    # Download
    try:
        file_path = await youtube_downloader.download(track.id)
    except Exception as e:
        logger.error(f"Download error for deep link: {e}")
        error_msg = str(e)

        if "too large" in error_msg.lower():
            error_text = "❌ <b>Файл слишком большой</b>\n\nПопробуй более короткий трек"
        elif "not available" in error_msg.lower():
            error_text = "❌ <b>Трек недоступен</b>\n\nПопробуй другой трек"
        else:
            error_text = "❌ <b>Ошибка при скачивании</b>\n\nПопробуй другой трек"

        await status_msg.edit_text(error_text)
        return

    # Send audio
    try:
        audio_file = FSInputFile(file_path)

        # Keyboard for after download
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎬 Смотреть видео", url=f"https://youtube.com/watch?v={track.id}")],
            [InlineKeyboardButton(text="🔍 Искать ещё", callback_data="search_again")],
            [
                InlineKeyboardButton(text="🏆 Топ треков", callback_data="quick:top"),
                InlineKeyboardButton(text="❤️ Избранное", callback_data="quick:favorites")
            ]
        ])

        caption_text = "⚡ Быстрое скачивание /get" if source == "get_command" else "🎵 Найдено через интеграцию"
        await message.answer_audio(
            audio=audio_file,
            performer=track.artist,
            title=track.title,
            duration=track.duration,
            caption=f"{caption_text}\n\n"
                    f"Любая музыка за секунды @UspMusicFinder_bot",
            reply_markup=keyboard
        )

        # Record download
        await download_repo.add_download(
            user_id=user_id,
            track_id=track.id,
            title=track.title,
            artist=track.artist,
            duration=track.duration
        )
        await user_repo.increment_downloads(user_id)
        await stats_repo.record_download(track.id, track.title, track.artist)

        # Update limits
        if bonus > 0:
            await user_repo.use_bonus_download(user_id)
        else:
            await download_repo.increment_daily_count(user_id)

        # Delete loading message
        try:
            await status_msg.delete()
        except:
            pass

        logger.info(f"Deep link download completed for {user_id}: {track.title}")

    except Exception as e:
        logger.error(f"Error sending audio from deep link: {e}")
        await status_msg.edit_text("❌ <b>Ошибка при отправке</b>\n\nПопробуй скачать другой трек")

    finally:
        if 'file_path' in locals() and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    """Handle /start command with optional deep link parameter."""
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""

    # Get deep link parameter
    args = command.args

    # Parse referral code from /start ref_USER_ID
    referrer_id = None
    is_search_query = False
    search_query = None

    if args:
        if args.startswith("ref_"):
            # Referral link
            try:
                referrer_id = int(args.replace("ref_", ""))
            except:
                pass
        elif args.startswith("track_"):
            # Shared track link (existing functionality)
            pass
        else:
            # Deep link with search query (e.g., from Mira Bot)
            is_search_query = True
            search_query = args

    # Register user in database
    is_new = await user_repo.create_user(user_id, username, first_name, referrer_id)

    if is_new and referrer_id and referrer_id != user_id:
        # Award referrer with bonus
        await user_repo.add_bonus_downloads(referrer_id, 5)
        from src.bot import bot
        try:
            await bot.send_message(
                referrer_id,
                f"🎉 <b>Новый реферал!</b>\n\n"
                f"Пользователь {first_name} присоединился по твоей ссылке.\n"
                f"Ты получил +5 бонусных скачиваний!"
            )
        except:
            pass
        logger.info(f"User {user_id} registered via referral from {referrer_id}")

    logger.info(f"User {user_id} started bot (args: {args})")

    # If deep link with search query - auto search and download
    if is_search_query and search_query:
        logger.info(f"Deep link search for {user_id}: {search_query}")
        await auto_search_and_download(message, search_query)
        return

    # Normal welcome message
    await message.answer(
        "🎵 <b>Добро пожаловать в UspMusicFinder Bot!</b>\n\n"
        "Я помогу тебе найти и скачать музыку с YouTube Music.\n\n"
        "<b>Как пользоваться:</b>\n"
        "1️⃣ Отправь мне название песни или исполнителя\n"
        "2️⃣ Выбери трек из списка (кнопки 1-10)\n"
        "3️⃣ Получи MP3 файл!\n\n"
        "💡 Используй кнопки меню или просто напиши название песни!\n\n"
        "Попробуй поискать песню! 🎶",
        reply_markup=get_main_keyboard()
    )


@router.message(Command("get"))
async def cmd_get(message: Message, command: CommandObject):
    """
    Handle /get command - instant search and download first result.
    Usage: /get Coldplay Yellow
    Alternative method for auto-download (works for existing users).
    """
    query = command.args

    if not query:
        await message.answer(
            "⚡ <b>Быстрое скачивание</b>\n\n"
            "Используй: <code>/get название песни</code>\n\n"
            "<b>Примеры:</b>\n"
            "• <code>/get Coldplay Yellow</code>\n"
            "• <code>/get Queen Bohemian Rhapsody</code>\n"
            "• <code>/get Кино Группа крови</code>\n\n"
            "Я найду и скачаю первый подходящий трек автоматически!"
        )
        return

    logger.info(f"User {message.from_user.id} used /get command: {query}")
    await auto_search_and_download(message, query, source="get_command")


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command."""
    await message.answer(
        "🎵 <b>UspMusicFinder Bot - Help</b>\n\n"

        "<b>🔍 Как пользоваться:</b>\n"
        "1️⃣ Отправь название песни или исполнителя\n"
        "2️⃣ Нажми кнопку номера трека (1-10)\n"
        "3️⃣ Получи MP3 файл с метаданными!\n\n"

        "<b>📝 Примеры поиска:</b>\n"
        "• Bohemian Rhapsody\n"
        "• Queen\n"
        "• The Beatles Help\n\n"

        "<b>⚡ Команды:</b>\n"
        "  /start - Начать работу\n"
        "  /help - Эта справка\n"
        "  /get название - Быстрое скачивание ⚡\n"
        "  /top - Популярные песни по странам 🔥\n"
        "  /recommendations - Персональные рекомендации 🎵\n"
        "  /history - История поиска\n"
        "  /favorites - Избранные песни\n"
        "  /referral - Реферальная программа\n\n"

        "<b>✨ Возможности:</b>\n"
        "  🔍 Поиск по названию песни или исполнителю\n"
        "  ⬇️ Скачивание MP3 качество 192 kbps\n"
        "  📊 Просмотр популярных треков\n"
        "  🎯 Инлайн режим: <code>@UspMusicFinder_bot название</code>\n\n"

        "<b>Ограничения:</b>\n"
        "  • Максимум 5 поисков в минуту\n"
        "  • Максимальный размер файла: 50 MB\n"
        "  • Максимальная длительность: 10 минут\n\n"

        "<b>Поддерживаемые источники:</b>\n"
        "  • YouTube Music (основной источник)\n\n"

        "💡 <b>Совет:</b> Будь конкретен в запросе для лучших результатов!"
    )


# ============== Quick Reply Keyboard Handlers ==============

@router.message(F.text == "🏆 Топ треков")
async def quick_top_handler(message: Message):
    """Handle Top tracks quick button."""
    from src.handlers.top import top_command
    await top_command(message)


@router.message(F.text == "🎵 Рекомендации")
async def quick_recommendations_handler(message: Message):
    """Handle Recommendations quick button."""
    from src.handlers.recommendations import recommendations_command
    await recommendations_command(message)


@router.message(F.text == "📜 История")
async def quick_history_handler(message: Message):
    """Handle History quick button."""
    from src.handlers.history import cmd_history
    await cmd_history(message)


@router.message(F.text == "❤️ Избранное")
async def quick_favorites_handler(message: Message):
    """Handle Favorites quick button."""
    from src.handlers.favorites import cmd_favorites
    await cmd_favorites(message)


@router.message(F.text == "⭐ Премиум")
async def quick_premium_handler(message: Message):
    """Handle Premium quick button."""
    from src.handlers.premium import premium_command
    await premium_command(message)


@router.message(F.text == "👥 Рефералы")
async def quick_referral_handler(message: Message):
    """Handle Referral quick button."""
    from src.handlers.referral import referral_command
    await referral_command(message)
