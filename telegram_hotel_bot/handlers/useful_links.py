"""
Раздел «Полезные ссылки»: карты (отель, магазины, ТЦ).
"""

from __future__ import annotations

import aiosqlite
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import database
from keyboards.main_menu import language_inline_keyboard
from keyboards.useful_links import useful_links_keyboard
from translations import main_menu_texts, t

router = Router(name="useful_links")


async def _lang(user_id: int) -> str | None:
    async with aiosqlite.connect(database.DB_PATH) as db:
        return await database.get_user_lang(db, user_id)


@router.message(F.text.in_(main_menu_texts("btn_useful_links")))
async def open_useful_links(message: Message, state: FSMContext) -> None:
    await state.clear()
    lang = await _lang(message.from_user.id)
    if lang is None:
        await message.answer(t("ru", "choose_language"), reply_markup=language_inline_keyboard())
        return

    await message.answer(
        t(lang, "useful_links_intro"),
        reply_markup=useful_links_keyboard(lang),
    )
