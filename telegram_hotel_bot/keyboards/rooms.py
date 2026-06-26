"""
Inline-клавиатура для просмотра карточек номеров (листание + Airbnb + уточнение дат + галерея фото).
"""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import booking_url_for_room
from translations import t


def room_summary_actions_keyboard(
    lang: str,
    *,
    room_id: int,
    list_index: int,
    listing_url: str | None = None,
) -> InlineKeyboardMarkup:
    """Только Airbnb и «уточнить даты» — для карточек в разделе «Все номера»."""
    booking_url = (listing_url or "").strip() or booking_url_for_room(room_id)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "btn_check_dates"),
                    url=booking_url,
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "btn_ask_manager_dates"),
                    callback_data=f"room:ask_dates:{list_index}",
                )
            ],
        ]
    )


def room_card_keyboard(
    lang: str,
    *,
    room_id: int,
    index: int,
    total: int,
    listing_url: str | None = None,
    photo_index: int = 0,
    gallery_size: int = 1,
) -> InlineKeyboardMarkup:
    """
    Кнопки под карточкой:
    - номер вперёд/назад (сбрасывают просмотр фото на первое);
    - при gallery_size > 1 — перелистывание фото того же лота;
    - ссылка на бронирование (listing_url или BOOKING_BASE_URL).
    Колбэк: room:idx:{индекс_в_списке}:{индекс_фото}.
    """
    prev_room = f"room:idx:{index - 1}:0" if index > 0 else "room:block"
    next_room = f"room:idx:{index + 1}:0" if index < total - 1 else "room:block"

    booking_url = (listing_url or "").strip() or booking_url_for_room(room_id)

    keyboard: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(text=t(lang, "btn_room_prev"), callback_data=prev_room),
            InlineKeyboardButton(text=t(lang, "btn_room_next"), callback_data=next_room),
        ],
    ]

    g = max(1, gallery_size)
    if g > 1:
        p = max(0, min(photo_index, g - 1))
        prev_ph = (p - 1) % g
        next_ph = (p + 1) % g
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=t(lang, "btn_room_photo_prev"),
                    callback_data=f"room:idx:{index}:{prev_ph}",
                ),
                InlineKeyboardButton(
                    text=t(lang, "btn_room_photo_next"),
                    callback_data=f"room:idx:{index}:{next_ph}",
                ),
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                text=t(lang, "btn_check_dates"),
                url=booking_url,
            )
        ]
    )
    keyboard.append(
        [
            InlineKeyboardButton(
                text=t(lang, "btn_ask_manager_dates"),
                callback_data=f"room:ask_dates:{index}",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def rating_keyboard(callback_prefix: str = "rev:rate") -> InlineKeyboardMarkup:
    """Оценка 1–5 одним рядом звёздочек (колбэк: rev:rate:3)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=str(n), callback_data=f"{callback_prefix}:{n}")
                for n in range(1, 6)
            ]
        ]
    )
