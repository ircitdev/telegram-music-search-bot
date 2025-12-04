"""Search command handlers."""
from aiogram import Router, F
from aiogram.types import Message
from src.searchers.youtube import youtube_searcher
from src.keyboards import create_track_keyboard
from src.utils.cache import cache
from src.utils.logger import logger
from src.utils.rate_limiter import rate_limiter
from src.database.repositories import user_repo

router = Router()


@router.message(F.text)
async def text_search_handler(message: Message):
    """
    Handle text search requests.

    User sends song/artist name, bot searches YouTube and shows results.
    """
    query = message.text

    # Ignore commands
    if query.startswith('/'):
        return

    user_id = message.from_user.id
    username = message.from_user.username or ""
    logger.info(f"User {user_id} searched: {query}")

    # Check rate limit
    allowed, wait_seconds = rate_limiter.is_allowed(user_id)
    if not allowed:
        logger.warning(f"Rate limit exceeded for user {user_id}: wait {wait_seconds}s")
        await message.answer(
            f"⏳ <b>Слишком много запросов</b>\n\n"
            f"Пожалуйста, подожди {wait_seconds} секунд\n\n"
            f"<i>Лимит: {rate_limiter.max_requests} поисков в минуту</i>"
        )
        return

    # Show typing action
    await message.bot.send_chat_action(message.chat.id, "typing")

    # Search
    tracks = await youtube_searcher.search(query)

    if not tracks:
        await message.answer(
            "❌ <b>Ничего не найдено</b>\n\n"
            "💡 Попробуй:\n"
            "• Проверить правильность названия\n"
            "• Использовать английский язык\n"
            "• Написать только название песни или исполнителя"
        )
        logger.warning(f"No results found for query: {query}")
        return

    # Record search in database
    await user_repo.increment_searches(user_id)

    # Cache all results for pagination (10 minutes)
    cache_key = f"search:{user_id}"
    cache.set(cache_key, tracks, ttl=600)
    # Also cache query for display
    cache.set(f"query:{user_id}", query, ttl=600)
    logger.debug(f"Cached {len(tracks)} results for user {user_id}")

    # Show first page (tracks 1-10)
    page_tracks = tracks[:10]
    total_tracks = len(tracks)

    # Format search results with beautiful formatting
    text = f"🎵 <b>Результаты поиска:</b> <code>{query}</code>\n"
    text += f"<i>Найдено: {total_tracks} треков</i>\n\n"
    
    for i, track in enumerate(page_tracks, 1):
        # Icons for top 3 tracks
        icon = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"<b>{i}</b>."
        text += (
            f"{icon} <b>{track.artist}</b>\n"
            f"   🎤 <i>{track.title}</i>\n"
            f"   ⏱️ <code>{track.formatted_duration}</code>\n\n"
        )

    text += f"👇 <b>Выбери номер трека (1-{len(page_tracks)})</b>"
    if total_tracks > 10:
        text += f"\n📄 Страница 1/{(total_tracks + 9) // 10}"

    # Create inline keyboard with pagination
    keyboard = create_track_keyboard(page_tracks, page=0, total_tracks=total_tracks)

    await message.answer(text, reply_markup=keyboard)
    logger.info(f"Shown {len(page_tracks)}/{total_tracks} results to user {user_id}")
