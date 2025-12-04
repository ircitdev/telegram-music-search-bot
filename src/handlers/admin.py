"""Admin panel and commands."""
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.config import settings
from src.utils.logger import logger
from src.utils.stats import bot_stats
from src.utils.users import user_manager
from src.bot import bot

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

    text = bot_stats.get_stats_text()
    await message.answer(text)
    logger.info(f"Stats viewed by admin {message.from_user.id}")


@router.message(Command("users"))
async def users_command(message: Message):
    """Show user count."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещён")
        return

    count = bot_stats.get_user_count()
    active = bot_stats.get_active_users(minutes=60)

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

    text = bot_stats.get_top_users_text(limit=10)
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
        user_id = int(args[1])
    except ValueError:
        await message.answer("❌ ID должен быть числом")
        return

    text = bot_stats.get_user_stats(user_id)
    await message.answer(text)
    logger.info(f"User stats viewed by admin {message.from_user.id}: user {user_id}")


@router.message(Command("reset_stats"))
async def reset_stats_command(message: Message):
    """Reset all statistics."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещён")
        return

    bot_stats.reset()
    await message.answer("✅ Статистика сброшена")
    logger.warning(f"Stats reset by admin {message.from_user.id}")


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

    user_count = user_manager.get_user_count()

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
    users = user_manager.get_all_users()
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
