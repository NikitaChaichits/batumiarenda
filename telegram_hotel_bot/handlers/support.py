"""
Поддержка: команда /support или кнопка меню — пользователь пишет текст, мы шлём его админам.
"""

from __future__ import annotations

import aiosqlite
from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

import database
from config import (
    ADMIN_IDS,
    SUPPORT_MAX_MESSAGES_PER_WINDOW,
    SUPPORT_RATE_WINDOW_SECONDS,
)
from keyboards.main_menu import language_inline_keyboard, main_reply_keyboard
from translations import main_menu_texts, t

router = Router(name="support")


class SupportStates(StatesGroup):
    """Ожидаем одно текстовое обращение от гостя."""

    waiting_text = State()


async def _lang(user_id: int) -> str | None:
    async with aiosqlite.connect(database.DB_PATH) as db:
        return await database.get_user_lang(db, user_id)


def _minutes_from_seconds(seconds: int) -> int:
    return max(1, (int(seconds) + 59) // 60)


async def _enter_support_flow(message: Message, state: FSMContext) -> None:
    """Общий вход: сохраняем состояние и просим описать проблему."""
    await state.clear()
    lang = await _lang(message.from_user.id)
    if lang is None:
        await message.answer(t("ru", "choose_language"), reply_markup=language_inline_keyboard())
        return

    if not ADMIN_IDS:
        await message.answer(
            t(lang, "support_no_admins"),
            reply_markup=main_reply_keyboard(lang),
        )
        return

    await state.set_state(SupportStates.waiting_text)
    await message.answer(
        t(lang, "support_intro") + "\n\n" + t(lang, "cmd_cancel"),
        reply_markup=main_reply_keyboard(lang),
    )


@router.message(Command("support"))
async def cmd_support(message: Message, state: FSMContext) -> None:
    """Эскалация администратору через команду /support."""
    await _enter_support_flow(message, state)


@router.message(F.text.in_(main_menu_texts("btn_support")))
async def menu_support(message: Message, state: FSMContext) -> None:
    """То же самое через кнопку «Поддержка»."""
    await _enter_support_flow(message, state)


@router.message(SupportStates.waiting_text, F.text)
async def support_deliver(message: Message, state: FSMContext, bot: Bot) -> None:
    """Пересылаем текст администраторам из ADMIN_IDS (telegram user id)."""
    lang = await _lang(message.from_user.id)
    if lang is None:
        await state.clear()
        return

    if not ADMIN_IDS:
        await state.clear()
        await message.answer(t(lang, "support_no_admins"), reply_markup=main_reply_keyboard(lang))
        return

    # Лимит сообщений в поддержку за скользящее окно (см. .env).
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

    username = message.from_user.username
    uname = f"@{username}" if username else "(без username)"

    admin_text = (
        "🛎 <b>Обращение в поддержку</b>\n"
        f"От: {uname}\n"
        f"user_id: <code>{message.from_user.id}</code>\n\n"
        f"{message.text}"
    )

    sent_ok = False
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, admin_text, parse_mode="HTML")
            sent_ok = True
        except Exception:
            # Не валим сценарий гостя, если один админ недоступен / не начинал чат с ботом.
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
    await message.answer(t(lang, "support_sent"), reply_markup=main_reply_keyboard(lang))


@router.message(SupportStates.waiting_text)
async def support_non_text(message: Message, state: FSMContext) -> None:
    """Если пришло не текст (фото, стикер) — просим отправить текстом."""
    lang = await _lang(message.from_user.id)
    if lang is None:
        await state.clear()
        return
    await message.answer(t(lang, "support_text_only"))
