# Anycast Control Panel

Рабочая панель управления персональной anycast-сетью: FastAPI backend + статичный, но насыщенный UI без заглушек.

## Возможности
- Регистрация и вход с валидацией пароля, JWT хранится в браузере
- CRUD по entry point нодам (название, IP, локация, статус)
- CRUD по маршрутам c привязкой к выбранным entry points и выбором протоколов
- Проверка форматов IP/поддоменов на сервере
- Postgres (или SQLite по умолчанию) через SQLAlchemy
- Docker-compose для запуска API, Postgres и фронтенда
- Показатели в реальном времени на дашборде (кол-во нод, маршрутов, UDP/TCP+HAProxy)
- Градиентный тёмный интерфейс с overlay-спиннером и toasts

## Структура проекта
```
backend/        # FastAPI, SQLAlchemy, JWT
frontend/       # Dockerfile для nginx
public/         # HTML/CSS/JS без сборщиков
```

## Быстрый старт
1. Создайте `.env` с параметрами подключения:
   ```env
   ANYCAST_SECRET_KEY=change_me
   ANYCAST_DATABASE_URL=postgresql+psycopg2://anycast:anycast@postgres:5432/anycast
   ```
   (при отсутствии переменной база будет создана в `backend/app/anycast.db`)
2. Поднимите сервисы:
   ```bash
   docker compose up --build
   ```
3. Откройте `http://localhost:3000` — зарегистрируйте пользователя и работайте с реальными данными.

## API
- `POST /api/auth/register` — создать пользователя
- `POST /api/auth/login` — получить JWT
- `GET /api/auth/me` — информация о текущем пользователе
- `GET/POST/PUT/DELETE /api/entry-points` — управление entry points
- `GET/POST/PUT/DELETE /api/routes` — управление маршрутами

## Полезное
- Health-check: `GET /healthz`
- Все запросы, кроме регистрации/логина, требуют `Authorization: Bearer <token>`
- Фронтенд обращается к API только после успешной аутентификации — фиктивных данных нет
