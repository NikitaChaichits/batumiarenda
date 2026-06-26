"""
FAQ: вопросы «из книги отеля», ответы подставляются из translations (пока заглушка).
"""

from __future__ import annotations

import aiosqlite
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import database
from keyboards.main_menu import language_inline_keyboard
from translations import faq_answer, faq_items, main_menu_texts, t

router = Router(name="faq")


def _faq_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Список вопросов; callback_data вида faq:<key> (короткий ключ для лимита 64 байта)."""
    rows: list[list[InlineKeyboardButton]] = []
    for item in faq_items(lang):
        q = item["question"]
        if len(q) > 64:
            q = q[:61] + "..."
        rows.append(
            [InlineKeyboardButton(text=q, callback_data=f"faq:{item['key']}")],
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _lang(message: Message | CallbackQuery) -> str | None:
    uid = message.from_user.id
    async with aiosqlite.connect(database.DB_PATH) as db:
        return await database.get_user_lang(db, uid)


@router.message(F.text.in_(main_menu_texts("btn_faq")))
async def menu_open_faq(message: Message, state: FSMContext) -> None:
    """Кнопка «FAQ» — показываем список вопросов."""
    await state.clear()
    lang = await _lang(message)
    if lang is None:
        await message.answer(t("ru", "choose_language"), reply_markup=language_inline_keyboard())
        return

    await message.answer(
        t(lang, "faq_title"),
        reply_markup=_faq_keyboard(lang),
    )


@router.callback_query(F.data.startswith("faq:"))
async def faq_open_item(callback: CallbackQuery) -> None:
    """Показ ответа или возврат к списку."""
    lang = await _lang(callback)
    if lang is None:
        await callback.answer()
        return

    payload = callback.data.split(":", 1)[1]

    if payload == "back":
        try:
            await callback.message.edit_text(
                t(lang, "faq_title"),
                reply_markup=_faq_keyboard(lang),
            )
        except Exception:
            await callback.message.answer(
                t(lang, "faq_title"),
                reply_markup=_faq_keyboard(lang),
            )
        await callback.answer()
        return

    item_key = payload
    question = next((i["question"] for i in faq_items(lang) if i["key"] == item_key), "")
    answer = faq_answer(lang, item_key)

    text = f"<b>{question}</b>\n\n{answer}"
    back_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "faq_back"), callback_data="faq:back")],
        ],
    )

    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_kb)
    except Exception:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=back_kb)

    await callback.answer()
