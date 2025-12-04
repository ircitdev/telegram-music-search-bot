"""Admin panel and commands."""
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from src.config import settings
from src.utils.logger import logger
from src.utils.stats import bot_stats

router = Router()


def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    admin_ids = settings.ADMIN_IDS
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
        "<b>/reset_stats</b> - Сбросить всю статистику\n\n"
        "<b>/help_admin</b> - Эта справка\n"
    )

    await message.answer(text)
    logger.info(f"Admin help viewed by {message.from_user.id}")
