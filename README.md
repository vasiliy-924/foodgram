[![Main Foodgram workflow](https://github.com/vasiliy-924/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/vasiliy-924/foodgram/actions/workflows/main.yml)

## Foodgram 🍕🍳🥩 — «Продуктовый помощник»

Foodgram — сервис публикации рецептов. Пользователи могут создавать рецепты,
подписываться на авторов, добавлять рецепты в избранное и список покупок,
скачивать список покупок файлом, искать ингредиенты и фильтровать рецепты по тегам.

- Прод: [thunderfoodgram.hopto.org](https://thunderfoodgram.hopto.org)
- Документация API: [thunderfoodgram.hopto.org/api/docs/](https://thunderfoodgram.hopto.org/api/docs/)

## Основные возможности
- **Аутентификация по токену**: выдача/удаление токена
  - POST `/api/auth/token/login/`, POST `/api/auth/token/logout/`
- **Пользователи и профиль**: список, профиль, «Я», аватар, подписки
  - GET `/api/users/`, GET `/api/users/{id}/`, GET `/api/users/me/`
  - PUT `/api/users/me/avatar/`, GET `/api/users/subscriptions/`
  - POST/DELETE `/api/users/{id}/subscribe/`
- **Ингредиенты**: поиск по префиксу названия
  - GET `/api/ingredients/?name=мо`
- **Теги**: список и детальная информация
  - GET `/api/tags/`, GET `/api/tags/{id}/`
- **Рецепты**: список/детально, фильтры, CRUD (для автора),
  избранное, список покупок, выгрузка покупок
  - GET/POST `/api/recipes/`, GET/PATCH/DELETE `/api/recipes/{id}/`
  - POST/DELETE `/api/recipes/{id}/favorite/`
  - POST/DELETE `/api/recipes/{id}/shopping_cart/`
  - GET `/api/recipes/download_shopping_cart/` (txt-файл)

Полная спецификация OpenAPI — в `docs/openapi-schema.yml` и
[на проде](https://thunderfoodgram.hopto.org/api/docs/).

## Стек
- **Backend**: Python 3.12, Django, Django REST Framework, django-filter,
  Gunicorn, PostgreSQL
- **Frontend**: React (SPA, предсобранный билд)
- **Infra/CI/CD**: Docker, Docker Compose, Nginx, GitHub Actions

## Конфигурация окружения (.env)
Пример переменных (для прод/CI):

```
SECRET_KEY=your_django_secret
ALLOWED_HOSTS=localhost,127.0.0.1,thunderfoodgram.hopto.org

# Использовать SQLite локально (True/False)
DJANGO_USE_SQLITE=False
DJANGO_DEBUG=False

# Postgres
POSTGRES_DB=django_db
POSTGRES_USER=django_user
POSTGRES_PASSWORD=django_password
DB_HOST=db
DB_PORT=5432
```

Для локальной разработки можно выставить `DJANGO_USE_SQLITE=True` и опустить
переменные Postgres.

## Запуск локально (Docker Compose)

```
docker compose -f infra/docker-compose.yml up --build
```

- Приложение: http://localhost
- Документация API: http://localhost/api/docs/

## Продакшен (Docker Compose)
В проде используется `infra/docker-compose.production.yml` (сервисы: db,
backend, frontend, nginx). Образы публикуются в Docker Hub, затем
контейнеры поднимаются на сервере.

Ручной деплой на сервере:
```
cd ~/foodgram
sudo docker compose -f infra/docker-compose.production.yml pull
sudo docker compose -f infra/docker-compose.production.yml up -d
```

## Наполнение тестовыми данными
В контейнер `backend` смонтирован каталог `data/` как `/data`. Есть две
команды (идемпотентны):

1) Полное наполнение тестовыми данными (пользователи, теги, рецепты,
   ингредиенты, связи, картинки):
```
sudo docker compose -f infra/docker-compose.production.yml \
  exec -T backend python manage.py seed_demo | cat
```

2) Импорт только ингредиентов (из `ingredients.json` или `ingredients.csv`):
```
sudo docker compose -f infra/docker-compose.production.yml \
  exec -T backend python manage.py import_ingredients | cat
```

Если на сервере нет каталога `~/foodgram/data`, скопируйте его из репозитория
и повторно выполните команду.

## CI/CD
Workflow: `.github/workflows/main.yml`.
Выполняет:
- тесты бекенда;
- сборку и публикацию образов `backend`, `frontend`, `nginx` в Docker Hub;
- деплой на сервер по SSH (копирование compose и запуск);
- уведомление в Telegram.

Секреты репозитория (GitHub → Settings → Secrets and variables → Actions):
- `DOCKER_USERNAME`, `DOCKER_PASSWORD`
- `HOST`, `USER`, `SSH_KEY`, `SSH_PASSPHRASE`
- `TELEGRAM_TO`, `TELEGRAM_TOKEN`

## Автор
**Василий Петров** - [GitHub https://github.com/vasiliy-924](https://github.com/vasiliy-924)