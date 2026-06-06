# Survey Platform (практика VK)

Платформа опросов: личный кабинет, публичные ссылки, ответы, экспорт XLS, API для интеграций.

## Быстрый старт (локально)

```bash
docker compose up -d --build
docker compose exec backend alembic -c /app/alembic.ini upgrade head  # если миграции не применились
cd frontend && npm install && npm run dev
```

- API: http://localhost:8000/docs  
- UI: http://localhost:3000  

## Деплой на VPS

См. **[docs/DEPLOY.md](docs/DEPLOY.md)**.

## Структура API

| Группа | Префикс |
|--------|---------|
| Личный кабинет | `/surveys` |
| Публичное прохождение | `/public` |
| Внешние системы | `/api/v1/external` |
