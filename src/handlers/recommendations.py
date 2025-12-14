"""Recommendations handler based on user history."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from src.database.repositories import download_repo, stats_repo
from src.utils.logger import logger
from src.handlers.callbacks import download_and_send_track
from src.models import Track

router = Router()


async def get_recommendations(user_id: int, limit: int = 10) -> list:
    """
    Generate recommendations based on user's download history.

    Algorithm:
    1. Get user's most downloaded artists
    2. Get popular tracks from those artists
    3. Filter out tracks user already downloaded
    4. Return top recommendations
    """
    # Get user's download history
    history = await download_repo.get_user_history(user_id, limit=100)

    if not history:
        # No history - return global top tracks
        return await stats_repo.get_top_tracks(limit=limit, period="week")

    # Count artists from user's history
    artist_counts = {}
    user_track_ids = set()

    for download in history:
        artist = download.get('artist', 'Unknown')
        track_id = download.get('track_id')

        if artist and artist != 'Unknown':
            artist_counts[artist] = artist_counts.get(artist, 0) + 1

        if track_id:
            user_track_ids.add(track_id)

    # Get top 3 artists from user's history
    top_artists = sorted(artist_counts.items(), key=lambda x: x[1], reverse=True)[:3]

    if not top_artists:
        # Fallback to global top
        return await stats_repo.get_top_tracks(limit=limit, period="week")

    # Get popular tracks from similar artists
    recommendations = []

    for artist, _ in top_artists:
        # Get tracks by this artist from global stats
        artist_tracks = await stats_repo.get_tracks_by_artist(artist, limit=5)

        for track in artist_tracks:
            # Skip if user already downloaded this track
            if track['track_id'] in user_track_ids:
                continue

            recommendations.append(track)

            if len(recommendations) >= limit:
                break

        if len(recommendations) >= limit:
            break

    # If not enough recommendations, add popular tracks
    if len(recommendations) < limit:
        top_tracks = await stats_repo.get_top_tracks(limit=limit * 2, period="week")

        for track in top_tracks:
            if track['track_id'] not in user_track_ids:
                recommendations.append(track)

            if len(recommendations) >= limit:
                break

    return recommendations[:limit]


def create_recommendations_keyboard(tracks: list, page: int = 0) -> InlineKeyboardMarkup:
    """Create keyboard with recommendation buttons."""
    buttons = []

    # Track buttons (1-10)
    start_idx = page * 10
    end_idx = min(start_idx + 10, len(tracks))

    for i in range(start_idx, end_idx):
        track = tracks[i]
        artist = track.get('artist', 'Unknown')
        title = track.get('title', 'Unknown')

        button_text = f"{i - start_idx + 1}. {artist} - {title}"
        if len(button_text) > 40:
            button_text = button_text[:37] + "..."

        buttons.append([InlineKeyboardButton(
            text=button_text,
            callback_data=f"rec_download:{i}"
        )])

    # Navigation buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=f"rec_page:{page - 1}"
        ))

    if end_idx < len(tracks):
        nav_buttons.append(InlineKeyboardButton(
            text="Вперёд ▶️",
            callback_data=f"rec_page:{page + 1}"
        ))

    if nav_buttons:
        buttons.append(nav_buttons)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("recommendations"))
async def recommendations_command(message: Message):
    """Show personalized recommendations."""
    user_id = message.from_user.id

    # Check if user has any history
    history_count = await download_repo.get_user_download_count(user_id)

    if history_count == 0:
        # No history - show popular tracks instead
        await message.answer(
            "🎵 <b>РЕКОМЕНДАЦИИ</b>\n\n"
            "У тебя пока нет истории скачиваний.\n"
            "Вот популярные треки на этой неделе:"
        )
    else:
        await message.answer(
            "🎵 <b>РЕКОМЕНДАЦИИ ДЛЯ ТЕБЯ</b>\n\n"
            f"На основе твоих {history_count} скачиваний:"
        )

    # Get recommendations
    recommendations = await get_recommendations(user_id, limit=20)

    if not recommendations:
        await message.answer("❌ Не удалось составить рекомендации. Попробуй позже.")
        return

    # Store recommendations in message for callback access
    # Since we can't store in FSM easily, we'll regenerate on callback

    text = "🎵 <b>Рекомендуемые треки:</b>\n\n"

    for i, track in enumerate(recommendations[:10], 1):
        artist = track.get('artist', 'Unknown')
        title = track.get('title', 'Unknown')
        downloads = track.get('download_count', 0)

        text += f"{i}. <b>{artist}</b> — {title}\n"
        text += f"   ⬇️ {downloads} скачиваний\n\n"

    keyboard = create_recommendations_keyboard(recommendations, page=0)

    await message.answer(text, reply_markup=keyboard)
    logger.info(f"User {user_id} requested recommendations ({len(recommendations)} tracks)")


@router.callback_query(F.data.startswith("rec_download:"))
async def rec_download_callback(callback: CallbackQuery):
    """Handle recommendation download."""
    user_id = callback.from_user.id

    try:
        # Parse track index
        track_idx = int(callback.data.split(":")[1])

        # Regenerate recommendations to get the track
        recommendations = await get_recommendations(user_id, limit=20)

        if track_idx >= len(recommendations):
            await callback.answer("❌ Трек не найден", show_alert=True)
            return

        track_data = recommendations[track_idx]

        # Convert to Track object
        track = Track(
            id=track_data['track_id'],
            title=track_data['title'],
            artist=track_data.get('artist', 'Unknown'),
            duration=track_data.get('duration', 0),
            url=f"https://youtube.com/watch?v={track_data['track_id']}"
        )

        # Use shared download function
        await download_and_send_track(callback, track)

    except Exception as e:
        logger.error(f"Recommendation download error: {e}")
        await callback.answer("❌ Ошибка при скачивании", show_alert=True)


@router.callback_query(F.data.startswith("rec_page:"))
async def rec_page_callback(callback: CallbackQuery):
    """Handle recommendation pagination."""
    user_id = callback.from_user.id
    page = int(callback.data.split(":")[1])

    # Get recommendations
    recommendations = await get_recommendations(user_id, limit=20)

    # Build message
    text = "🎵 <b>Рекомендуемые треки:</b>\n\n"

    start_idx = page * 10
    end_idx = min(start_idx + 10, len(recommendations))

    for i in range(start_idx, end_idx):
        track = recommendations[i]
        artist = track.get('artist', 'Unknown')
        title = track.get('title', 'Unknown')
        downloads = track.get('download_count', 0)

        text += f"{i - start_idx + 1}. <b>{artist}</b> — {title}\n"
        text += f"   ⬇️ {downloads} скачиваний\n\n"

    keyboard = create_recommendations_keyboard(recommendations, page=page)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()
