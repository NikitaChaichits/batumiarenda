"""
Inline-клавиатура входа в раздел «Отзывы» (оставить / посмотреть).
"""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from translations import t


def review_entry_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Две кнопки под приглашением в раздел отзывов."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t(lang, "btn_review_write"), callback_data="rev:write"),
                InlineKeyboardButton(
                    text=t(lang, "btn_review_browse"), callback_data="rev:browse"
                ),
            ],
        ]
    )
