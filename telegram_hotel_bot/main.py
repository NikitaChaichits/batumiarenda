"""
Запуск бота: инициализация БД, FSM-хранилище, регистрация роутеров по приоритету.
"""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN

import database
from handlers import (
    faq_router,
    loyalty_router,
    reviews_router,
    rooms_router,
    start_router,
    support_router,
    useful_links_router,
)

logging.basicConfig(level=logging.INFO)


async def on_startup() -> None:
    """
    При старте polling: создаём таблицы и при необходимости пересобираем каталог номеров.
    FSM в памяти: после перезапуска незавершённые сценарии (отзыв, поддержка, уточнение дат) сбрасываются.
    """
    await database.init_db()


async def main() -> None:
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.startup.register(on_startup)

    # Порядок важен: команды и язык → FSM (отзыв, поддержка) → каталог и FAQ.
    dp.include_router(start_router)
    dp.include_router(reviews_router)
    dp.include_router(support_router)
    dp.include_router(rooms_router)
    dp.include_router(faq_router)
    dp.include_router(useful_links_router)
    dp.include_router(loyalty_router)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
