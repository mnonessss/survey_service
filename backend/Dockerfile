FROM python:3.12-slim

WORKDIR /app

COPY requirements.prod.txt .
RUN pip install --no-cache-dir -r requirements.prod.txt

COPY backend/ /app/backend/
COPY alembic /app/alembic/
COPY alembic.ini /app/alembic.ini

WORKDIR /app/backend
ENV PYTHONPATH=/app/backend

CMD ["sh", "-c", "cd /app && alembic -c alembic.ini upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
