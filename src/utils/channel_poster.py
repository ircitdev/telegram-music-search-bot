"""Channel auto-posting module for TopMusicToday."""
import asyncio
from datetime import datetime, timedelta
from typing import Optional

from src.bot import bot
from src.config import settings
from src.database.repositories import stats_repo
from src.utils.logger import logger


class ChannelPoster:
    """Handles automatic posting to Telegram channel."""

    def __init__(self):
        self.channel_id = settings.CHANNEL_ID
        self.post_hour = settings.CHANNEL_POST_HOUR
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        """Start the scheduled posting task."""
        if not self.channel_id:
            logger.info("Channel posting disabled (CHANNEL_ID not set)")
            return

        self._running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info(f"Channel poster started. Posting to {self.channel_id} at {self.post_hour}:00")

    async def stop(self):
        """Stop the scheduled posting task."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Channel poster stopped")

    async def _scheduler_loop(self):
        """Main scheduler loop - posts daily at specified hour."""
        while self._running:
            try:
                # Calculate time until next post
                now = datetime.now()
                next_post = now.replace(hour=self.post_hour, minute=0, second=0, microsecond=0)

                if now >= next_post:
                    # If past post time today, schedule for tomorrow
                    next_post += timedelta(days=1)

                wait_seconds = (next_post - now).total_seconds()
                logger.info(f"Next channel post in {wait_seconds / 3600:.1f} hours")

                # Wait until post time
                await asyncio.sleep(wait_seconds)

                # Post to channel
                await self.post_daily_top()

                # Wait a bit before next iteration to avoid double posting
                await asyncio.sleep(60)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Channel poster error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    async def post_daily_top(self):
        """Post daily top tracks to channel."""
        try:
            # Get top tracks for today
            tracks = await stats_repo.get_top_tracks(limit=10, period="day")

            if not tracks:
                # If no tracks today, get weekly
                tracks = await stats_repo.get_top_tracks(limit=10, period="week")
                period_text = "за неделю"
            else:
                period_text = "за сегодня"

            if not tracks:
                logger.info("No tracks to post to channel")
                return

            # Format message
            now = datetime.now()
            date_str = now.strftime("%d.%m.%Y")

            text = f"🎵 <b>ТОП-10 ТРЕКОВ {period_text.upper()}</b>\n"
            text += f"📅 {date_str}\n\n"

            for i, track in enumerate(tracks[:10], 1):
                # Medals for top 3
                if i == 1:
                    icon = "🥇"
                elif i == 2:
                    icon = "🥈"
                elif i == 3:
                    icon = "🥉"
                else:
                    icon = f"{i}."

                artist = track.get("artist") or "Unknown"
                title = track["title"]
                count = track["download_count"]

                text += f"{icon} <b>{artist}</b> — {title}\n"
                text += f"    └ ⬇️ {count}\n\n"

            text += "━━━━━━━━━━━━━━━━━━━━\n"
            text += f"🤖 Скачать: @{settings.BOT_USERNAME}\n"
            text += "🔔 Подпишись, чтобы быть в курсе!"

            # Send to channel
            await bot.send_message(
                chat_id=self.channel_id,
                text=text,
                parse_mode="HTML",
                disable_web_page_preview=True
            )

            logger.info(f"Posted daily top to channel {self.channel_id}")

        except Exception as e:
            logger.error(f"Failed to post to channel: {e}")

    async def post_weekly_top(self):
        """Post weekly top tracks to channel (can be called manually)."""
        try:
            tracks = await stats_repo.get_top_tracks(limit=10, period="week")

            if not tracks:
                logger.info("No weekly tracks to post")
                return

            now = datetime.now()
            week_start = (now - timedelta(days=7)).strftime("%d.%m")
            week_end = now.strftime("%d.%m.%Y")

            text = f"🏆 <b>ТОП-10 ТРЕКОВ НЕДЕЛИ</b>\n"
            text += f"📅 {week_start} — {week_end}\n\n"

            for i, track in enumerate(tracks[:10], 1):
                if i == 1:
                    icon = "🥇"
                elif i == 2:
                    icon = "🥈"
                elif i == 3:
                    icon = "🥉"
                else:
                    icon = f"{i}."

                artist = track.get("artist") or "Unknown"
                title = track["title"]
                count = track["download_count"]

                text += f"{icon} <b>{artist}</b> — {title}\n"
                text += f"    └ ⬇️ {count} скачиваний\n\n"

            text += "━━━━━━━━━━━━━━━━━━━━\n"
            text += f"🤖 Скачать треки: @{settings.BOT_USERNAME}\n"
            text += "📢 Подпишись на канал!"

            await bot.send_message(
                chat_id=self.channel_id,
                text=text,
                parse_mode="HTML",
                disable_web_page_preview=True
            )

            logger.info(f"Posted weekly top to channel {self.channel_id}")

        except Exception as e:
            logger.error(f"Failed to post weekly top: {e}")

    async def post_new_track_alert(self, artist: str, title: str, downloads: int):
        """Post alert when a track reaches milestone downloads."""
        if not self.channel_id:
            return

        try:
            # Only post for significant milestones
            milestones = [100, 500, 1000, 5000, 10000]
            if downloads not in milestones:
                return

            text = f"🔥 <b>ХИТОВЫЙ ТРЕК!</b>\n\n"
            text += f"🎵 <b>{artist}</b> — {title}\n"
            text += f"⬇️ Уже <b>{downloads}</b> скачиваний!\n\n"
            text += f"Скачай и ты: @{settings.BOT_USERNAME}"

            await bot.send_message(
                chat_id=self.channel_id,
                text=text,
                parse_mode="HTML"
            )

            logger.info(f"Posted track milestone: {artist} - {title} ({downloads})")

        except Exception as e:
            logger.error(f"Failed to post track alert: {e}")


# Global instance
channel_poster = ChannelPoster()


def create_channel_poster_task() -> asyncio.Task:
    """Create and start the channel poster task."""
    return asyncio.create_task(channel_poster.start())
