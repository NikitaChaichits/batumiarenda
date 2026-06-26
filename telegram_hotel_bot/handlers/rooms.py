"""
Каталог номеров: карточка с фото (галерея), описанием, кнопки «Проверить даты на Airbnb» и «Уточнить даты у менеджера».
"""

from __future__ import annotations

import aiosqlite
from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InputMediaPhoto, Message, URLInputFile

import database
from config import (
    ADMIN_IDS,
    SUPPORT_MAX_MESSAGES_PER_WINDOW,
    SUPPORT_RATE_WINDOW_SECONDS,
    booking_url_for_room,
)
from keyboards.main_menu import language_inline_keyboard, main_reply_keyboard
from keyboards.rooms import room_card_keyboard, room_summary_actions_keyboard
from translations import main_menu_texts, t

router = Router(name="rooms")


class AskDatesStates(StatesGroup):
    """После кнопки «Уточнить даты» ждём одно текстовое сообщение с датами."""

    waiting_dates = State()


async def _load_rooms() -> list[dict]:
    async with aiosqlite.connect(database.DB_PATH) as db:
        return await database.fetch_rooms(db)


async def _lang_from_event(event: Message | CallbackQuery) -> str | None:
    uid = event.from_user.id
    async with aiosqlite.connect(database.DB_PATH) as db:
        return await database.get_user_lang(db, uid)


def _room_gallery(room: dict) -> list[str]:
    """Список URL для карточки (минимум один)."""
    imgs = room.get("images")
    if isinstance(imgs, list) and imgs:
        return [str(u) for u in imgs if str(u).strip()]
    if room.get("image_url"):
        return [str(room["image_url"])]
    return []


def _gallery_photo_url(room: dict, photo_index: int) -> str:
    g = _room_gallery(room)
    if not g:
        return ""
    photo_index = max(0, min(photo_index, len(g) - 1))
    return g[photo_index]


def _room_caption(room: dict, lang: str, photo_index: int) -> str:
    title = room["title_ru"] if lang == "ru" else room["title_en"]
    desc = room["description_ru"] if lang == "ru" else room["description_en"]
    base = t(
        lang,
        "room_caption",
        title=title,
        description=desc,
    )
    g = _room_gallery(room)
    if len(g) > 1:
        photo_index = max(0, min(photo_index, len(g) - 1))
        base += t(
            lang,
            "room_gallery_caption",
            cur=photo_index + 1,
            total=len(g),
        )
    return base


def _parse_room_callback(data: str) -> tuple[int, int] | None:
    """room:idx:{list_index}:{photo_index} → (list_index, photo_index)."""
    parts = data.split(":")
    if len(parts) < 3 or parts[0] != "room" or parts[1] != "idx":
        return None
    try:
        idx = int(parts[2])
        pic = int(parts[3]) if len(parts) >= 4 else 0
    except ValueError:
        return None
    return idx, pic


def _telegram_user_url(user_id: int, username: str | None) -> str:
    if username:
        return f"https://t.me/{username}"
    return f"tg://user?id={user_id}"


def _minutes_from_seconds(seconds: int) -> int:
    return max(1, (int(seconds) + 59) // 60)


async def _send_room_summary(
    message: Message, room: dict, lang: str, list_index: int
) -> None:
    """Одна карточка для списка «Все номера»: фото + подпись + кнопки Airbnb / менеджер."""
    caption_html = _room_caption(room, lang, 0)
    kb = room_summary_actions_keyboard(
        lang,
        room_id=int(room["id"]),
        list_index=list_index,
        listing_url=room.get("listing_url"),
    )
    g = _room_gallery(room)
    if g:
        await message.answer_photo(
            URLInputFile(g[0]),
            caption=caption_html,
            parse_mode="HTML",
            reply_markup=kb,
        )
    else:
        await message.answer(caption_html, parse_mode="HTML", reply_markup=kb)


async def _send_first_card(
    message: Message,
    rooms: list[dict],
    idx: int,
    lang: str,
    photo_index: int = 0,
) -> None:
    """Отправка карточки (первое открытие каталога)."""
    room = rooms[idx]
    photo_index = max(0, photo_index)
    caption_html = _room_caption(room, lang, photo_index)
    g = _room_gallery(room)
    url = _gallery_photo_url(room, photo_index)
    kb = room_card_keyboard(
        lang,
        room_id=int(room["id"]),
        index=idx,
        total=len(rooms),
        listing_url=room.get("listing_url"),
        photo_index=photo_index,
        gallery_size=len(g) if g else 1,
    )
    photo = URLInputFile(url)
    await message.answer_photo(
        photo,
        caption=caption_html,
        parse_mode="HTML",
        reply_markup=kb,
    )


async def _edit_card(
    callback: CallbackQuery,
    rooms: list[dict],
    idx: int,
    lang: str,
    photo_index: int,
) -> None:
    """Обновляем медиа и клавиатуру (смена лота или слайд галереи)."""
    room = rooms[idx]
    g = _room_gallery(room)
    photo_index = max(0, min(photo_index, len(g) - 1)) if g else 0
    caption_html = _room_caption(room, lang, photo_index)
    url = _gallery_photo_url(room, photo_index)
    kb = room_card_keyboard(
        lang,
        room_id=int(room["id"]),
        index=idx,
        total=len(rooms),
        listing_url=room.get("listing_url"),
        photo_index=photo_index,
        gallery_size=len(g) if g else 1,
    )
    media = InputMediaPhoto(media=url, caption=caption_html, parse_mode="HTML")
    await callback.message.edit_media(media, reply_markup=kb)


@router.message(F.text.in_(main_menu_texts("btn_rooms")))
async def menu_open_rooms(message: Message, state: FSMContext) -> None:
    """Кнопка «Номера»: сбрасываем FSM и показываем первый номер."""
    await state.clear()
    lang = await _lang_from_event(message)
    if lang is None:
        await message.answer(t("ru", "choose_language"), reply_markup=language_inline_keyboard())
        return

    rooms = await _load_rooms()
    if not rooms:
        await message.answer("⚠️ В базе ещё нет номеров — проверьте database.init_db().")
        return

    await message.answer(t(lang, "rooms_title"))
    await _send_first_card(message, rooms, 0, lang, 0)


@router.message(F.text.in_(main_menu_texts("btn_all_rooms")))
async def menu_all_rooms_list(message: Message, state: FSMContext) -> None:
    """Все объекты: подряд сообщения с фото и описанием."""
    await state.clear()
    lang = await _lang_from_event(message)
    if lang is None:
        await message.answer(t("ru", "choose_language"), reply_markup=language_inline_keyboard())
        return

    rooms = await _load_rooms()
    if not rooms:
        await message.answer("⚠️ В базе ещё нет номеров — проверьте database.init_db().")
        return

    await message.answer(
        t(lang, "all_rooms_heading", count=len(rooms)),
        parse_mode="HTML",
    )
    for i, room in enumerate(rooms):
        await _send_room_summary(message, room, lang, i)


@router.callback_query(F.data.startswith("room:ask_dates:"))
async def ask_dates_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Кнопка «Уточнить даты у менеджера» — просим текст с датами."""
    try:
        idx = int(callback.data.split(":")[2])
    except (IndexError, ValueError):
        await callback.answer()
        return

    await state.clear()
    lang = await _lang_from_event(callback)
    if lang is None:
        await callback.answer()
        return

    if not ADMIN_IDS:
        await callback.answer()
        if callback.message:
            await callback.message.answer(
                t(lang, "support_no_admins"),
                reply_markup=main_reply_keyboard(lang),
            )
        return

    rooms = await _load_rooms()
    if not rooms or idx < 0 or idx >= len(rooms):
        await callback.answer()
        return

    room = rooms[idx]
    listing = (room.get("listing_url") or "").strip() or booking_url_for_room(int(room["id"]))
    await state.set_state(AskDatesStates.waiting_dates)
    await state.update_data(listing_url=listing)
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            t(lang, "ask_dates_prompt") + "\n\n" + t(lang, "cmd_cancel"),
            reply_markup=main_reply_keyboard(lang),
        )


@router.message(StateFilter(AskDatesStates.waiting_dates), F.text)
async def ask_dates_deliver(message: Message, state: FSMContext, bot: Bot) -> None:
    """Отправляем менеджерам запрос с датами (тот же лимит, что и для поддержки)."""
    lang = await _lang_from_event(message)
    if lang is None:
        await state.clear()
        return

    data = await state.get_data()
    listing_url = str(data.get("listing_url", "")).strip()
    dates_text = message.text.strip()
    user_url = _telegram_user_url(message.from_user.id, message.from_user.username)

    if SUPPORT_MAX_MESSAGES_PER_WINDOW > 0:
        window = max(1, SUPPORT_RATE_WINDOW_SECONDS)
        async with aiosqlite.connect(database.DB_PATH) as db:
            recent = await database.count_support_events_in_window(
                db, message.from_user.id, window
            )
        if recent >= SUPPORT_MAX_MESSAGES_PER_WINDOW:
            await state.clear()
            await message.answer(
                t(lang, "rate_limit_support", minutes=_minutes_from_seconds(window)),
                reply_markup=main_reply_keyboard(lang),
            )
            return

    admin_text = (
        f"Пользователь - {user_url}\n"
        f"Апартаменты - {listing_url}\n"
        f"хочет уточнить свободен ли номер на эти даты - {dates_text}"
    )

    sent_ok = False
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, admin_text)
            sent_ok = True
        except Exception:
            continue

    if not sent_ok:
        await state.clear()
        await message.answer(
            t(lang, "support_send_failed"),
            reply_markup=main_reply_keyboard(lang),
        )
        return

    if SUPPORT_MAX_MESSAGES_PER_WINDOW > 0:
        async with aiosqlite.connect(database.DB_PATH) as db:
            await database.record_support_rate_event(db, message.from_user.id)

    await state.clear()
    await message.answer(t(lang, "ask_dates_sent"), reply_markup=main_reply_keyboard(lang))


@router.message(StateFilter(AskDatesStates.waiting_dates))
async def ask_dates_non_text(message: Message, state: FSMContext) -> None:
    lang = await _lang_from_event(message)
    if lang is None:
        await state.clear()
        return
    await message.answer(t(lang, "support_text_only"))


@router.callback_query(F.data.startswith("room:open:"))
async def room_open_from_list(callback: CallbackQuery) -> None:
    """Из старых сообщений со списком №1… — отправить полную карточку."""
    try:
        idx = int(callback.data.split(":")[2])
    except (IndexError, ValueError):
        await callback.answer()
        return

    lang = await _lang_from_event(callback)
    if lang is None:
        await callback.answer()
        return

    rooms = await _load_rooms()
    if not rooms or idx < 0 or idx >= len(rooms):
        await callback.answer()
        return

    if callback.message:
        await _send_first_card(callback.message, rooms, idx, lang, 0)
    await callback.answer()


@router.callback_query(F.data.startswith("room:idx:"))
async def room_card_callback(callback: CallbackQuery) -> None:
    """Смена карточки апартаментов или перелистывание фото внутри лота."""
    parsed = _parse_room_callback(callback.data)
    if parsed is None:
        await callback.answer()
        return
    idx, photo_index = parsed

    lang = await _lang_from_event(callback)
    if lang is None:
        await callback.answer()
        return

    rooms = await _load_rooms()
    if not rooms or idx < 0 or idx >= len(rooms):
        await callback.answer()
        return

    room = rooms[idx]
    g = _room_gallery(room)
    if g:
        photo_index = max(0, min(photo_index, len(g) - 1))
    else:
        photo_index = 0

    try:
        await _edit_card(callback, rooms, idx, lang, photo_index)
    except Exception:
        url = _gallery_photo_url(room, photo_index)
        await callback.message.answer_photo(
            URLInputFile(url),
            caption=_room_caption(room, lang, photo_index),
            parse_mode="HTML",
            reply_markup=room_card_keyboard(
                lang,
                room_id=int(room["id"]),
                index=idx,
                total=len(rooms),
                listing_url=room.get("listing_url"),
                photo_index=photo_index,
                gallery_size=len(g) if g else 1,
            ),
        )

    await callback.answer()


@router.callback_query(F.data == "room:block")
async def room_nav_blocked(callback: CallbackQuery) -> None:
    """Край каталога по апартаментам."""
    lang = await _lang_from_event(callback)
    if lang is None:
        await callback.answer()
        return
    await callback.answer(t(lang, "room_nav_end"), show_alert=True)
