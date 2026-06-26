"""Пакет обработчиков: роутеры подключаются в main.py."""

from handlers.faq import router as faq_router
from handlers.loyalty import router as loyalty_router
from handlers.reviews import router as reviews_router
from handlers.rooms import router as rooms_router
from handlers.start import router as start_router
from handlers.support import router as support_router
from handlers.useful_links import router as useful_links_router

__all__ = [
    "faq_router",
    "loyalty_router",
    "reviews_router",
    "rooms_router",
    "start_router",
    "support_router",
    "useful_links_router",
]
