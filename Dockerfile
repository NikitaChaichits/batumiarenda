FROM python:3.12-slim

WORKDIR /app

COPY telegram_hotel_bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY telegram_hotel_bot/ .

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
