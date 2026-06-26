"""
Reply- и inline-клавиатуры главного меню (тексты зависят от языка пользователя).
"""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from translations import t


def main_reply_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """
    Постоянные кнопки внизу экрана (две в ряд, кроме последней строки):
    номера / все номера → отзывы / FAQ → поддержка / язык → полезные ссылки.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=t(lang, "btn_rooms")),
                KeyboardButton(text=t(lang, "btn_all_rooms")),
            ],
            [
                KeyboardButton(text=t(lang, "btn_reviews")),
                KeyboardButton(text=t(lang, "btn_faq")),
            ],
            [
                KeyboardButton(text=t(lang, "btn_support")),
                KeyboardButton(text=t(lang, "btn_language")),
            ],
            [
                KeyboardButton(text=t(lang, "btn_useful_links")),
            ],
        ],
        resize_keyboard=True,
    )


def language_inline_keyboard() -> InlineKeyboardMarkup:
    """Первичный выбор языка и смена языка из меню."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Русский", callback_data="setlang:ru"),
                InlineKeyboardButton(text="English", callback_data="setlang:en"),
            ]
        ]
    )
