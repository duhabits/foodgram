[![Foodgram workflow](https://github.com/duhabits/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/duhabits/foodgram/actions/workflows/main.yml)

# Foodgram - Продуктовый помощник

Foodgram — это онлайн-сервис и API для публикации рецептов. Пользователи могут создавать рецепты, добавлять их в избранное, формировать список покупок, подписываться на других авторов и скачивать сводный список ингредиентов для выбранных рецептов.

https://foodgram.ddnsking.com/recipes

## Функциональные возможности

### Для всех пользователей:
- Просмотр списка рецептов с пагинацией
- Фильтрация рецептов по тегам
- Просмотр детальной информации о рецепте (ингредиенты, время приготовления, автор)
- Поиск по названию рецепта

### Для авторизованных пользователей:
- Создание, редактирование и удаление своих рецептов
- Добавление рецептов в избранное
- Добавление рецептов в список покупок
- Скачивание списка покупок в текстовом файле
- Подписка на других авторов
- Просмотр ленты подписок
- Смена аватара
- Изменение пароля

### Административная панель:
- Управление пользователями
- Управление рецептами
- Управление тегами и ингредиентами
- Просмотр статистики

## Технологический стек

### Бэкенд
- **Python 3.11** — основной язык программирования
- **Django 4.2** — веб-фреймворк
- **Django REST Framework** — создание API
- **Djoser** — аутентификация и управление пользователями
- **PostgreSQL 15** — реляционная база данных
- **Gunicorn** — WSGI-сервер
- **Pillow** — обработка изображений
- **drf-extra-fields** — дополнительные поля для DRF

### Фронтенд
- **React** — библиотека для UI
- **React Router** — маршрутизация
- **Axios** — HTTP-клиент

### Инфраструктура и DevOps
- **Docker** — контейнеризация
- **Docker Compose** — оркестрация контейнеров
- **Nginx** — веб-сервер и обратный прокси
- **GitHub Actions** — CI/CD
- **Docker Hub** — реестр образов
- **Gunicorn** — WSGI-сервер

### Документация API
- **ReDoc** — интерактивная документация

## API Эндпоинты

Основные эндпоинты API:

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| GET | `/api/recipes/` | Получить список рецептов |
| POST | `/api/recipes/` | Создать новый рецепт |
| GET | `/api/recipes/{id}/` | Получить рецепт по ID |
| PUT/PATCH | `/api/recipes/{id}/` | Обновить рецепт |
| DELETE | `/api/recipes/{id}/` | Удалить рецепт |
| POST | `/api/recipes/{id}/favorite/` | Добавить в избранное |
| DELETE | `/api/recipes/{id}/favorite/` | Удалить из избранного |
| POST | `/api/recipes/{id}/shopping_cart/` | Добавить в корзину |
| DELETE | `/api/recipes/{id}/shopping_cart/` | Удалить из корзины |
| GET | `/api/users/subscriptions/` | Получить подписки |
| POST | `/api/users/{id}/subscribe/` | Подписаться на пользователя |
| PUT/DELETE | `/api/users/me/avatar/` | Управление аватаром |

Полная документация API доступна по адресу: `http://ваш-домен/api/docs/`

## Развертывание проекта

### Предварительные требования

1. Сервер с **Ubuntu 20.04/22.04**
2. Установленные **Docker** и **Docker Compose**
3. Доменное имя (опционально, для production)
4. Аккаунт на **Docker Hub**

### Локальный запуск (для разработки)

1. **Клонируйте репозиторий:**
```bash
git clone https://github.com/duhabits/foodgram.git
cd foodgram
cd infra
touch .env
env:
    # PostgreSQL
    POSTGRES_DB=foodgram
    POSTGRES_USER=foodgram_user
    POSTGRES_PASSWORD=your_password
    DB_NAME=foodgram
    DB_USER=foodgram_user
    DB_PASSWORD=your_password
    DB_HOST=db
    DB_PORT=5432

    # Django
    SECRET_KEY=your_secret_key_here
    DEBUG=False
    ALLOWED_HOSTS=localhost,127.0.0.1,ваш-домен

    # Docker
    DOCKER_USERNAME=hesuo17
docker-compose up -d
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py load_tags
docker-compose exec backend python manage.py load_ingredients --file=data/ingredients.csv
docker-compose exec backend python manage.py collectstatic --noinput

# Загрузка тегов
docker-compose exec backend python manage.py load_tags

# Загрузка ингредиентов из CSV файла
docker-compose exec backend python manage.py load_ingredients --file=data/ingredients.csv

Автор
Андрей Жеребцов
GitHub: @duhabits