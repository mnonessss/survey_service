# Деплой Survey Platform на VPS

Backend (FastAPI), frontend (React), Postgres, Redis, nginx.

## Что реализовано

| Требование | Реализация |
|------------|------------|
| Личный кабинет: CRUD опросов | `/surveys`, React UI |
| Типы вопросов | `QuestionType` + CRUD `/surveys/{id}/questions` |
| Уникальные ссылки без регистрации | `secrets.token_urlsafe(48)`, `/public/surveys/{token}` |
| Прохождение опроса и ответы | `response_sessions`, `answers`, `/public/.../submit` |
| Выгрузка XLS | `GET /surveys/{id}/export.xlsx` |
| Черновики | Redis `draft:{session_id}`, `PUT /public/sessions/{id}/draft` |
| API для внешних систем | `/api/v1/external/*` |
| XSS | `html.escape` на ответах, CSP заголовки |
| IDOR на ссылках | криптостойкий токен, не UUID |
| Security Gate | `.gitlab-ci.yml` с шаблоном SAST |

---

## 1. Подготовка VPS

```bash
sudo apt update && sudo apt install -y docker.io docker-compose-plugin git
sudo usermod -aG docker $USER
```

Откройте порты **80** (и **443** при настройке TLS).

---

## 2. Настройка `.env`

```bash
cp .env.example .env
nano .env
```

Обязательно задайте:

- `POSTGRES_PASSWORD`
- `PUBLIC_APP_URL`, `API_PUBLIC_URL`, `CORS_ORIGINS`

---

## 3. Запуск

```bash
git clone <ваш-репозиторий> survey_platform
cd survey_platform
cp .env.example .env
# заполните .env

docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec backend alembic -c /app/alembic.ini upgrade head
```

Проверка: `curl http://ВАШ_IP/health`

---

## 4. Security Gate (GitLab)

Файл `.gitlab-ci.yml` подключает `Security/SAST.gitlab-ci.yml`.
Залейте код в GitLab VK / включите Security Gate в проекте и исправьте findings.

---

## 5. Локальная разработка

```bash
docker compose up -d
cd frontend && npm install && npm run dev
```

---

## 6. Чеклист перед сдачей

- [ ] `alembic -c /app/alembic.ini upgrade head` выполнен
- [ ] Создан опрос → вопросы → ссылка → прохождение → XLS
- [ ] Security Gate пройден / замечания задокументированы
