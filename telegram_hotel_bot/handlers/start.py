"""
/start, выбор языка и общие команды (/cancel). Главное меню показывается после выбора языка.
"""

from __future__ import annotations

import aiosqlite
from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import database
from keyboards.main_menu import language_inline_keyboard, main_reply_keyboard
from translations import main_menu_texts, t

router = Router(name="start")


async def _lang_or_prompt(message: Message) -> str | None:
    """Читает язык пользователя из БД; если его ещё нет — предлагает выбрать."""
    async with aiosqlite.connect(database.DB_PATH) as db:
        lang = await database.get_user_lang(db, message.from_user.id)
    if lang is None:
        await message.answer(
            t("ru", "choose_language"),
            reply_markup=language_inline_keyboard(),
        )
        return None
    return lang


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """
    Команда /start:
    - обновляем запись пользователя в БД;
    - если язык не выбран — показываем inline RU/EN;
    - если выбран — приветствие и ReplyKeyboard главного меню.
    """
    async with aiosqlite.connect(database.DB_PATH) as db:
        await database.ensure_user(
            db,
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name,
        )
        lang = await database.get_user_lang(db, message.from_user.id)

    if lang is None:
        await message.answer(
            t("ru", "choose_language"),
            reply_markup=language_inline_keyboard(),
        )
        return

    name = message.from_user.first_name or ""
    await message.answer(
        t(lang, "welcome", name=name) + "\n\n" + t(lang, "main_menu_hint"),
        reply_markup=main_reply_keyboard(lang),
    )


@router.callback_query(F.data.startswith("setlang:"))
async def callback_set_language(callback: CallbackQuery) -> None:
    """Пользователь нажал «Русский» или «English» — сохраняем код языка в SQLite."""
    chosen = callback.data.split(":")[1]
    if chosen not in {"ru", "en"}:
        await callback.answer()
        return

    async with aiosqlite.connect(database.DB_PATH) as db:
        await database.ensure_user(
            db,
            callback.from_user.id,
            callback.from_user.username,
            callback.from_user.first_name,
        )
        await database.set_user_lang(db, callback.from_user.id, chosen)

    lang = chosen
    await callback.answer(t(lang, "language_changed"), show_alert=False)

    # Убираем кнопки под сообщением с выбором языка
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        # Если Telegram не даёт отредактировать — не мешаем дальнейшему сценарию
        pass

    name = callback.from_user.first_name or ""
    await callback.message.answer(
        t(lang, "welcome", name=name) + "\n\n" + t(lang, "main_menu_hint"),
        reply_markup=main_reply_keyboard(lang),
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext) -> None:
    """
    Команда /menu: сбрасывает FSM и снова показывает главное меню
    (удобно, если пользователь «застрял» в середине отзыва или поддержки).
    """
    await state.clear()
    async with aiosqlite.connect(database.DB_PATH) as db:
        await database.ensure_user(
            db,
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name,
        )
        lang = await database.get_user_lang(db, message.from_user.id)

    if lang is None:
        await message.answer(
            t("ru", "choose_language"),
            reply_markup=language_inline_keyboard(),
        )
        return

    await message.answer(
        t(lang, "cmd_menu") + "\n\n" + t(lang, "main_menu_hint"),
        reply_markup=main_reply_keyboard(lang),
    )


@router.message(F.text.in_(main_menu_texts("btn_language")))
async def menu_change_language(message: Message) -> None:
    """Кнопка «Язык» — снова показываем inline, текущий язык остаётся до выбора нового."""
    lang = await _lang_or_prompt(message)
    if lang is None:
        return
    await message.answer(
        t(lang, "choose_language"),
        reply_markup=language_inline_keyboard(),
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    """Сбрасывает машину состояний (отзыв, поддержка и т.д.) и возвращает в меню."""
    await state.clear()
    lang = await _lang_or_prompt(message)
    if lang is None:
        return
    await message.answer(
        t(lang, "flow_cancelled"),
        reply_markup=main_reply_keyboard(lang),
    )
