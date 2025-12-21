"""Localization module for multilanguage support."""
from typing import Dict, Optional
from src.utils.logger import logger

# Supported languages
SUPPORTED_LANGUAGES = ["ru", "en", "uz"]
DEFAULT_LANGUAGE = "ru"


class Localization:
    """Handles multilanguage text translations."""

    _translations: Dict[str, Dict[str, str]] = {}
    _user_languages: Dict[int, str] = {}

    @classmethod
    def load_translations(cls):
        """Load all translations."""
        from src.locales import ru, en, uz
        cls._translations = {
            "ru": ru.MESSAGES,
            "en": en.MESSAGES,
            "uz": uz.MESSAGES,
        }
        logger.info(f"Loaded translations for: {list(cls._translations.keys())}")

    @classmethod
    def get_user_lang(cls, user_id: int) -> str:
        """Get user's language preference."""
        return cls._user_languages.get(user_id, DEFAULT_LANGUAGE)

    @classmethod
    def set_user_lang(cls, user_id: int, lang: str):
        """Set user's language preference."""
        if lang in SUPPORTED_LANGUAGES:
            cls._user_languages[user_id] = lang
            logger.info(f"User {user_id} set language to {lang}")

    @classmethod
    def get(cls, key: str, user_id: int, **kwargs) -> str:
        """Get translated message for user."""
        lang = cls.get_user_lang(user_id)

        # Get translations dict for language
        translations = cls._translations.get(lang, cls._translations.get(DEFAULT_LANGUAGE, {}))

        # Get message, fallback to Russian if not found
        message = translations.get(key)
        if message is None:
            message = cls._translations.get(DEFAULT_LANGUAGE, {}).get(key, key)

        # Format with kwargs if provided
        if kwargs:
            try:
                message = message.format(**kwargs)
            except KeyError as e:
                logger.warning(f"Missing translation key: {e} in {key}")

        return message

    @classmethod
    def get_language_name(cls, lang: str) -> str:
        """Get human-readable language name."""
        names = {
            "ru": "🇷🇺 Русский",
            "en": "🇬🇧 English",
            "uz": "🇺🇿 O'zbek",
        }
        return names.get(lang, lang)


# Shortcut function
def _(key: str, user_id: int, **kwargs) -> str:
    """Shortcut for getting translated message."""
    return Localization.get(key, user_id, **kwargs)


# Initialize translations on import
def init_locales():
    """Initialize localization system."""
    Localization.load_translations()
