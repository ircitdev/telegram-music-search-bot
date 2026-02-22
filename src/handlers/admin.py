"""Admin panel and commands."""
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.config import settings
from src.utils.logger import logger
from src.database.repositories import user_repo, download_repo, stats_repo
from src.bot import bot

# Track bot start time
BOT_START_TIME = datetime.now()

router = Router()


class MailingStates(StatesGroup):
    """States for mailing process."""
    waiting_for_message = State()


def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    admin_ids = settings.get_admin_ids()
    return user_id in admin_ids


def create_admin_keyboard() -> InlineKeyboardMarkup:
    """Create admin panel keyboard with command buttons."""
    buttons = [
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="admin:stats"),
            InlineKeyboardButton(text="👥 Пользователи", callback_data="admin:users")
        ],
        [
            InlineKeyboardButton(text="🏆 ТОП-10", callback_data="admin:top"),
            InlineKeyboardButton(text="🌐 Web-панель", callback_data="admin:web")
        ],
        [
            InlineKeyboardButton(text="📢 Рассылка", callback_data="admin:mailing"),
            InlineKeyboardButton(text="📣 Пост в канал", callback_data="admin:post")
        ],
        [
            InlineKeyboardButton(text="🔧 Обновить yt-dlp", callback_data="admin:update_ytdlp")
        ],
        [
            InlineKeyboardButton(text="📝 Справка", callback_data="admin:help")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("admin"))
async def admin_command(message: Message):
    """Show admin panel."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещён")
        logger.warning(f"Unauthorized admin access attempt from user {message.from_user.id}")
        return

    text = (
        "🔐 <b>АДМИН-ПАНЕЛЬ</b>\n\n"
        "Выбери действие из меню ниже:\n\n"
        "<i>Также доступны команды:</i>\n"
        "• <code>/user_stats ID</code> - статистика пользователя\n"
        "• <code>/setpremium ID дни</code> - выдать премиум"
    )

    await message.answer(text, reply_markup=create_admin_keyboard())
    logger.info(f"Admin panel opened by {message.from_user.id}")


@router.message(Command("stats"))
async def stats_command(message: Message):
    """Show bot statistics."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещён")
        return

    # Get stats from database
    summary = await user_repo.get_stats_summary()
    total_users = summary.get("total_users", 0)
    total_searches = summary.get("total_searches", 0)
    total_downloads = summary.get("total_downloads", 0)
    active_users = await user_repo.get_active_users(minutes=60)

    # Calculate uptime
    uptime = datetime.now() - BOT_START_TIME
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)

    text = (
        "📊 <b>СТАТИСТИКА БОТА</b>\n\n"
        f"⏱ <b>Время работы:</b> {hours}ч {minutes}м {seconds}с\n\n"
        f"👥 <b>Пользователи:</b>\n"
        f"  • Всего: {total_users}\n"
        f"  • Активных (60 мин): {active_users}\n\n"
        f"📈 <b>Активность:</b>\n"
        f"  • Поисков: {total_searches}\n"
        f"  • Скачиваний: {total_downloads}\n"
    )

    await message.answer(text)
    logger.info(f"Stats viewed by admin {message.from_user.id}")


@router.message(Command("users"))
async def users_command(message: Message):
    """Show user count."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещён")
        return

    count = await user_repo.get_user_count()
    active = await user_repo.get_active_users(minutes=60)

    text = (
        "👥 <b>ПОЛЬЗОВАТЕЛИ</b>\n\n"
        f"📊 <b>Всего:</b> {count}\n"
        f"🟢 <b>Активных (60 мин):</b> {active}\n"
    )

    await message.answer(text)
    logger.info(f"User count viewed by admin {message.from_user.id}")


@router.message(Command("top"))
async def top_command(message: Message):
    """Show top users."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещён")
        return

    top_users = await user_repo.get_top_users(limit=10)

    if not top_users:
        await message.answer("📊 Пока нет данных о пользователях")
        return

    text = "🏆 <b>ТОП 10 ПОЛЬЗОВАТЕЛЕЙ</b>\n\n"
    for i, user in enumerate(top_users, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        username = f"@{user['username']}" if user.get('username') else user.get('first_name', 'Unknown')
        text += f"{medal} {username}\n"
        text += f"    🔍 {user['searches']} | ⬇️ {user['downloads']}\n\n"

    await message.answer(text)
    logger.info(f"Top users viewed by admin {message.from_user.id}")


@router.message(Command("user_stats"))
async def user_stats_command(message: Message):
    """Show specific user stats."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещён")
        return

    args = message.text.split(maxsplit=1)

    if len(args) < 2:
        await message.answer(
            "❌ Укажи ID пользователя\n\n"
            "<code>/user_stats 123456789</code>"
        )
        return

    try:
        target_user_id = int(args[1])
    except ValueError:
        await message.answer("❌ ID должен быть числом")
        return

    user = await user_repo.get_user(target_user_id)

    if not user:
        await message.answer(f"❌ Пользователь {target_user_id} не найден")
        return

    username = f"@{user['username']}" if user.get('username') else "не указан"
    first_name = user.get('first_name', 'не указано')
    is_premium = "✅ Да" if user.get('is_premium') else "❌ Нет"

    text = (
        f"👤 <b>СТАТИСТИКА ПОЛЬЗОВАТЕЛЯ</b>\n\n"
        f"🆔 ID: <code>{target_user_id}</code>\n"
        f"👤 Имя: {first_name}\n"
        f"📛 Username: {username}\n"
        f"⭐ Премиум: {is_premium}\n\n"
        f"📊 <b>Активность:</b>\n"
        f"  🔍 Поисков: {user.get('searches', 0)}\n"
        f"  ⬇️ Скачиваний: {user.get('downloads', 0)}\n"
        f"  🎁 Бонусов: {user.get('bonus_downloads', 0)}\n\n"
        f"📅 Первый визит: {user.get('created_at', 'неизвестно')}\n"
        f"🕐 Последний визит: {user.get('last_seen', 'неизвестно')}"
    )

    await message.answer(text)
    logger.info(f"User stats viewed by admin {message.from_user.id}: user {target_user_id}")


@router.message(Command("setpremium"))
async def set_premium_command(message: Message):
    """Set premium status for a user."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещён")
        return

    args = message.text.split()

    if len(args) < 2:
        await message.answer(
            "⭐ <b>ВЫДАЧА ПРЕМИУМА</b>\n\n"
            "Использование:\n"
            "<code>/setpremium USER_ID [дней]</code>\n\n"
            "Примеры:\n"
            "<code>/setpremium 123456789</code> - на 30 дней\n"
            "<code>/setpremium 123456789 90</code> - на 90 дней\n"
            "<code>/setpremium 123456789 0</code> - снять премиум\n"
        )
        return

    try:
        target_user_id = int(args[1])
    except ValueError:
        await message.answer("❌ ID должен быть числом")
        return

    # Default 30 days
    days = 30
    if len(args) >= 3:
        try:
            days = int(args[2])
        except ValueError:
            await message.answer("❌ Количество дней должно быть числом")
            return

    # Check if user exists
    user = await user_repo.get_user(target_user_id)
    if not user:
        await message.answer(f"❌ Пользователь {target_user_id} не найден в базе")
        return

    if days == 0:
        # Remove premium
        await user_repo.set_premium(target_user_id, False, None)
        await message.answer(
            f"✅ Премиум снят с пользователя <code>{target_user_id}</code>"
        )
        logger.info(f"Premium removed from user {target_user_id} by admin {message.from_user.id}")
    else:
        # Set premium
        expires_at = datetime.now() + timedelta(days=days)
        await user_repo.set_premium(target_user_id, True, expires_at)
        await message.answer(
            f"✅ Премиум выдан!\n\n"
            f"👤 Пользователь: <code>{target_user_id}</code>\n"
            f"⏱ Срок: {days} дней\n"
            f"📅 До: {expires_at.strftime('%d.%m.%Y %H:%M')}"
        )
        logger.info(f"Premium granted to user {target_user_id} for {days} days by admin {message.from_user.id}")


@router.message(Command("reset_stats"))
async def reset_stats_command(message: Message):
    """Reset all statistics - disabled for safety."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещён")
        return

    await message.answer(
        "⚠️ Сброс статистики отключён для безопасности данных.\n\n"
        "Данные хранятся в SQLite базе данных."
    )
    logger.warning(f"Stats reset attempted by admin {message.from_user.id}")


@router.message(Command("help_admin"))
async def help_admin_command(message: Message):
    """Show admin help."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещён")
        return

    text = (
        "🔐 <b>СПРАВКА ПО АДМИН-КОМАНДАМ</b>\n\n"
        "<b>/admin</b> - Меню администратора\n\n"
        "<b>/stats</b> - Статистика бота:\n"
        "  • Время работы\n"
        "  • Кол-во пользователей\n"
        "  • Активные пользователи\n"
        "  • Общие поиски/скачивания\n\n"
        "<b>/users</b> - Информация о пользователях:\n"
        "  • Всего пользователей\n"
        "  • Активных последний час\n\n"
        "<b>/top</b> - ТОП 10 пользователей по скачиваниям\n\n"
        "<b>/user_stats &lt;ID&gt;</b> - Статистика пользователя:\n"
        "  /user_stats 123456789\n\n"
        "<b>/setpremium &lt;ID&gt; [дни]</b> - Выдать премиум:\n"
        "  /setpremium 123456789 - 30 дней (по умолчанию)\n"
        "  /setpremium 123456789 90 - на 90 дней\n"
        "  /setpremium 123456789 0 - забрать премиум\n\n"
        "<b>/mailing</b> - Массовая рассылка сообщений всем пользователям\n\n"
        "<b>/reset_stats</b> - Сбросить всю статистику\n\n"
        "<b>/help_admin</b> - Эта справка\n"
    )

    await message.answer(text)
    logger.info(f"Admin help viewed by {message.from_user.id}")


@router.message(Command("mailing"))
async def mailing_command(message: Message, state: FSMContext):
    """Start mailing process."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещён")
        return

    user_count = await user_repo.get_user_count()

    text = (
        f"📢 <b>МАССОВАЯ РАССЫЛКА</b>\n\n"
        f"Получателей: {user_count} пользователей\n\n"
        f"Отправь сообщение, которое хочешь разослать всем.\n"
        f"Сообщение может содержать:\n"
        f"  • Текст\n"
        f"  • Ссылки\n"
        f"  • Форматирование (жирный, курсив)\n\n"
        f"<code>/cancel</code> - Отменить рассылку"
    )

    await message.answer(text)
    await state.set_state(MailingStates.waiting_for_message)
    logger.info(f"Mailing started by admin {message.from_user.id}")


@router.message(MailingStates.waiting_for_message)
async def mailing_message_handler(message: Message, state: FSMContext):
    """Handle mailing message."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещён")
        await state.clear()
        return

    # Check if it's /cancel
    if message.text and message.text.lower() == "/cancel":
        await message.answer("❌ Рассылка отменена")
        await state.clear()
        return

    # Get all users
    users = await user_repo.get_all_user_ids()
    total = len(users)

    if total == 0:
        await message.answer("❌ Нет пользователей для рассылки")
        await state.clear()
        return

    # Send message to all users
    sent = 0
    failed = 0

    await message.answer(
        f"⏳ Отправляю сообщение {total} пользователям...\n\n"
        f"Пожалуйста, дождись завершения рассылки."
    )

    for user_id in users:
        try:
            # Copy message to all users
            await bot.copy_message(
                chat_id=user_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
            sent += 1
        except Exception as e:
            logger.warning(f"Failed to send message to {user_id}: {e}")
            failed += 1

    # Report results
    result_text = (
        f"✅ <b>РАССЫЛКА ЗАВЕРШЕНА</b>\n\n"
        f"✅ Отправлено: {sent}/{total}\n"
        f"❌ Ошибок: {failed}\n\n"
        f"Успешность: {(sent/total*100):.1f}%"
    )

    await message.answer(result_text)
    logger.info(f"Mailing completed: sent {sent}/{total} by admin {message.from_user.id}")

    await state.clear()


@router.message(Command("setpremium"))
async def setpremium_command(message: Message):
    """Set premium status for a user."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещён")
        return

    args = message.text.split(maxsplit=2)

    if len(args) < 3:
        await message.answer(
            "❌ Неверный формат команды\n\n"
            "<b>Использование:</b>\n"
            "<code>/setpremium &lt;user_id&gt; &lt;days&gt;</code>\n\n"
            "<b>Примеры:</b>\n"
            "• <code>/setpremium 123456789 30</code> - премиум на 30 дней\n"
            "• <code>/setpremium 123456789 365</code> - премиум на год\n"
            "• <code>/setpremium 123456789 0</code> - отменить премиум"
        )
        return

    try:
        target_user_id = int(args[1])
        days = int(args[2])
    except ValueError:
        await message.answer("❌ ID и количество дней должны быть числами")
        return

    # Get or create user
    user = await user_repo.get_user(target_user_id)

    if not user:
        await message.answer(
            f"❌ Пользователь {target_user_id} не найден в базе.\n\n"
            f"Пользователь должен хотя бы раз запустить бота командой /start"
        )
        return

    if days == 0:
        # Remove premium
        await user_repo.set_premium(target_user_id, is_premium=False, premium_until=None)

        username = f"@{user.get('username')}" if user.get('username') else user.get('first_name', 'Unknown')

        await message.answer(
            f"✅ <b>Премиум отменён</b>\n\n"
            f"👤 Пользователь: {username}\n"
            f"🆔 ID: <code>{target_user_id}</code>\n"
            f"⭐ Статус: Бесплатный"
        )

        # Notify user
        try:
            await bot.send_message(
                target_user_id,
                "⚠️ Твоя премиум подписка была отменена.\n\n"
                "Теперь действует лимит: 10 треков в день."
            )
        except Exception:
            pass

    else:
        # Set premium
        premium_until = datetime.now() + timedelta(days=days)
        await user_repo.set_premium(target_user_id, is_premium=True, premium_until=premium_until)

        username = f"@{user.get('username')}" if user.get('username') else user.get('first_name', 'Unknown')

        await message.answer(
            f"✅ <b>Премиум выдан</b>\n\n"
            f"👤 Пользователь: {username}\n"
            f"🆔 ID: <code>{target_user_id}</code>\n"
            f"⭐ Статус: Премиум\n"
            f"📅 Срок: {days} дней\n"
            f"⏰ До: {premium_until.strftime('%Y-%m-%d %H:%M')}"
        )

        # Notify user
        try:
            await bot.send_message(
                target_user_id,
                f"🎉 <b>Поздравляем!</b>\n\n"
                f"Тебе выдан премиум статус на {days} дней!\n\n"
                f"⭐ <b>Преимущества:</b>\n"
                f"• ♾ Безлимитные скачивания\n"
                f"• 🚀 Приоритет в очереди\n"
                f"• ❤️ Избранные треки\n\n"
                f"Действует до: {premium_until.strftime('%d.%m.%Y %H:%M')}"
            )
        except Exception:
            pass

    logger.info(f"Premium status changed by admin {message.from_user.id}: user {target_user_id}, days {days}")


from src.utils.auth_codes import generate_auth_code


@router.message(Command("web_admin"))
async def web_admin_command(message: Message):
    """Send web admin dashboard link with auth code."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещён")
        return

    # Generate one-time auth code
    auth_code = generate_auth_code(message.from_user.id, message.from_user.username)

    # Dashboard URL with code
    dashboard_url = "https://musicfinder.uspeshnyy.ru"

    text = (
        "🌐 <b>WEB-ДАШБОРД</b>\n\n"
        f"🔗 <b>URL:</b> {dashboard_url}\n\n"
        f"🔑 <b>Код авторизации (действует 5 мин):</b>\n"
        f"<code>{auth_code}</code>\n\n"
        f"<i>Нажми на код, чтобы скопировать, затем вставь на сайте</i>\n\n"
        f"📊 <b>Возможности дашборда:</b>\n"
        f"• Статистика пользователей и скачиваний\n"
        f"• Управление премиум-подписками\n"
        f"• Статистика платежей и рефералов\n"
        f"• Управление API ключами\n"
        f"• Редактирование конфигурации\n"
        f"• Мониторинг системы"
    )

    await message.answer(text)
    logger.info(f"Web admin auth code generated for {message.from_user.id}")


from src.utils.channel_poster import channel_poster


@router.message(Command("post_top"))
async def post_top_command(message: Message):
    """Manually post top tracks to channel."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещён")
        return

    if not settings.CHANNEL_ID:
        await message.answer("❌ CHANNEL_ID не настроен")
        return

    args = message.text.split()
    period = args[1] if len(args) > 1 else "day"

    await message.answer(f"📤 Публикую топ ({period}) в канал...")

    try:
        if period == "week":
            await channel_poster.post_weekly_top()
        else:
            await channel_poster.post_daily_top()

        await message.answer(f"✅ Топ опубликован в {settings.CHANNEL_ID}")
        logger.info(f"Manual channel post by admin {message.from_user.id}: {period}")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
        logger.error(f"Manual channel post error: {e}")


@router.message(Command("update_ytdlp"))
async def update_ytdlp_command(message: Message):
    """Update yt-dlp to latest version."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещён")
        return

    await message.answer("⏳ Обновляю yt-dlp...\n\nПожалуйста, подожди.")

    try:
        import subprocess
        import sys

        # Update yt-dlp using pip
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0:
            # Get version info
            version_result = subprocess.run(
                [sys.executable, "-c", "import yt_dlp; print(yt_dlp.version.__version__)"],
                capture_output=True,
                text=True,
                timeout=10
            )

            version = version_result.stdout.strip() if version_result.returncode == 0 else "unknown"

            await message.answer(
                f"✅ <b>yt-dlp успешно обновлён</b>\n\n"
                f"📦 Версия: <code>{version}</code>\n\n"
                f"Теперь попробуй скачать проблемный трек заново."
            )
            logger.info(f"yt-dlp updated to version {version} by admin {message.from_user.id}")
        else:
            await message.answer(
                f"❌ <b>Ошибка обновления</b>\n\n"
                f"<code>{result.stderr[:500]}</code>"
            )
            logger.error(f"yt-dlp update failed: {result.stderr}")

    except subprocess.TimeoutExpired:
        await message.answer("❌ Превышено время ожидания обновления (120 сек)")
        logger.error("yt-dlp update timeout")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
        logger.error(f"yt-dlp update error: {e}")


# Callback handlers for admin panel buttons
from aiogram.types import CallbackQuery


@router.callback_query(F.data.startswith("admin:"))
async def admin_callback_handler(callback: CallbackQuery, state: FSMContext):
    """Handle admin panel button clicks."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    action = callback.data.split(":")[1]

    if action == "stats":
        # Show statistics
        summary = await user_repo.get_stats_summary()
        total_users = summary.get("total_users", 0)
        total_searches = summary.get("total_searches", 0)
        total_downloads = summary.get("total_downloads", 0)
        active_users = await user_repo.get_active_users(minutes=60)

        uptime = datetime.now() - BOT_START_TIME
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)

        text = (
            "📊 <b>СТАТИСТИКА БОТА</b>\n\n"
            f"⏱ <b>Время работы:</b> {hours}ч {minutes}м {seconds}с\n\n"
            f"👥 <b>Пользователи:</b>\n"
            f"  • Всего: {total_users}\n"
            f"  • Активных (60 мин): {active_users}\n\n"
            f"📈 <b>Активность:</b>\n"
            f"  • Поисков: {total_searches}\n"
            f"  • Скачиваний: {total_downloads}\n"
        )

        # Add back button
        back_button = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin:back")]
        ])

        await callback.message.edit_text(text, reply_markup=back_button)
        await callback.answer()

    elif action == "users":
        # Show user count
        count = await user_repo.get_user_count()
        active = await user_repo.get_active_users(minutes=60)

        text = (
            "👥 <b>ПОЛЬЗОВАТЕЛИ</b>\n\n"
            f"📊 <b>Всего:</b> {count}\n"
            f"🟢 <b>Активных (60 мин):</b> {active}\n"
        )

        back_button = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin:back")]
        ])

        await callback.message.edit_text(text, reply_markup=back_button)
        await callback.answer()

    elif action == "top":
        # Show top users
        top_users = await user_repo.get_top_users(limit=10)

        if not top_users:
            await callback.answer("📊 Пока нет данных о пользователях", show_alert=True)
            return

        text = "🏆 <b>ТОП 10 ПОЛЬЗОВАТЕЛЕЙ</b>\n\n"
        for i, user in enumerate(top_users, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            username = f"@{user['username']}" if user.get('username') else user.get('first_name', 'Unknown')
            text += f"{medal} {username}\n"
            text += f"    🔍 {user['searches']} | ⬇️ {user['downloads']}\n\n"

        back_button = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin:back")]
        ])

        await callback.message.edit_text(text, reply_markup=back_button)
        await callback.answer()

    elif action == "web":
        # Show web admin panel
        auth_code = generate_auth_code(callback.from_user.id, callback.from_user.username)
        dashboard_url = "https://musicfinder.uspeshnyy.ru"

        text = (
            "🌐 <b>WEB-ДАШБОРД</b>\n\n"
            f"🔗 <b>URL:</b> {dashboard_url}\n\n"
            f"🔑 <b>Код авторизации (действует 5 мин):</b>\n"
            f"<code>{auth_code}</code>\n\n"
            f"<i>Нажми на код, чтобы скопировать, затем вставь на сайте</i>\n\n"
            f"📊 <b>Возможности дашборда:</b>\n"
            f"• Статистика пользователей и скачиваний\n"
            f"• Управление премиум-подписками\n"
            f"• Статистика платежей и рефералов\n"
            f"• Управление API ключами\n"
            f"• Редактирование конфигурации\n"
            f"• Мониторинг системы"
        )

        back_button = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin:back")]
        ])

        await callback.message.edit_text(text, reply_markup=back_button)
        await callback.answer()
        logger.info(f"Web admin auth code generated for {callback.from_user.id}")

    elif action == "mailing":
        # Start mailing
        user_count = await user_repo.get_user_count()

        text = (
            f"📢 <b>МАССОВАЯ РАССЫЛКА</b>\n\n"
            f"Получателей: {user_count} пользователей\n\n"
            f"Отправь сообщение, которое хочешь разослать всем.\n"
            f"Сообщение может содержать:\n"
            f"  • Текст\n"
            f"  • Ссылки\n"
            f"  • Форматирование (жирный, курсив)\n\n"
            f"<code>/cancel</code> - Отменить рассылку"
        )

        back_button = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Отмена", callback_data="admin:back")]
        ])

        await callback.message.edit_text(text, reply_markup=back_button)
        await state.set_state(MailingStates.waiting_for_message)
        await callback.answer()
        logger.info(f"Mailing started by admin {callback.from_user.id}")

    elif action == "post":
        # Post to channel
        if not settings.CHANNEL_ID:
            await callback.answer("❌ CHANNEL_ID не настроен", show_alert=True)
            return

        # Ask which period
        text = (
            "📣 <b>ПУБЛИКАЦИЯ В КАНАЛ</b>\n\n"
            "Выбери период для топа:"
        )

        period_buttons = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📅 День", callback_data="admin:post_day"),
                InlineKeyboardButton(text="📆 Неделя", callback_data="admin:post_week")
            ],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin:back")]
        ])

        await callback.message.edit_text(text, reply_markup=period_buttons)
        await callback.answer()

    elif action == "post_day":
        # Post daily top
        await callback.answer("📤 Публикую топ дня...")
        try:
            await channel_poster.post_daily_top()
            await callback.answer("✅ Топ дня опубликован", show_alert=True)
            logger.info(f"Daily top posted by admin {callback.from_user.id}")
        except Exception as e:
            await callback.answer(f"❌ Ошибка: {e}", show_alert=True)
            logger.error(f"Daily top post error: {e}")

    elif action == "post_week":
        # Post weekly top
        await callback.answer("📤 Публикую топ недели...")
        try:
            await channel_poster.post_weekly_top()
            await callback.answer("✅ Топ недели опубликован", show_alert=True)
            logger.info(f"Weekly top posted by admin {callback.from_user.id}")
        except Exception as e:
            await callback.answer(f"❌ Ошибка: {e}", show_alert=True)
            logger.error(f"Weekly top post error: {e}")

    elif action == "update_ytdlp":
        # Update yt-dlp
        await callback.message.edit_text("⏳ Обновляю yt-dlp...\n\nПожалуйста, подожди.")
        await callback.answer()

        try:
            import subprocess
            import sys

            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                version_result = subprocess.run(
                    [sys.executable, "-c", "import yt_dlp; print(yt_dlp.version.__version__)"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                version = version_result.stdout.strip() if version_result.returncode == 0 else "unknown"

                text = (
                    f"✅ <b>yt-dlp успешно обновлён</b>\n\n"
                    f"📦 Версия: <code>{version}</code>\n\n"
                    f"Теперь попробуй скачать проблемный трек заново."
                )

                back_button = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="◀️ Назад", callback_data="admin:back")]
                ])

                await callback.message.edit_text(text, reply_markup=back_button)
                logger.info(f"yt-dlp updated to version {version} by admin {callback.from_user.id}")
            else:
                await callback.message.edit_text(
                    f"❌ <b>Ошибка обновления</b>\n\n"
                    f"<code>{result.stderr[:500]}</code>"
                )
                logger.error(f"yt-dlp update failed: {result.stderr}")

        except subprocess.TimeoutExpired:
            await callback.message.edit_text("❌ Превышено время ожидания обновления (120 сек)")
            logger.error("yt-dlp update timeout")
        except Exception as e:
            await callback.message.edit_text(f"❌ Ошибка: {e}")
            logger.error(f"yt-dlp update error: {e}")

    elif action == "help":
        # Show help
        text = (
            "🔐 <b>СПРАВКА ПО АДМИН-КОМАНДАМ</b>\n\n"
            "<b>/admin</b> - Меню администратора\n\n"
            "<b>/stats</b> - Статистика бота\n"
            "<b>/users</b> - Информация о пользователях\n"
            "<b>/top</b> - ТОП 10 пользователей\n\n"
            "<b>/user_stats &lt;ID&gt;</b> - Статистика пользователя:\n"
            "  /user_stats 123456789\n\n"
            "<b>/setpremium &lt;ID&gt; [дни]</b> - Выдать премиум:\n"
            "  /setpremium 123456789 - 30 дней\n"
            "  /setpremium 123456789 90 - на 90 дней\n"
            "  /setpremium 123456789 0 - забрать премиум\n\n"
            "<b>/mailing</b> - Массовая рассылка\n"
            "<b>/web_admin</b> - Web-дашборд\n"
            "<b>/post_top</b> - Публикация в канал\n"
            "<b>/update_ytdlp</b> - Обновить yt-dlp\n"
        )

        back_button = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin:back")]
        ])

        await callback.message.edit_text(text, reply_markup=back_button)
        await callback.answer()

    elif action == "back":
        # Return to main admin menu
        text = (
            "🔐 <b>АДМИН-ПАНЕЛЬ</b>\n\n"
            "Выбери действие из меню ниже:\n\n"
            "<i>Также доступны команды:</i>\n"
            "• <code>/user_stats ID</code> - статистика пользователя\n"
            "• <code>/setpremium ID дни</code> - выдать премиум"
        )

        await callback.message.edit_text(text, reply_markup=create_admin_keyboard())
        await callback.answer()
        # Clear state if any
        await state.clear()
