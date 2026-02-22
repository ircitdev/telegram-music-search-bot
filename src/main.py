"""Main application entry point."""
import asyncio
from aiogram.fsm.storage.memory import MemoryStorage

from src.bot import bot, dp
from src.handlers import start, search, callbacks, admin, history, favorites, top, referral, recommendations, premium, recognize, api, language, stats
from src.utils.logger import logger
from src.utils.cleanup import create_cleanup_task
from src.utils.sentry import init_sentry, capture_exception
from src.utils.channel_poster import channel_poster
from src.database import db


async def main():
    """Main function - startup the bot."""
    cleanup_task = None
    channel_task = None

    # Initialize Sentry error tracking
    init_sentry()

    try:
        # Connect to database
        await db.connect()

        # Setup FSM storage (in-memory)
        storage = MemoryStorage()
        dp.fsm.storage = storage

        # Initialize localization
        from src.locales import init_locales
        init_locales()

        # Include all routers (order matters!)
        dp.include_router(admin.router)  # Admin first (higher priority)
        dp.include_router(premium.router)  # Premium/payments (before start for pre_checkout)
        dp.include_router(recognize.router)  # Music recognition
        dp.include_router(language.router)  # Language selection
        dp.include_router(start.router)
        dp.include_router(top.router)  # TOP command
        dp.include_router(referral.router)  # Referral system
        dp.include_router(recommendations.router)  # Recommendations
        dp.include_router(stats.router)  # User statistics
        dp.include_router(history.router)
        dp.include_router(favorites.router)
        dp.include_router(search.router)
        dp.include_router(api.router)
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

        # Start channel poster task
        channel_task = asyncio.create_task(channel_poster.start())

        # Start polling
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

    except Exception as e:
        logger.error(f"Startup error: {e}", exc_info=True)
        capture_exception(e)
        raise
    finally:
        # Cancel cleanup task
        if cleanup_task:
            cleanup_task.cancel()
            try:
                await cleanup_task
            except asyncio.CancelledError:
                pass

        # Stop channel poster
        if channel_task:
            await channel_poster.stop()

        # Close database connection
        await db.disconnect()

        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
