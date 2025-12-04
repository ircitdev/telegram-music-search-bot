"""Bot initialization module."""
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from src.config import settings

# Initialize bot with default HTML parse mode
bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# Initialize FSM storage and dispatcher
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
