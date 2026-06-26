"""
Отзывы: подменю (оставить / посмотреть), FSM оценка → текст, модерация через ADMIN_IDS.
"""

from __future__ import annotations

import html

import aiosqlite
from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import database
from config import ADMIN_IDS, REVIEW_COOLDOWN_SECONDS
from keyboards.main_menu import language_inline_keyboard, main_reply_keyboard
from keyboards.review_menu import review_entry_keyboard
from keyboards.rooms import rating_keyboard
from translations import main_menu_texts, t

router = Router(name="reviews")

_REVIEW_LIST_FETCH_LIMIT = 25
_TELEGRAM_MAX_MESSAGE = 4090
_ADMIN_REVIEW_TEXT_MAX = 3500


class ReviewStates(StatesGroup):
    """Пошаговая форма одного отзыва."""

    rating = State()
    comment = State()


async def _lang(user_id: int) -> str | None:
    async with aiosqlite.connect(database.DB_PATH) as db:
        return await database.get_user_lang(db, user_id)


async def _admin_lang(user_id: int) -> str:
    lang = await _lang(user_id)
    return lang if lang in {"ru", "en"} else "ru"


def _minutes_from_seconds(seconds: int) -> int:
    return max(1, (int(seconds) + 59) // 60)


def _format_review_block(rev: dict, lang: str) -> str:
    rating = int(rev.get("rating") or 0)
    rating = max(1, min(5, rating))
    stars = "⭐" * rating
    raw_text = (rev.get("text") or "").strip() or "—"
    body = html.escape(raw_text)
    name_raw = (rev.get("guest_name") or "").strip() or t(lang, "review_author_guest")
    name_e = html.escape(name_raw)
    date_s = html.escape(str(rev.get("created_at") or "")[:10])
    photo = " 📷" if rev.get("photo_file_id") else ""
    return f"{stars}{photo}\n{body}\n<i>{name_e} · {date_s}</i>"


def _truncate_admin_text(text: str) -> str:
    raw = html.escape(text.strip())
    if len(raw) > _ADMIN_REVIEW_TEXT_MAX:
        return raw[: _ADMIN_REVIEW_TEXT_MAX - 1] + "…"
    return raw


async def _notify_admins_review_pending(
    bot: Bot,
    *,
    review_id: int,
    user_id: int,
    rating: int,
    text: str,
) -> None:
    """Шлёт в личку админам карточку отзыва с кнопкой «Одобрить»."""
    if not ADMIN_IDS:
        return
    stars = "⭐" * max(1, min(5, int(rating)))
    body = _truncate_admin_text(text)
    for admin_id in ADMIN_IDS:
        admin_lang = await _admin_lang(admin_id)
        btn = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=t(admin_lang, "btn_review_approve"),
                        callback_data=f"rev:approve:{review_id}",
                    ),
                ],
            ]
        )
        note = t(
            admin_lang,
            "admin_review_pending",
            review_id=review_id,
            user_id=user_id,
            stars=stars,
            text=body,
        )
        try:
            await bot.send_message(admin_id, note, parse_mode="HTML", reply_markup=btn)
        except Exception:
            continue


async def _send_reviews_list(from_message: Message, lang: str) -> None:
    async with aiosqlite.connect(database.DB_PATH) as db:
        rows = await database.fetch_recent_reviews(db, limit=_REVIEW_LIST_FETCH_LIMIT)
    if not rows:
        await from_message.answer(
            t(lang, "reviews_empty"),
            reply_markup=main_reply_keyboard(lang),
        )
        return

    blocks = [_format_review_block(r, lang) for r in rows]
    header = t(lang, "reviews_list_title")
    chunks: list[str] = []
    buf = header + "\n\n"
    for b in blocks:
        addition = b + "\n\n"
        if len(buf) + len(addition) > _TELEGRAM_MAX_MESSAGE:
            chunks.append(buf.rstrip())
            buf = addition
        else:
            buf += addition
    if buf.strip():
        chunks.append(buf.rstrip())

    for i, chunk in enumerate(chunks):
        await from_message.answer(
            chunk,
            parse_mode="HTML",
            reply_markup=main_reply_keyboard(lang) if i == len(chunks) - 1 else None,
        )


@router.callback_query(F.data.startswith("rev:approve:"))
async def review_approve_callback(callback: CallbackQuery) -> None:
    """Только ADMIN_IDS: публикация отзыва в ленте «Посмотреть отзывы»."""
    admin_lang = await _admin_lang(callback.from_user.id)
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer(t(admin_lang, "review_not_admin"), show_alert=True)
        return
    try:
        review_id = int(callback.data.split(":")[2])
    except (IndexError, ValueError):
        await callback.answer()
        return

    async with aiosqlite.connect(database.DB_PATH) as db:
        ok = await database.approve_review(db, review_id)

    await callback.answer(
        t(admin_lang, "review_approve_ok" if ok else "review_approve_fail"),
        show_alert=not ok,
    )
    if ok and callback.message:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass


@router.message(F.text.in_(main_menu_texts("btn_reviews")))
async def review_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    lang = await _lang(message.from_user.id)
    if lang is None:
        await message.answer(t("ru", "choose_language"), reply_markup=language_inline_keyboard())
        return

    await message.answer(
        t(lang, "review_menu_prompt"),
        reply_markup=review_entry_keyboard(lang),
    )


@router.callback_query(F.data == "rev:write")
async def review_begin_write(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    lang = await _lang(callback.from_user.id)
    if lang is None:
        await callback.answer()
        return

    if REVIEW_COOLDOWN_SECONDS > 0:
        async with aiosqlite.connect(database.DB_PATH) as db:
            left = await database.review_cooldown_seconds_left(
                db, callback.from_user.id, REVIEW_COOLDOWN_SECONDS
            )
        if left > 0:
            await callback.answer()
            if callback.message:
                await callback.message.answer(
                    t(lang, "rate_limit_review", minutes=_minutes_from_seconds(left)),
                    reply_markup=main_reply_keyboard(lang),
                )
            return

    await state.set_state(ReviewStates.rating)
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            t(lang, "review_start") + "\n" + t(lang, "cmd_cancel"),
            reply_markup=rating_keyboard(),
        )


@router.callback_query(F.data == "rev:browse")
async def review_browse(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    lang = await _lang(callback.from_user.id)
    if lang is None:
        await callback.answer()
        return
    await callback.answer()
    if callback.message:
        await _send_reviews_list(callback.message, lang)


@router.callback_query(ReviewStates.rating, F.data.startswith("rev:rate:"))
async def review_set_rating(callback: CallbackQuery, state: FSMContext) -> None:
    lang = await _lang(callback.from_user.id)
    if lang is None:
        await callback.answer()
        await state.clear()
        return

    rating = int(callback.data.split(":")[2])
    await state.update_data(rating=rating)
    await state.set_state(ReviewStates.comment)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(t(lang, "review_ask_text"))
    await callback.answer()


@router.message(ReviewStates.comment, F.text)
async def review_set_text(message: Message, state: FSMContext, bot: Bot) -> None:
    lang = await _lang(message.from_user.id)
    if lang is None:
        await state.clear()
        return

    data = await state.get_data()
    ok, left, review_id = await _try_persist_review(
        telegram_id=message.from_user.id,
        rating=int(data["rating"]),
        text=message.text.strip(),
    )
    await state.clear()
    if not ok:
        await message.answer(
            t(lang, "rate_limit_review", minutes=_minutes_from_seconds(left)),
            reply_markup=main_reply_keyboard(lang),
        )
        return

    pending = bool(ADMIN_IDS) and review_id is not None
    if pending:
        await _notify_admins_review_pending(
            bot,
            review_id=review_id,
            user_id=message.from_user.id,
            rating=int(data["rating"]),
            text=message.text.strip(),
        )
        await message.answer(t(lang, "review_thanks_pending"), reply_markup=main_reply_keyboard(lang))
    else:
        await message.answer(t(lang, "review_thanks"), reply_markup=main_reply_keyboard(lang))


async def _try_persist_review(
    *,
    telegram_id: int,
    rating: int,
    text: str,
) -> tuple[bool, int, int | None]:
    """
    Пишет отзыв. Если заданы ADMIN_IDS — approved=0 до модерации, иначе сразу 1.
    Возвращает (успех, секунд cooldown при отказе, id отзыва при успехе).
    """
    approved = 0 if ADMIN_IDS else 1
    async with aiosqlite.connect(database.DB_PATH) as db:
        if REVIEW_COOLDOWN_SECONDS > 0:
            left = await database.review_cooldown_seconds_left(
                db, telegram_id, REVIEW_COOLDOWN_SECONDS
            )
            if left > 0:
                return False, left, None
        rid = await database.insert_review(db, telegram_id, rating, text, None, approved=approved)
    return True, 0, rid
