"""
Вспомогательные функции для многоязычия: выбор словаря ru/en и FAQ.
"""

from __future__ import annotations

from typing import FrozenSet

from translations import en as en_mod
from translations import ru as ru_mod


def t(lang: str, key: str, **kwargs: object) -> str:
    """
    Возвращает строку по ключу для языка lang ('ru' или 'en').
    kwargs передаются в str.format(...).
    """
    table = ru_mod.MESSAGES if lang == "ru" else en_mod.MESSAGES
    text = table[key]
    return text.format(**kwargs) if kwargs else text


def faq_items(lang: str) -> list[dict[str, str]]:
    """Список вопросов FAQ для выбранного языка."""
    return ru_mod.FAQ_ITEMS if lang == "ru" else en_mod.FAQ_ITEMS


def faq_answer(lang: str, item_key: str) -> str:
    """
    Текст ответа по ключу вопроса.
    Если в модуле языка нет готового ответа — возвращается общая заглушка.
    """
    answers = ru_mod.FAQ_ANSWERS if lang == "ru" else en_mod.FAQ_ANSWERS
    if item_key in answers and answers[item_key].strip():
        return answers[item_key].strip()
    return t(lang, "faq_placeholder")


def main_menu_texts(key: str) -> FrozenSet[str]:
    """
    Множество вариантов текста кнопки на двух языках — чтобы ловить нажатия ReplyKeyboard
    без отдельного middleware.
    """
    return frozenset({ru_mod.MESSAGES[key], en_mod.MESSAGES[key]})
