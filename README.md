# Anycast Control Panel

Полноценная система управления "Anycast без BGP" с современным веб-интерфейсом и backend на FastAPI.

## Возможности
- Аутентификация с JWT и поддержкой refresh токенов
- Управление Entry Points: автоматическая установка через SSH, WireGuard mesh, HAProxy и nftables
- Мастер создания маршрутов с поддержкой SRV/A записей и продвинутых настроек балансировки
- Real-time мониторинг (WebSocket, Celery задачи, Redis)
- Аналитика трафика, отчёты, алерты и DDoS-дэшборд
- Настройки профиля, тарифов, интеграций и командного доступа
- Docker инфраструктура с PostgreSQL, Redis и Celery worker

## Структура проекта
```
backend/        # FastAPI + Celery + SQLAlchemy
frontend/       # Dockerfile для отдачи статических файлов панели
public/         # HTML/CSS/JS интерфейс без сборщиков
```

## Быстрый старт
1. Создайте файл `.env` в корне:
   ```env
   ANYCAST_SECRET_KEY=change_me
   ANYCAST_DATABASE_URL=postgresql+psycopg2://anycast:anycast@postgres:5432/anycast
   ANYCAST_REDIS_URL=redis://redis:6379/0
   ```
2. Запустите стек:
   ```bash
   docker compose up --build
   ```
3. Панель будет доступна на `http://localhost:3000`, API — на `http://localhost:8000`.

## Backend
- FastAPI маршруты соответствуют требованиям: `/api/auth`, `/api/entry-points`, `/api/routes`, `/api/stats`, `/api/alerts`, `/api/settings`, `/api/admin`
- Celery задачи: установка нод, распространение конфигов, сбор метрик, мониторинг здоровья, очистка статистики
- PostgreSQL используется для хранения данных, Redis — для брокера и кэша

## Frontend
- Адаптивный интерфейс с темой по умолчанию (dark), поддержкой переключения и PWA подсказками
- Компоненты для дашборда, таблиц нод/маршрутов, мастера маршрутов, мониторинга, аналитики и документации
- Используются Tailwind-подобные приёмы, градиенты и lucide-иконки (через CDN), Chart.js для графиков

## Дополнительно
- Health-check endpoint: `/healthz`
- Dockerfile для backend и frontend
- Готовая конфигурация docker-compose для локального или production деплоя
