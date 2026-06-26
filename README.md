# batumiarenda

Telegram-бот для апартаментов в Батуми (aiogram 3, SQLite).

## Локальный запуск

```bash
cd telegram_hotel_bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # или создайте .env вручную
python main.py
```

Переменные окружения: `BOT_TOKEN` (обяз.), `ADMIN_IDS`, опционально `BOOKING_BASE_URL`, `DB_PATH`.

## Railway

1. **New Project** → Deploy from GitHub/GitLab → репозиторий `batumiarenda`.
2. Сборка идёт через **Dockerfile** в корне (код в `telegram_hotel_bot/`).
3. **Variables:** `BOT_TOKEN`, `ADMIN_IDS` (и при необходимости остальное).
4. **Volume:** mount path `/data`, переменная `DB_PATH=/data/hotel_bot.db` (чтобы отзывы не пропадали при redeploy).
5. Остановите локальный `python main.py`, если бот уже запущен с тем же токеном.

Альтернатива без Docker: **Settings → Root Directory** = `telegram_hotel_bot`, тогда Railway увидит `requirements.txt` и `railway.toml` внутри папки.
