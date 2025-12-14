"""Admin panel and commands."""
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message
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


@router.message(Command("admin"))
async def admin_command(message: Message):
    """Show admin panel."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещён")
        logger.warning(f"Unauthorized admin access attempt from user {message.from_user.id}")
        return

    text = (
        "🔐 <b>АДМИН-ПАНЕЛЬ</b>\n\n"
        "Доступные команды:\n\n"
        "📊 /stats - Общая статистика бота\n"
        "👥 /users - Количество пользователей\n"
        "🏆 /top - ТОП 10 пользователей\n"
        "👤 /user_stats - Статистика пользователя\n"
        "⭐ /setpremium - Выдать премиум\n"
        "🔄 /reset_stats - Сбросить статистику\n"
        "📢 /mailing - Массовая рассылка\n"
        "📝 /help_admin - Справка по командам\n"
    )

    await message.answer(text)
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
