"""Main application entry point."""
import asyncio
from src.bot import bot, dp
from src.handlers import start, search, callbacks
from src.utils.logger import logger
from src.utils.cleanup import create_cleanup_task


async def main():
    """Main function - startup the bot."""
    cleanup_task = None
    
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
        
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
