"""API handler for external bot requests.

Allows other Telegram bots to request music downloads.
Usage: Send message to this bot with format:
  /api <chat_id> <api_key> <query>

The bot will search, download and send the audio to the specified chat_id.
"""
from aiogram import Router, F, Bot
from aiogram.types import Message, FSInputFile
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
import os
import asyncio

from src.config import settings
from src.searchers.youtube import youtube_searcher
from src.downloaders import youtube_downloader as downloader
from src.utils.logger import logger

router = Router()

# API keys for authorized bots (bot_id -> api_key)
# In production, store in database or .env
API_KEYS = {
    # "bot_id": "api_key"
    # Will be loaded from settings
}


def get_api_keys() -> dict:
    """Load API keys from settings."""
    keys = {}
    # Format in .env: API_KEYS=bot1:key1,bot2:key2
    api_keys_str = getattr(settings, 'API_KEYS', '')
    if api_keys_str:
        for pair in api_keys_str.split(','):
            if ':' in pair:
                bot_id, key = pair.split(':', 1)
                keys[bot_id.strip()] = key.strip()
    return keys


def verify_api_key(api_key: str) -> bool:
    """Verify if API key is valid."""
    keys = get_api_keys()
    # If no keys configured, use admin IDs as fallback auth
    if not keys:
        return False
    return api_key in keys.values()


@router.message(F.text.startswith('/api '))
async def api_request_handler(message: Message, bot: Bot):
    """
    Handle API requests from other bots.

    Format: /api <target_chat_id> <api_key> <search_query>

    Example: /api 123456789 myapikey123 Linkin Park Numb

    The bot will:
    1. Verify API key
    2. Search for the track
    3. Download best match
    4. Send audio to target_chat_id
    5. Reply with status to requester
    """
    try:
        # Parse command
        parts = message.text.split(' ', 3)

        if len(parts) < 4:
            await message.answer(
                "❌ <b>Неверный формат</b>\n\n"
                "Использование:\n"
                "<code>/api &lt;chat_id&gt; &lt;api_key&gt; &lt;запрос&gt;</code>\n\n"
                "Пример:\n"
                "<code>/api 123456789 mykey Linkin Park Numb</code>"
            )
            return

        _, target_chat_id_str, api_key, query = parts

        # Validate chat_id
        try:
            target_chat_id = int(target_chat_id_str)
        except ValueError:
            await message.answer("❌ Неверный chat_id. Должно быть число.")
            return

        # Verify API key
        if not verify_api_key(api_key):
            logger.warning(f"Invalid API key attempt from user {message.from_user.id}")
            await message.answer("❌ Неверный API ключ.")
            return

        logger.info(f"API request: chat_id={target_chat_id}, query='{query}'")

        # Send processing status
        status_msg = await message.answer(
            f"🔍 <b>Обрабатываю запрос...</b>\n"
            f"Запрос: <code>{query}</code>\n"
            f"Целевой чат: <code>{target_chat_id}</code>"
        )

        # Search for tracks
        tracks = await youtube_searcher.search(query)

        if not tracks:
            await status_msg.edit_text(
                f"❌ <b>Ничего не найдено</b>\n"
                f"Запрос: <code>{query}</code>"
            )
            return

        # Take the best match (first result)
        track = tracks[0]

        await status_msg.edit_text(
            f"📥 <b>Скачиваю...</b>\n"
            f"🎵 {track.artist} - {track.title}\n"
            f"⏱️ {track.formatted_duration}"
        )

        # Download the track
        file_path = await downloader.download(track)

        if not file_path or not os.path.exists(file_path):
            await status_msg.edit_text(
                f"❌ <b>Ошибка скачивания</b>\n"
                f"Трек: {track.artist} - {track.title}"
            )
            return

        # Send to target chat
        try:
            audio_file = FSInputFile(file_path)
            sent_message = await bot.send_audio(
                chat_id=target_chat_id,
                audio=audio_file,
                title=track.title,
                performer=track.artist,
                duration=track.duration,
                caption=f"🎵 {track.artist} - {track.title}\n\n🤖 @{settings.BOT_USERNAME}"
            )

            # Get file_id for caching
            file_id = sent_message.audio.file_id

            await status_msg.edit_text(
                f"✅ <b>Успешно отправлено!</b>\n\n"
                f"🎵 {track.artist} - {track.title}\n"
                f"⏱️ {track.formatted_duration}\n"
                f"📤 Отправлено в чат: <code>{target_chat_id}</code>\n"
                f"🆔 file_id: <code>{file_id}</code>"
            )

            logger.info(f"API: Sent '{track.title}' to chat {target_chat_id}")

        except TelegramForbiddenError:
            await status_msg.edit_text(
                f"❌ <b>Нет доступа к чату</b>\n"
                f"Бот не может отправить сообщение в чат {target_chat_id}.\n"
                f"Убедитесь, что бот добавлен в этот чат."
            )
            logger.warning(f"API: No access to chat {target_chat_id}")

        except TelegramBadRequest as e:
            await status_msg.edit_text(
                f"❌ <b>Ошибка Telegram</b>\n"
                f"Чат: {target_chat_id}\n"
                f"Ошибка: {e.message}"
            )
            logger.error(f"API: Telegram error for chat {target_chat_id}: {e}")

        finally:
            # Cleanup temp file
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.error(f"Failed to remove temp file: {e}")

    except Exception as e:
        logger.error(f"API request error: {e}")
        await message.answer(f"❌ <b>Ошибка</b>: {str(e)}")


@router.message(F.text.startswith('/api_search '))
async def api_search_handler(message: Message):
    """
    Search-only API - returns track info without downloading.

    Format: /api_search <api_key> <query>
    Returns: List of found tracks with video IDs
    """
    try:
        parts = message.text.split(' ', 2)

        if len(parts) < 3:
            await message.answer(
                "❌ <b>Неверный формат</b>\n\n"
                "Использование:\n"
                "<code>/api_search &lt;api_key&gt; &lt;запрос&gt;</code>"
            )
            return

        _, api_key, query = parts

        if not verify_api_key(api_key):
            await message.answer("❌ Неверный API ключ.")
            return

        tracks = await youtube_searcher.search(query)

        if not tracks:
            await message.answer(f"❌ Ничего не найдено по запросу: {query}")
            return

        # Format results
        text = f"🔍 <b>Результаты поиска:</b> <code>{query}</code>\n\n"

        for i, track in enumerate(tracks[:5], 1):
            text += (
                f"{i}. <b>{track.artist}</b> - {track.title}\n"
                f"   ⏱️ {track.formatted_duration} | ID: <code>{track.video_id}</code>\n\n"
            )

        await message.answer(text)

    except Exception as e:
        logger.error(f"API search error: {e}")
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(F.text.startswith('/api_download '))
async def api_download_by_id_handler(message: Message, bot: Bot):
    """
    Download by video ID and send to target chat.

    Format: /api_download <chat_id> <api_key> <video_id>
    """
    try:
        parts = message.text.split(' ', 3)

        if len(parts) < 4:
            await message.answer(
                "❌ <b>Неверный формат</b>\n\n"
                "Использование:\n"
                "<code>/api_download &lt;chat_id&gt; &lt;api_key&gt; &lt;video_id&gt;</code>"
            )
            return

        _, target_chat_id_str, api_key, video_id = parts

        try:
            target_chat_id = int(target_chat_id_str)
        except ValueError:
            await message.answer("❌ Неверный chat_id.")
            return

        if not verify_api_key(api_key):
            await message.answer("❌ Неверный API ключ.")
            return

        status_msg = await message.answer(
            f"🔍 <b>Получаю информацию о видео...</b>\n"
            f"ID: <code>{video_id}</code>"
        )

        # Get track info by video ID
        tracks = await youtube_searcher.search(f"https://youtube.com/watch?v={video_id}")

        if not tracks:
            await status_msg.edit_text(f"❌ Видео не найдено: {video_id}")
            return

        track = tracks[0]

        await status_msg.edit_text(
            f"📥 <b>Скачиваю...</b>\n"
            f"🎵 {track.artist} - {track.title}"
        )

        file_path = await downloader.download(track)

        if not file_path:
            await status_msg.edit_text("❌ Ошибка скачивания")
            return

        try:
            audio_file = FSInputFile(file_path)
            sent = await bot.send_audio(
                chat_id=target_chat_id,
                audio=audio_file,
                title=track.title,
                performer=track.artist,
                duration=track.duration
            )

            await status_msg.edit_text(
                f"✅ <b>Отправлено!</b>\n"
                f"🎵 {track.artist} - {track.title}\n"
                f"🆔 file_id: <code>{sent.audio.file_id}</code>"
            )

        except Exception as e:
            await status_msg.edit_text(f"❌ Ошибка отправки: {e}")

        finally:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)

    except Exception as e:
        logger.error(f"API download error: {e}")
        await message.answer(f"❌ Ошибка: {str(e)}")
