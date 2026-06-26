"""
Заглушка под будущую программу лояльности (в главном меню нет кнопки — можно вызвать /loyalty).
"""

from __future__ import annotations

import aiosqlite
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

import database
from keyboards.main_menu import language_inline_keyboard, main_reply_keyboard
from translations import t

router = Router(name="loyalty")


async def _lang(user_id: int) -> str | None:
    async with aiosqlite.connect(database.DB_PATH) as db:
        return await database.get_user_lang(db, user_id)


@router.message(Command("loyalty"))
async def cmd_loyalty(message: Message) -> None:
    """Мини-заглушка до появления реальной логики начисления баллов."""
    lang = await _lang(message.from_user.id)
    if lang is None:
        await message.answer(
            t("ru", "choose_language"),
            reply_markup=language_inline_keyboard(),
        )
        return
    await message.answer(t(lang, "loyalty_soon"), reply_markup=main_reply_keyboard(lang))
