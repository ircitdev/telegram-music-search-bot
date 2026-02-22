"""Keyboard layouts for the bot."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List
from src.models import Track


def create_track_keyboard(
    tracks: List[Track],
    page: int = 0,
    total_tracks: int = 0,
    with_favorites: bool = True
) -> InlineKeyboardMarkup:
    """
    Create inline keyboard with numbered buttons for tracks.

    Args:
        tracks: List of Track objects (current page, 10 items)
        page: Current page (0 = first 10, 1 = next 10)
        total_tracks: Total number of tracks available
        with_favorites: Add favorite buttons row

    Returns:
        InlineKeyboardMarkup with track selection buttons
    """
    buttons = []
    offset = page * 10

    # First row: 1-5 (or 11-15 for page 1)
    row1 = [
        InlineKeyboardButton(
            text=str(offset + i),
            callback_data=f"track:{offset + i}"
        )
        for i in range(1, min(6, len(tracks) + 1))
    ]

    # Second row: 6-10 (or 16-20 for page 1)
    row2 = [
        InlineKeyboardButton(
            text=str(offset + i),
            callback_data=f"track:{offset + i}"
        )
        for i in range(6, min(11, len(tracks) + 1))
    ]

    if row1:
        buttons.append(row1)
    if row2:
        buttons.append(row2)

    # Third row: favorite buttons ❤️1 - ❤️5
    if with_favorites and len(tracks) > 0:
        fav_row = [
            InlineKeyboardButton(
                text=f"❤️{offset + i}",
                callback_data=f"fav:{offset + i}"
            )
            for i in range(1, min(6, len(tracks) + 1))
        ]
        buttons.append(fav_row)

    # Pagination row
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"page:{page - 1}"
        ))
    if total_tracks > (page + 1) * 10:
        nav_row.append(InlineKeyboardButton(
            text="Ещё ➡️",
            callback_data=f"page:{page + 1}"
        ))
    if nav_row:
        buttons.append(nav_row)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_video_keyboard(track_id: str) -> InlineKeyboardMarkup:
    """
    Create keyboard with video link button.

    Args:
        track_id: YouTube video ID

    Returns:
        InlineKeyboardMarkup with "Watch video" button
    """
    buttons = [[
        InlineKeyboardButton(
            text="🎬 Смотреть видео",
            url=f"https://youtube.com/watch?v={track_id}"
        )
    ]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_country_keyboard() -> InlineKeyboardMarkup:
    """
    Create inline keyboard for country selection in TOP handler.

    Returns:
        InlineKeyboardMarkup with country flags
    """
    buttons = [
        [
            InlineKeyboardButton(text="🇺🇿", callback_data="top:uz"),
            InlineKeyboardButton(text="🇷🇺", callback_data="top:ru"),
            InlineKeyboardButton(text="🇬🇧", callback_data="top:en"),
            InlineKeyboardButton(text="🇰🇿", callback_data="top:kz"),
            InlineKeyboardButton(text="🇹🇷", callback_data="top:tr"),
            InlineKeyboardButton(text="🇦🇿", callback_data="top:az"),
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)
