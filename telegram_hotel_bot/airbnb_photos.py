"""
Вытаскивание прямых ссылок на фото объявления Airbnb из HTML страницы /rooms/{id}.

В разметке гостевой страницы встречаются URL вида
https://a0.muscache.com/im/pictures/hosting/Hosting-{id}/original/{uuid}.jpeg

Важно: неофициальный разбор HTML — Airbnb может изменить вёрстку.
Соблюдайте правила использования сайта и robots.txt.

Запуск:
  python -m airbnb_photos "https://www.airbnb.ru/rooms/123..."
"""

from __future__ import annotations

import html
import re
import ssl
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def extract_room_id(listing_url: str) -> str | None:
    """Числовой id листинга из пути /rooms/123."""
    m = re.search(r"/rooms/(\d+)", listing_url)
    return m.group(1) if m else None


def _fetch_html(url: str, *, timeout: float, user_agent: str) -> bytes | None:
    """GET страницы; при сбое проверки SSL (часто на macOS без certifi) — повтор без verify."""
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    }
    req = Request(url.strip(), headers=headers, method="GET")
    try:
        with urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except URLError as e:
        err = str(e)
        if "CERTIFICATE_VERIFY_FAILED" not in err and "SSL" not in err:
            return None
    try:
        ctx = ssl._create_unverified_context()
        with urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.read()
    except (HTTPError, URLError, TimeoutError, OSError):
        return None


def fetch_listing_photo_urls(
    listing_url: str,
    *,
    max_photos: int = 10,
    timeout: float = 25.0,
    user_agent: str = DEFAULT_USER_AGENT,
) -> list[str]:
    """
    Загружает страницу объявления и возвращает до max_photos уникальных URL фото
    (каталог Hosting-{room_id} на muscache).
    """
    base_url = listing_url.strip().split("?")[0]
    room_id = extract_room_id(base_url)
    if not room_id:
        return []

    raw = _fetch_html(base_url, timeout=timeout, user_agent=user_agent)
    if not raw:
        return []

    text = html.unescape(raw.decode("utf-8", errors="replace"))
    pattern = re.compile(
        rf"https://a0\.muscache\.com/im/pictures/hosting/Hosting-{room_id}/original/"
        r"[a-f0-9-]+\.jpeg[^\"'\s<>]*",
        re.IGNORECASE,
    )

    seen: set[str] = set()
    out: list[str] = []

    for m in pattern.finditer(text):
        full = m.group(0)
        base_jpeg = full.split("?")[0].split("&amp;")[0]
        fname = base_jpeg.rsplit("/", 1)[-1].lower()
        if fname in seen:
            continue
        seen.add(fname)
        out.append(base_jpeg + "?im_w=1200&quality=80&auto=webp")
        if len(out) >= max_photos:
            break

    return out


def merge_fetched_images(item: dict[str, Any], *, max_photos: int = 10) -> None:
    """
    Для элемента вида {"url": "https://www.airbnb...."} подставляет item["images"]
    списком URL, если загрузка страницы удалась. Иначе ничего не меняет.
    """
    url = item.get("url")
    if not url:
        return
    found = fetch_listing_photo_urls(str(url), max_photos=max_photos)
    if found:
        item["images"] = found


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m airbnb_photos <listing_url>", file=sys.stderr)
        sys.exit(2)
    urls = fetch_listing_photo_urls(sys.argv[1])
    for u in urls:
        print(u)


if __name__ == "__main__":
    main()
