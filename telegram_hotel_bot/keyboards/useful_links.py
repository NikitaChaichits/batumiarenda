"""
Inline-клавиатура «Полезные ссылки» — Google Maps (отель, магазины, ТЦ).
"""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from translations import t

# Короткие ссылки Google Maps на объекты рядом с отелем
HOTEL_MAPS_URL = "https://maps.app.goo.gl/zCv8MJ2aPnXLrrn57"

_SHOPS: list[tuple[str, str]] = [
    ("Nikora", "https://maps.app.goo.gl/DphTjQh5cDBhLazj8"),
    ("Carrefour", "https://maps.app.goo.gl/KVSzt7PSRiCosuSs6"),
    ("GoodWill", "https://maps.app.goo.gl/dVortvyzLTfcxJEu6"),
]
_MALLS: list[tuple[str, str]] = [
    ("Metro City", "https://maps.app.goo.gl/LYurWF8DMJFAxPTs5"),
    ("Grand Mall", "https://maps.app.goo.gl/gGLGnntkTzUVG1bm9"),
]


def useful_links_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Кнопки-ссылки на карты: отель, сети магазинов, торговые центры."""
    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text=t(lang, "useful_hotel_location"), url=HOTEL_MAPS_URL)],
        [
            InlineKeyboardButton(text=f"🛒 {_SHOPS[0][0]}", url=_SHOPS[0][1]),
            InlineKeyboardButton(text=f"🛒 {_SHOPS[1][0]}", url=_SHOPS[1][1]),
        ],
        [InlineKeyboardButton(text=f"🛒 {_SHOPS[2][0]}", url=_SHOPS[2][1])],
        [
            InlineKeyboardButton(text=f"🏬 {_MALLS[0][0]}", url=_MALLS[0][1]),
            InlineKeyboardButton(text=f"🏬 {_MALLS[1][0]}", url=_MALLS[1][1]),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
