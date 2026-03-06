FROM python:3.11-slim

WORKDIR /app

# Установка только необходимых системных зависимостей
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements.txt
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование всего проекта
COPY . .

# Сбор статики
RUN python manage.py collectstatic --noinput

# Запуск
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "foodgram.wsgi:application"]