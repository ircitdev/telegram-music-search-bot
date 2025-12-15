"""Main application entry point."""
import asyncio
from aiogram.fsm.storage.memory import MemoryStorage

from src.bot import bot, dp
from src.handlers import start, search, callbacks, admin, history, favorites, top, referral, recommendations, premium, recognize
from src.utils.logger import logger
from src.utils.cleanup import create_cleanup_task
from src.database import db


async def main():
    """Main function - startup the bot."""
    cleanup_task = None

    try:
        # Connect to database
        await db.connect()

        # Setup FSM storage (in-memory)
        storage = MemoryStorage()
        dp.fsm.storage = storage

        # Include all routers (order matters!)
        dp.include_router(admin.router)  # Admin first (higher priority)
        dp.include_router(premium.router)  # Premium/payments (before start for pre_checkout)
        dp.include_router(recognize.router)  # Music recognition
        dp.include_router(start.router)
        dp.include_router(top.router)  # TOP command
        dp.include_router(referral.router)  # Referral system
        dp.include_router(recommendations.router)  # Recommendations
        dp.include_router(history.router)
        dp.include_router(favorites.router)
        dp.include_router(search.router)
        dp.include_router(callbacks.router)

        # Delete webhook for polling mode
        await bot.delete_webhook(drop_pending_updates=True)

        # Get bot info
        bot_info = await bot.me()
        logger.info(f"Bot started: @{bot_info.username}")
        logger.info("Polling mode activated")

        # Start cleanup task
        cleanup_task = create_cleanup_task(interval_seconds=3600, max_age_seconds=3600)
        logger.info("Cleanup task started (1 hour interval)")

        # Start polling
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

    except Exception as e:
        logger.error(f"Startup error: {e}", exc_info=True)
        raise
    finally:
        # Cancel cleanup task
        if cleanup_task:
            cleanup_task.cancel()
            try:
                await cleanup_task
            except asyncio.CancelledError:
                pass

        # Close database connection
        await db.disconnect()

        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
