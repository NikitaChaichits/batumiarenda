"""
Работа с SQLite через aiosqlite: пользователи, номера, отзывы, события для rate limit.
База создаётся автоматически рядом с этим файлом (hotel_bot.db).
"""

from __future__ import annotations

import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import aiosqlite

# Путь к файлу БД: по умолчанию рядом с кодом; на Railway — volume через DB_PATH=/data/hotel_bot.db
_default_db = Path(__file__).resolve().parent / "hotel_bot.db"
DB_PATH = Path(os.getenv("DB_PATH", str(_default_db)))

# При увеличении каталог пересоберётся из AIRBNB_LISTINGS.
_CATALOG_DB_VERSION = 4

# URL объявления + первая картинка (обложка). В каждом элементе AIRBNB_LISTINGS можно
# расширить "images" до нескольких URL (рекомендуем до 3–5 для скорости).
_AIRBNB_PAIRS: list[tuple[str, str]] = [
    (
        "https://www.airbnb.ru/rooms/1394696493286335612",
        "https://a0.muscache.com/im/pictures/hosting/Hosting-1394696493286335612/original/30df7c9b-2adf-41d7-9841-c52de06da805.jpeg?im_w=1200&quality=80&auto=webp",
    ),
    (
        "https://www.airbnb.ru/rooms/1415202849494099312",
        "https://a0.muscache.com/im/pictures/hosting/Hosting-1415202849494099312/original/101c5bdf-abc6-48b8-b690-49c07a458ed7.jpeg?im_w=1200&quality=80&auto=webp",
    ),
    (
        "https://www.airbnb.ru/rooms/1420142603759900069",
        "https://a0.muscache.com/im/pictures/hosting/Hosting-1420142603759900069/original/4d6db88d-e111-476e-90d4-59908a8d6baf.jpeg?im_w=1200&quality=80&auto=webp",
    ),
    (
        "https://www.airbnb.ru/rooms/1420842588733636305",
        "https://a0.muscache.com/im/pictures/hosting/Hosting-1420842588733636305/original/e82fee79-0acf-4a28-90e7-ffa361d9df2b.jpeg?im_w=1200&quality=80&auto=webp",
    ),
    (
        "https://www.airbnb.ru/rooms/1423221548597991755",
        "https://a0.muscache.com/im/pictures/hosting/Hosting-1423221548597991755/original/4f387d34-dd84-4412-a2e2-993cf3edf80f.jpeg?im_w=1200&quality=80&auto=webp",
    ),
    (
        "https://www.airbnb.ru/rooms/1426767859444130423",
        "https://a0.muscache.com/im/pictures/hosting/Hosting-1426767859444130423/original/84a33f63-bba9-4095-8d9d-5adeeadb3f81.jpeg?im_w=1200&quality=80&auto=webp",
    ),
    (
        "https://www.airbnb.ru/rooms/1441095766680610504",
        "https://a0.muscache.com/im/pictures/hosting/Hosting-1441095766680610504/original/57822b5c-157b-4020-a613-ee9911c72cba.jpeg?im_w=1200&quality=80&auto=webp",
    ),
    (
        "https://www.airbnb.ru/rooms/1444808717167247868",
        "https://a0.muscache.com/im/pictures/hosting/Hosting-1444808717167247868/original/ce352bf2-6863-4b72-a267-0a40d4765a6f.jpeg?im_w=1200&quality=80&auto=webp",
    ),
    (
        "https://www.airbnb.ru/rooms/1449384133790567823",
        "https://a0.muscache.com/im/pictures/hosting/Hosting-1449384133790567823/original/d9a5a451-188e-4ce5-acb4-acc1a2d1fb15.jpeg?im_w=1200&quality=80&auto=webp",
    ),
    (
        "https://www.airbnb.ru/rooms/1486341370739729896",
        "https://a0.muscache.com/im/pictures/hosting/Hosting-1486341370739729896/original/e06a166f-3c8a-49a6-b59f-73fe4c881cb6.jpeg?im_w=1200&quality=80&auto=webp",
    ),
    (
        "https://www.airbnb.ru/rooms/1570735627701941830",
        "https://a0.muscache.com/im/pictures/hosting/Hosting-1570735627701941830/original/ec73881e-2ff5-4069-a075-9535ef60821f.jpeg?im_w=1200&quality=80&auto=webp",
    ),
    (
        "https://www.airbnb.ru/rooms/1625214524408934808",
        "https://a0.muscache.com/im/pictures/hosting/Hosting-1625214524408934808/original/bbea883a-3c4e-41e3-9f64-dfc79b74e8bc.jpeg?im_w=1200&quality=80&auto=webp",
    ),
    (
        "https://www.airbnb.ru/rooms/1657887278747146237",
        "https://a0.muscache.com/im/pictures/hosting/Hosting-1657887278747146237/original/108bf14f-ee34-47a8-89b9-d83304081faa.jpeg?im_w=1200&quality=80&auto=webp",
    ),
    (
        "https://www.airbnb.ru/rooms/1660716668925148543",
        "https://a0.muscache.com/im/pictures/hosting/Hosting-1660716668925148543/original/087b2e45-d1ec-453d-b68f-e6c3a21aa3cf.jpeg?im_w=1200&quality=80&auto=webp",
    ),
    (
        "https://www.airbnb.ru/rooms/1676711262505053602",
        "https://a0.muscache.com/im/pictures/hosting/Hosting-1676711262505053602/original/0ee12455-9ccc-4383-82cd-b165a6aae93f.jpeg?im_w=1200&quality=80&auto=webp",
    ),
    (
        "https://www.airbnb.ru/rooms/1681728769269631627",
        "https://a0.muscache.com/im/pictures/hosting/Hosting-1681728769269631627/original/4d89cbbb-49c3-4a09-b729-a221597d37fb.jpeg?im_w=1200&quality=80&auto=webp",
    ),
]

# Уникальные тексты карточек (RU / EN) — отредактируйте под каждый объект.
_DESCRIPTIONS_RU: list[str] = [
    (
        "Раздвиньте шторы — открывается панорама Кавказских гор: вид, из‑за которого хочется замедлиться "
        "и по-настоящему насладиться утром.\n\n"
        "До пляжа и набережной — около 5 минут пешком.\n\n"
        "Внутри:\n"
        "- двуспальная кровать King size\n"
        "- оборудованная кухня, быстрый Wi‑Fi, Smart TV, кондиционер\n\n"
        "Студия в хорошем состоянии: чистая, современная, комфортная. "
        "Стойка регистрации в здании работает круглосуточно — заселение без оглядки на время."
    ),
    (
        "Уютная база на Новом бульваре Батуми: рядом море, набережная и парк — всё в пешей доступности.\n\n"
        "Внутри:\n"
        "- двуспальная кровать\n"
        "- мини-кухня со всем необходимым\n"
        "- быстрый Wi‑Fi\n"
        "- кондиционеры и центральное отопление\n"
        "- стиральная машина\n"
        "- балкон с видом на город и горы"
    ),
    (
        "Море — первое, что увидите, открыв глаза: не с балкона, а с кровати.\n\n"
        "Светлая студия на 12-м этаже на Новом бульваре. До пляжа и набережной — пешком.\n\n"
        "Внутри:\n"
        "- кровать King size\n"
        "- оборудованная кухня и стиральная машина\n"
        "- отдельное рабочее место\n"
        "- Smart TV, быстрый Wi‑Fi, кондиционер"
    ),
    (
        "Просторная студия у моря на Новом бульваре: 18-й этаж, вид на море и город. Пляж, набережная и парк — рядом.\n\n"
        "Внутри:\n"
        "- двуспальная кровать\n"
        "- мини-кухня, полностью укомплектованная\n"
        "- быстрый Wi‑Fi\n"
        "- кондиционеры и центральное отопление\n"
        "- стиральная машина\n"
        "- гардеробная у входа\n"
        "- балкон с видом на море и город"
    ),
    (
        "Отдельный балкон с боковым видом на море: студия на Новом бульваре, до пляжа и парка — пешком. "
        "Спокойное, комфортное жильё без лишнего.\n\n"
        "Внутри:\n"
        "- двуспальная кровать\n"
        "- мини-кухня\n"
        "- Smart TV и быстрый Wi‑Fi\n"
        "- балкон с видом на море и город сбоку"
    ),
    (
        "17-й этаж: ниже шум города, выше — море. Подходит для неспешного утра и тихого вечера: "
        "восход и закат из одного окна.\n\n"
        "Светлая студия на Новом бульваре. До пляжа и набережной — пешком.\n\n"
        "Внутри:\n"
        "- двуспальная кровать\n"
        "- оборудованная кухня и стиральная машина\n"
        "- Smart TV, быстрый Wi‑Fi, кондиционер"
    ),
    (
        "Светлая квартира около 45 м² с отдельной спальней — для спокойного отдыха на Новом бульваре.\n\n"
        "Внутри:\n"
        "- полностью оборудованная кухня\n"
        "- двуспальная кровать\n"
        "- кондиционер, отопление, Smart TV, стиральная машина\n"
        "- балкон с панорамным видом на горы\n"
        "- свежее бельё и полотенца\n"
        "- уборка перед заездом; дополнительная — по запросу"
    ),
    (
        "Студия у моря на Новом бульваре, комплекс Steps Residence. Тихое жильё с балконом. Пляж, набережная и парк — пешком.\n\n"
        "Внутри:\n"
        "- двуспальная кровать\n"
        "- мини-кухня\n"
        "- быстрый Wi‑Fi\n"
        "- кондиционеры и центральное отопление\n"
        "- стиральная машина\n"
        "- балкон с видом на внутренний двор"
    ),
    (
        "Светлая студия на 8-м этаже на Новом бульваре. До пляжа и набережной — пешком.\n\n"
        "Внутри:\n"
        "- кровать King size\n"
        "- оборудованная кухня и стиральная машина\n"
        "- Smart TV, быстрый Wi‑Fi, кондиционер"
    ),
    (
        "Когда нужно жильё без сюрпризов: чистое, тихое и как в описании.\n\n"
        "Светлая студия на 7-м этаже: много дневного света, вид на сад, без шума с улицы. "
        "До пляжа и набережной — около 5 минут пешком.\n\n"
        "Внутри:\n"
        "- кровать King size\n"
        "- оборудованная кухня и стиральная машина\n"
        "- быстрый Wi‑Fi, Smart TV, кондиционер"
    ),
    (
        "Студия с балконом на Новом бульваре: до моря, набережной и парка — несколько минут пешком.\n\n"
        "Светлая студия около 28 м². Внутри:\n"
        "- двуспальная кровать\n"
        "- мини-кухня\n"
        "- Smart TV и быстрый Wi‑Fi\n"
        "- балкон с видом на тихий внутренний двор"
    ),
    (
        "Утро с кофе на балконе и морским бризом. Студия в центре Нового бульвара — до пляжа около четырёх минут.\n\n"
        "Внутри:\n"
        "- двуспальная кровать\n"
        "- мини-кухня\n"
        "- быстрый Wi‑Fi, Smart TV, кондиционер\n\n"
        "Простое, но продуманное жильё — всё нужное под рукой, без лишнего."
    ),
    (
        "Студия у моря на Новом бульваре: тихое жильё с балконом и видом на сад. Пляж и набережная — пешком.\n\n"
        "Внутри:\n"
        "- двуспальная кровать\n"
        "- мини-кухня\n"
        "- Smart TV и быстрый Wi‑Fi\n"
        "- кондиционеры и центральное отопление\n"
        "- стиральная машина\n"
        "- балкон с видом на сад"
    ),
    (
        "Утренний кофе на собственном балконе с видом на море. Студия на Новом бульваре: пляж, набережная и парк — рядом.\n\n"
        "Внутри:\n"
        "- двуспальная кровать\n"
        "- полностью оборудованная кухня\n"
        "- Smart TV и быстрый Wi‑Fi\n"
        "- балкон с боковым видом на море"
    ),
    (
        "Двухкомнатная квартира на 19-м этаже: панорамные окна и балконы в спальнях — вид на горы и город. "
        "До пляжа — около 350 м пешком.\n\n"
        "Много света в течение дня. Внутри:\n"
        "- две спальни, в каждой балкон и панорамные окна\n"
        "- оборудованная кухня\n"
        "- кондиционер и Smart TV в комнатах"
    ),
    (
        "Море — первое, что увидите, открыв глаза: не с балкона, а с кровати.\n\n"
        "Светлая студия на Новом бульваре. До пляжа и набережной — около 5 минут пешком.\n\n"
        "Внутри:\n"
        "- кровать King size\n"
        "- оборудованная кухня и стиральная машина\n"
        "- Smart TV, быстрый Wi‑Fi, кондиционер"
    ),
]
_DESCRIPTIONS_EN: list[str] = [
    f"Apartment #{n} in Batumi. Price, layout, and amenities — see the Airbnb listing."
    for n in range(1, 17)
]

AIRBNB_LISTINGS: list[dict[str, Any]] = [
    {
        "url": url,
        # Несколько URL: слайдер «◀ фото ▶» в боте (например 2–3 снимка с объявления).
        "images": [img],
        "description_ru": dru,
        "description_en": den,
    }
    for (url, img), dru, den in zip(_AIRBNB_PAIRS, _DESCRIPTIONS_RU, _DESCRIPTIONS_EN)
]

# Пример: три фотографии у одного объекта — расширьте список images (URL с Airbnb / muscache):
# Часто проще взять ссылки с HTML листинга командой (до 10 уникальных снимков):
#   python -m airbnb_photos "https://www.airbnb.ru/rooms/ВАШ_ID"
# и вставить вывод в "images": [ ... ].
# AIRBNB_LISTINGS[0]["images"] = [
#     AIRBNB_LISTINGS[0]["images"][0],
#     "https://a0.muscache.com/im/pictures/.../второе.jpeg?im_w=1200",
#     "https://a0.muscache.com/im/pictures/.../третье.jpeg?im_w=1200",
# ]


def _normalize_listing_images(item: dict[str, Any]) -> list[str]:
    """Список URL картинок из ключа images или устаревшего image."""
    raw = item.get("images")
    if isinstance(raw, list) and raw:
        out = [str(u).strip() for u in raw if str(u).strip()]
    elif item.get("image"):
        out = [str(item["image"]).strip()]
    else:
        out = []
    # без дубликатов, порядок сохраняем
    seen: set[str] = set()
    uniq: list[str] = []
    for u in out:
        if u not in seen:
            seen.add(u)
            uniq.append(u)
    return uniq[:10]


async def _ensure_room_columns(db: aiosqlite.Connection) -> None:
    """Добавляем listing_url / images_json для старых баз."""
    async with db.execute("PRAGMA table_info(rooms)") as cur:
        cols = {row[1] for row in await cur.fetchall()}
    if "listing_url" not in cols:
        await db.execute("ALTER TABLE rooms ADD COLUMN listing_url TEXT")
    if "images_json" not in cols:
        await db.execute("ALTER TABLE rooms ADD COLUMN images_json TEXT")


async def _ensure_review_columns(db: aiosqlite.Connection) -> None:
    """Модерация отзывов: approved=1 видны гостям; старые строки без колонки считаем одобренными."""
    async with db.execute("PRAGMA table_info(reviews)") as cur:
        cols = {row[1] for row in await cur.fetchall()}
    if "approved" not in cols:
        await db.execute("ALTER TABLE reviews ADD COLUMN approved INTEGER")
        await db.execute("UPDATE reviews SET approved = 1 WHERE approved IS NULL")
        await db.commit()


async def _replace_rooms_with_airbnb(db: aiosqlite.Connection) -> None:
    """Полностью пересобирает таблицу rooms из AIRBNB_LISTINGS."""
    await db.execute("DELETE FROM rooms")
    await db.execute("DELETE FROM sqlite_sequence WHERE name = 'rooms'")

    placeholder_price = 50

    rows: list[tuple[Any, ...]] = []
    for i, item in enumerate(AIRBNB_LISTINGS, start=1):
        imgs = _normalize_listing_images(item)
        if not imgs:
            raise ValueError(f"AIRBNB_LISTINGS[{i - 1}]: нужен хотя бы один URL в images")
        desc_ru = str(item.get("description_ru") or "").strip()
        desc_en = str(item.get("description_en") or "").strip()
        if not desc_ru:
            desc_ru = (
                f"Апартаменты №{i} в Батуми. Актуальная цена и даты — на Airbnb "
                "(кнопка «Проверить даты»)."
            )
        if not desc_en:
            desc_en = (
                f"Apartment #{i} in Batumi. Live price and dates on Airbnb "
                '(button "Check dates").'
            )
        listing_url = str(item["url"]).strip()
        images_blob = json.dumps(imgs, ensure_ascii=False)
        rows.append(
            (
                f"Апартаменты №{i} · Airbnb",
                f"Apartment #{i} · Airbnb",
                desc_ru,
                desc_en,
                placeholder_price,
                imgs[0],
                images_blob,
                listing_url,
            )
        )

    await db.executemany(
        """
        INSERT INTO rooms (
            title_ru, title_en, description_ru, description_en,
            price_per_night, image_url, images_json, listing_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


async def init_db() -> None:
    """
    Создаёт таблицы, мигрирует схему и синхронизирует каталог с AIRBNB_LISTINGS
    при первом запуске после обновления (user_version < _CATALOG_DB_VERSION).
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(
            """
            PRAGMA journal_mode = WAL;

            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                lang TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                rating INTEGER NOT NULL,
                text TEXT NOT NULL,
                photo_file_id TEXT,
                approved INTEGER NOT NULL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title_ru TEXT NOT NULL,
                title_en TEXT NOT NULL,
                description_ru TEXT NOT NULL,
                description_en TEXT NOT NULL,
                price_per_night INTEGER NOT NULL,
                image_url TEXT NOT NULL
            );

            -- События для ограничения частоты (сейчас используется для поддержки).
            CREATE TABLE IF NOT EXISTS rate_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                kind TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_rate_events_user_kind
            ON rate_events (telegram_id, kind, created_at);
            """
        )

        await _ensure_room_columns(db)
        await _ensure_review_columns(db)

        async with db.execute("PRAGMA user_version") as cur:
            row = await cur.fetchone()
        user_ver = int(row[0]) if row else 0

        async with db.execute("SELECT COUNT(*) FROM rooms") as cur:
            room_count = int((await cur.fetchone())[0])

        if user_ver < _CATALOG_DB_VERSION or room_count == 0:
            await _replace_rooms_with_airbnb(db)
            await db.execute(f"PRAGMA user_version = {_CATALOG_DB_VERSION}")

        await db.commit()


async def reload_airbnb_catalog() -> None:
    """
    Принудительная перезаливка каталога из AIRBNB_LISTINGS (после правки списка в коде).
    Пользователи, отзывы и rate_limits не затрагиваются.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await _ensure_room_columns(db)
        await _replace_rooms_with_airbnb(db)
        await db.execute(f"PRAGMA user_version = {_CATALOG_DB_VERSION}")
        await db.commit()


async def ensure_user(
    db: aiosqlite.Connection,
    telegram_id: int,
    username: Optional[str],
    first_name: Optional[str],
) -> None:
    """Создаёт пользователя или обновляет имя/username (язык не трогаем)."""
    await db.execute(
        """
        INSERT INTO users (telegram_id, username, first_name)
        VALUES (?, ?, ?)
        ON CONFLICT(telegram_id) DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name
        """,
        (telegram_id, username, first_name),
    )
    await db.commit()


async def get_user_lang(db: aiosqlite.Connection, telegram_id: int) -> Optional[str]:
    """Возвращает 'ru', 'en' или None, если язык ещё не выбран."""
    async with db.execute("SELECT lang FROM users WHERE telegram_id = ?", (telegram_id,)) as cur:
        row = await cur.fetchone()
    if not row:
        return None
    return row[0]


async def set_user_lang(db: aiosqlite.Connection, telegram_id: int, lang: str) -> None:
    """Сохраняет код языка ('ru' или 'en')."""
    await db.execute(
        "UPDATE users SET lang = ? WHERE telegram_id = ?",
        (lang, telegram_id),
    )
    await db.commit()


async def fetch_rooms(db: aiosqlite.Connection) -> list[dict[str, Any]]:
    """Все номера по возрастанию id — для карточек в боте. Поле images — список URL галереи."""
    db.row_factory = aiosqlite.Row
    async with db.execute(
        """
        SELECT id, title_ru, title_en, description_ru, description_en,
               price_per_night, image_url, images_json, listing_url
        FROM rooms
        ORDER BY id
        """
    ) as cur:
        rows = await cur.fetchall()

    out: list[dict[str, Any]] = []
    for r in rows:
        d = dict(r)
        imgs: list[str] = []
        raw = d.get("images_json")
        if raw:
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    imgs = [str(u).strip() for u in parsed if str(u).strip()]
            except json.JSONDecodeError:
                imgs = []
        if not imgs and d.get("image_url"):
            imgs = [str(d["image_url"])]
        d["images"] = imgs[:10]
        out.append(d)
    return out


async def insert_review(
    db: aiosqlite.Connection,
    telegram_id: int,
    rating: int,
    text: str,
    photo_file_id: Optional[str],
    *,
    approved: int,
) -> int:
    """Сохраняет отзыв гостя. approved=1 — сразу в ленте; 0 — ждёт модерации. Возвращает id записи."""
    cur = await db.execute(
        """
        INSERT INTO reviews (telegram_id, rating, text, photo_file_id, approved)
        VALUES (?, ?, ?, ?, ?)
        """,
        (telegram_id, rating, text, photo_file_id, approved),
    )
    await db.commit()
    return int(cur.lastrowid)


async def approve_review(db: aiosqlite.Connection, review_id: int) -> bool:
    """Одобрить отзыв для показа гостям. False — не найден или уже одобрен."""
    async with db.execute(
        "SELECT COALESCE(approved, 0) FROM reviews WHERE id = ?",
        (review_id,),
    ) as cur:
        row = await cur.fetchone()
    if not row:
        return False
    if int(row[0]) == 1:
        return False
    await db.execute(
        "UPDATE reviews SET approved = 1 WHERE id = ?",
        (review_id,),
    )
    await db.commit()
    return True


async def fetch_recent_reviews(
    db: aiosqlite.Connection,
    *,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Последние отзывы (новые сверху) с именем гостя из users.first_name, если есть.
    """
    db.row_factory = aiosqlite.Row
    lim = max(1, min(int(limit), 50))
    async with db.execute(
        """
        SELECT r.rating, r.text, r.photo_file_id, r.created_at,
               u.first_name AS guest_name
        FROM reviews r
        LEFT JOIN users u ON u.telegram_id = r.telegram_id
        WHERE COALESCE(r.approved, 0) = 1
        ORDER BY r.id DESC
        LIMIT ?
        """,
        (lim,),
    ) as cur:
        rows = await cur.fetchall()
    return [dict(row) for row in rows]


def _parse_sqlite_datetime(value: str) -> datetime:
    """SQLite CURRENT_TIMESTAMP в виде 'YYYY-MM-DD HH:MM:SS' — считаем UTC."""
    value = value.strip()
    if "T" in value:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        dt = datetime.strptime(value[:19], "%Y-%m-%d %H:%M:%S")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


async def review_cooldown_seconds_left(
    db: aiosqlite.Connection,
    telegram_id: int,
    cooldown_seconds: int,
) -> int:
    """
    Сколько секунд ждать до следующего отзыва (0 — можно отправлять).
    Опирается на время последней записи в таблице reviews.
    """
    if cooldown_seconds <= 0:
        return 0
    async with db.execute(
        """
        SELECT created_at FROM reviews
        WHERE telegram_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (telegram_id,),
    ) as cur:
        row = await cur.fetchone()
    if not row:
        return 0
    last_at = _parse_sqlite_datetime(row[0])
    elapsed = (datetime.now(timezone.utc) - last_at).total_seconds()
    if elapsed >= cooldown_seconds:
        return 0
    return max(1, int(math.ceil(cooldown_seconds - elapsed)))


async def count_support_events_in_window(
    db: aiosqlite.Connection,
    telegram_id: int,
    window_seconds: int,
) -> int:
    """Сколько обращений в поддержку уже записано за последние window_seconds секунд."""
    if window_seconds <= 0:
        return 0
    async with db.execute(
        f"""
        SELECT COUNT(*) FROM rate_events
        WHERE telegram_id = ?
          AND kind = 'support'
          AND datetime(created_at) > datetime('now', '-{int(window_seconds)} seconds')
        """,
        (telegram_id,),
    ) as cur:
        row = await cur.fetchone()
    return int(row[0]) if row else 0


async def record_support_rate_event(
    db: aiosqlite.Connection,
    telegram_id: int,
) -> None:
    """Фиксируем успешную отправку в поддержку (для лимита сообщений)."""
    await db.execute(
        "INSERT INTO rate_events (telegram_id, kind) VALUES (?, 'support')",
        (telegram_id,),
    )
    await db.commit()
