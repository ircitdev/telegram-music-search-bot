"""Main application entry point."""
import asyncio
from src.bot import bot, dp
from src.handlers import start, search, callbacks
from src.utils.logger import logger


async def main():
    """Main function - startup the bot."""
    try:
        # Include all routers
        dp.include_router(start.router)
        dp.include_router(search.router)
        dp.include_router(callbacks.router)

        # Delete webhook for polling mode
        await bot.delete_webhook(drop_pending_updates=True)

        # Get bot info
        bot_info = await bot.me()
        logger.info(f"Bot started: @{bot_info.username}")
        logger.info("Polling mode activated")

        # Start polling
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

    except Exception as e:
        logger.error(f"Startup error: {e}", exc_info=True)
        raise
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
