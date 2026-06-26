"""
Настройки бота: секреты и параметры из .env (файл не коммитится).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Tuple

from dotenv import load_dotenv

# Явно читаем .env из папки проекта (рядом с этим файлом), а не только из текущего cwd.
load_dotenv(Path(__file__).resolve().parent / ".env")

# Токен от @BotFather
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError(
        "В .env не найден BOT_TOKEN. "
        "Добавьте строку: BOT_TOKEN=123456:ABC-DEF..."
    )


def _parse_admin_ids(raw: str | None) -> Tuple[int, ...]:
    """
    ADMIN_IDS в .env — список telegram user id через запятую.
    Пример: ADMIN_IDS=111111111,222222222
    Эти пользователи получают обращения из «Поддержки», запросы «Уточнить даты», модерацию отзывов и /support.
    """
    if not raw:
        return ()
    ids: list[int] = []
    for part in raw.replace(" ", "").split(","):
        if part.isdigit():
            ids.append(int(part))
    return tuple(set(ids))  # убираем дубликаты, порядок не важен


ADMIN_IDS: tuple[int, ...] = _parse_admin_ids(os.getenv("ADMIN_IDS"))

# Базовый URL страницы бронирования (кнопка «Проверить даты» добавит ?room_id=...)
BOOKING_BASE_URL = os.getenv("BOOKING_BASE_URL", "https://ru.airbnb.com/booking").rstrip("/")


def booking_url_for_room(room_id: int) -> str:
    """Ссылка для конкретного номера (подставьте свой сайт или модуль бронирования)."""
    return f"{BOOKING_BASE_URL}?room_id={room_id}"


def _int_from_env(name: str, default: int) -> int:
    """Целое из .env или значение по умолчанию (для лимитов антиспама)."""
    raw = os.getenv(name)
    if raw is None:
        return default
    raw = raw.strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(0, value)


# Минимальный интервал между отзывами одного пользователя (секунды). 0 = без ограничения.
REVIEW_COOLDOWN_SECONDS = _int_from_env("REVIEW_COOLDOWN_SECONDS", 3600)

# Сколько обращений в поддержку разрешено за окно SUPPORT_RATE_WINDOW_SECONDS.
SUPPORT_MAX_MESSAGES_PER_WINDOW = _int_from_env("SUPPORT_MAX_MESSAGES_PER_WINDOW", 5)
SUPPORT_RATE_WINDOW_SECONDS = _int_from_env("SUPPORT_RATE_WINDOW_SECONDS", 3600)
