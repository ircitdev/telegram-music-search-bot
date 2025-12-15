"""Start command handlers."""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.database.repositories import user_repo
from src.utils.logger import logger

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command."""
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""

    # Parse referral code from /start ref_USER_ID
    referrer_id = None
    if message.text and len(message.text.split()) > 1:
        param = message.text.split()[1]
        if param.startswith("ref_"):
            try:
                referrer_id = int(param.replace("ref_", ""))
            except:
                pass

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

    logger.info(f"User {user_id} started bot")

    await message.answer(
        "🎵 <b>Добро пожаловать в UspMusicFinder Bot!</b>\n\n"
        "Я помогу тебе найти и скачать музыку с YouTube Music.\n\n"
        "<b>Как пользоваться:</b>\n"
        "1️⃣ Отправь мне название песни или исполнителя\n"
        "2️⃣ Выбери трек из списка (кнопки 1-10)\n"
        "3️⃣ Получи MP3 файл!\n\n"
        "💡 <b>Команды:</b>\n"
        "/help - Справка\n"
        "/top - Топ треков\n"
        "/recommendations - Рекомендации\n"
        "/referral - Пригласи друзей!\n\n"
        "Попробуй поискать песню! 🎶"
    )


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
