"""Music recognition handler."""
from datetime import datetime, date
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ContentType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.bot import bot
from src.services.music_recognition import music_recognition
from src.database.repositories import user_repo
from src.utils.logger import logger

router = Router()

# Daily limit for free users
FREE_RECOGNIZE_LIMIT = 5


class RecognizeStates(StatesGroup):
    """States for recognition mode."""
    waiting_audio = State()
    waiting_humming = State()


def create_mode_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for recognition mode selection."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎵 Обычное распознавание",
            callback_data="recognize_mode:normal"
        )],
        [InlineKeyboardButton(
            text="🎤 По напеванию",
            callback_data="recognize_mode:humming"
        )],
        [InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="recognize_cancel"
        )]
    ])


def create_result_keyboard(artist: str, title: str) -> InlineKeyboardMarkup:
    """Create keyboard with download button."""
    search_query = f"{artist} {title}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="⬇️ Скачать этот трек",
            callback_data=f"recognize_download:{search_query[:50]}"
        )],
        [InlineKeyboardButton(
            text="🎵 Распознать еще",
            callback_data="recognize_more"
        )]
    ])


async def check_recognize_limit(user_id: int) -> tuple[bool, int]:
    """
    Check if user can use recognition.
    Returns (can_use, remaining_count).
    """
    # Check if premium
    is_premium = await user_repo.is_premium(user_id)
    if is_premium:
        return True, -1  # Unlimited

    # Get today's recognition count
    user = await user_repo.get_user(user_id)
    if not user:
        return True, FREE_RECOGNIZE_LIMIT

    # Check daily limit
    today = date.today().isoformat()
    last_recognize_date = user.get('last_recognize_date', '')
    recognize_count = user.get('recognize_count', 0)

    if last_recognize_date != today:
        # New day - reset counter
        recognize_count = 0

    remaining = FREE_RECOGNIZE_LIMIT - recognize_count
    return remaining > 0, remaining


async def increment_recognize_count(user_id: int):
    """Increment user's recognize count for today."""
    from src.database.connection import db

    today = date.today().isoformat()
    user = await user_repo.get_user(user_id)

    if not user:
        return

    last_date = user.get('last_recognize_date', '')
    if last_date != today:
        # New day - reset
        count = 1
    else:
        count = user.get('recognize_count', 0) + 1

    await db.execute("""
        UPDATE users SET recognize_count = ?, last_recognize_date = ? WHERE id = ?
    """, (count, today, user_id))
    await db.commit()


@router.message(Command("recognize"))
async def recognize_command(message: Message, state: FSMContext):
    """Start music recognition mode."""
    user_id = message.from_user.id

    # Check limit
    can_use, remaining = await check_recognize_limit(user_id)

    if not can_use:
        await message.answer(
            "❌ <b>Лимит распознаваний исчерпан</b>\n\n"
            f"Бесплатный лимит: {FREE_RECOGNIZE_LIMIT} распознаваний в день\n\n"
            "⭐ Купи <b>Премиум</b> для безлимитного распознавания!\n"
            "Команда: /premium"
        )
        return

    # Check if premium
    is_premium = await user_repo.is_premium(user_id)
    limit_text = "" if is_premium else f"\n📊 Осталось сегодня: {remaining}/{FREE_RECOGNIZE_LIMIT}"

    text = (
        "🎵 <b>РАСПОЗНАВАНИЕ МУЗЫКИ</b>\n\n"
        "Выбери режим:\n\n"
        "🎵 <b>Обычное</b> — отправь аудио с музыкой (3-10 сек)\n"
        "🎤 <b>По напеванию</b> — напой мелодию голосом"
        f"{limit_text}"
    )

    keyboard = create_mode_keyboard()
    await message.answer(text, reply_markup=keyboard)
    logger.info(f"User {user_id} started recognition")


@router.callback_query(F.data == "recognize_more")
async def recognize_more_callback(callback: CallbackQuery, state: FSMContext):
    """Start another recognition."""
    user_id = callback.from_user.id

    can_use, remaining = await check_recognize_limit(user_id)

    if not can_use:
        await callback.answer("Лимит распознаваний исчерпан. Купи Премиум!", show_alert=True)
        return

    is_premium = await user_repo.is_premium(user_id)
    limit_text = "" if is_premium else f"\n📊 Осталось сегодня: {remaining}/{FREE_RECOGNIZE_LIMIT}"

    text = (
        "🎵 <b>РАСПОЗНАВАНИЕ МУЗЫКИ</b>\n\n"
        "Выбери режим:\n\n"
        "🎵 <b>Обычное</b> — отправь аудио с музыкой (3-10 сек)\n"
        "🎤 <b>По напеванию</b> — напой мелодию голосом"
        f"{limit_text}"
    )

    keyboard = create_mode_keyboard()
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("recognize_mode:"))
async def recognize_mode_callback(callback: CallbackQuery, state: FSMContext):
    """Handle mode selection."""
    mode = callback.data.split(":")[1]

    if mode == "normal":
        await state.set_state(RecognizeStates.waiting_audio)
        text = (
            "🎵 <b>Обычное распознавание</b>\n\n"
            "Отправь аудио или голосовое сообщение с музыкой.\n\n"
            "💡 <b>Советы:</b>\n"
            "• Запись должна быть 3-10 секунд\n"
            "• Чем чище звук, тем лучше результат\n"
            "• Избегай фонового шума\n\n"
            "Жду аудио... 🎧"
        )
    else:
        await state.set_state(RecognizeStates.waiting_humming)
        text = (
            "🎤 <b>Распознавание по напеванию</b>\n\n"
            "Напой мелодию голосовым сообщением!\n\n"
            "💡 <b>Советы:</b>\n"
            "• Напевай от 8 секунд\n"
            "• Слова не обязательны\n"
            "• Напевай мелодию голоса, а не инструментов\n"
            "• Русскоязычные песни распознаются хуже\n\n"
            "Жду голосовое... 🎤"
        )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="recognize_cancel")]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "recognize_cancel")
async def recognize_cancel_callback(callback: CallbackQuery, state: FSMContext):
    """Cancel recognition mode."""
    await state.clear()
    await callback.message.edit_text("❌ Распознавание отменено")
    await callback.answer()


@router.message(RecognizeStates.waiting_audio, F.content_type.in_({ContentType.AUDIO, ContentType.VOICE, ContentType.VIDEO_NOTE}))
async def handle_audio_recognition(message: Message, state: FSMContext):
    """Handle audio for normal recognition."""
    await process_recognition(message, state, is_humming=False)


@router.message(RecognizeStates.waiting_humming, F.content_type == ContentType.VOICE)
async def handle_humming_recognition(message: Message, state: FSMContext):
    """Handle voice for humming recognition."""
    await process_recognition(message, state, is_humming=True)


async def process_recognition(message: Message, state: FSMContext, is_humming: bool):
    """Process audio recognition."""
    user_id = message.from_user.id

    # Check limit again
    can_use, _ = await check_recognize_limit(user_id)
    if not can_use:
        await message.answer("❌ Лимит распознаваний исчерпан. Купи Премиум: /premium")
        await state.clear()
        return

    # Send processing message
    processing_msg = await message.answer("🔍 Распознаю музыку...")

    try:
        # Download audio file
        if message.audio:
            file = await bot.get_file(message.audio.file_id)
        elif message.voice:
            file = await bot.get_file(message.voice.file_id)
        elif message.video_note:
            file = await bot.get_file(message.video_note.file_id)
        else:
            await processing_msg.edit_text("❌ Неподдерживаемый формат")
            return

        # Download file content
        file_path = file.file_path
        audio_data = await bot.download_file(file_path)
        audio_bytes = audio_data.read()

        # Recognize
        result = await music_recognition.recognize_audio(audio_bytes, is_humming=is_humming)

        # Increment counter
        await increment_recognize_count(user_id)

        if result.success:
            # Format result
            text = (
                "✅ <b>Трек найден!</b>\n\n"
                f"🎤 <b>Исполнитель:</b> {result.artist}\n"
                f"🎵 <b>Название:</b> {result.title}\n"
            )

            if result.album:
                text += f"💿 <b>Альбом:</b> {result.album}\n"

            if result.release_date:
                text += f"📅 <b>Дата:</b> {result.release_date}\n"

            if result.timecode:
                text += f"⏱ <b>Таймкод:</b> {result.timecode}\n"

            # Add links
            links = []
            if result.song_link:
                links.append(f"<a href='{result.song_link}'>🔗 Ссылка</a>")
            if result.apple_music_url:
                links.append(f"<a href='{result.apple_music_url}'>🍎 Apple Music</a>")
            if result.spotify_url:
                links.append(f"<a href='{result.spotify_url}'>🟢 Spotify</a>")

            if links:
                text += "\n" + " | ".join(links)

            keyboard = create_result_keyboard(result.artist, result.title)
            await processing_msg.edit_text(text, reply_markup=keyboard, disable_web_page_preview=True)

            logger.info(f"Recognition success for user {user_id}: {result.artist} - {result.title}")

        else:
            await processing_msg.edit_text(
                f"❌ <b>Не удалось распознать</b>\n\n"
                f"{result.error}\n\n"
                "Попробуй еще раз: /recognize"
            )
            logger.info(f"Recognition failed for user {user_id}: {result.error}")

    except Exception as e:
        logger.error(f"Recognition error for user {user_id}: {e}")
        await processing_msg.edit_text(
            f"❌ Ошибка при распознавании\n\n"
            f"Попробуй еще раз: /recognize"
        )

    await state.clear()


@router.callback_query(F.data.startswith("recognize_download:"))
async def recognize_download_callback(callback: CallbackQuery):
    """Download recognized track."""
    query = callback.data.split(":", 1)[1]

    await callback.answer("🔍 Ищу трек...")

    # Search for the track
    from src.searchers.youtube import youtube_searcher

    tracks = await youtube_searcher.search(query)

    if not tracks:
        await callback.message.answer("❌ Трек не найден в каталоге. Попробуй поискать вручную.")
        return

    # Get first track
    track = tracks[0]

    # Use existing download function
    from src.handlers.callbacks import download_and_send_track
    await download_and_send_track(callback, track)
