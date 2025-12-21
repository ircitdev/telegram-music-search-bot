"""Language selection handler."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from src.database.repositories import user_repo
from src.locales import SUPPORTED_LANGUAGES, Localization, _
from src.utils.logger import logger

router = Router()


def create_language_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard with language options."""
    buttons = [
        [InlineKeyboardButton(
            text=Localization.get_language_name(lang),
            callback_data=f"set_lang:{lang}"
        )]
        for lang in SUPPORTED_LANGUAGES
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("lang", "language"))
async def lang_command(message: Message):
    """Handle /lang command - show language selection."""
    user_id = message.from_user.id

    text = _("lang_title", user_id)
    keyboard = create_language_keyboard()

    await message.answer(text, reply_markup=keyboard)
    logger.info(f"User {user_id} opened language selection")


@router.callback_query(F.data.startswith("set_lang:"))
async def set_language_callback(callback: CallbackQuery):
    """Handle language selection."""
    user_id = callback.from_user.id
    new_lang = callback.data.split(":")[1]

    if new_lang not in SUPPORTED_LANGUAGES:
        await callback.answer("Invalid language")
        return

    # Save to database
    await user_repo.set_user_language(user_id, new_lang)

    # Update in-memory cache
    Localization.set_user_lang(user_id, new_lang)

    # Get confirmation message in new language
    confirmation = _("lang_changed", user_id)

    await callback.message.edit_text(confirmation)
    await callback.answer()
    logger.info(f"User {user_id} changed language to {new_lang}")
