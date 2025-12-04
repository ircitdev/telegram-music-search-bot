"""Keyboard layouts for the bot."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List
from src.models import Track


def create_track_keyboard(tracks: List[Track]) -> InlineKeyboardMarkup:
    """
    Create inline keyboard with numbered buttons for tracks (1-10).

    Args:
        tracks: List of Track objects

    Returns:
        InlineKeyboardMarkup with track selection buttons
    """
    buttons = []

    # First row: 1-5
    row1 = [
        InlineKeyboardButton(
            text=str(i),
            callback_data=f"track:{i}"
        )
        for i in range(1, min(6, len(tracks) + 1))
    ]

    # Second row: 6-10
    row2 = [
        InlineKeyboardButton(
            text=str(i),
            callback_data=f"track:{i}"
        )
        for i in range(6, min(11, len(tracks) + 1))
    ]

    if row1:
        buttons.append(row1)
    if row2:
        buttons.append(row2)

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
