FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN SECRET_KEY=build-dummy DB_NAME=x DB_USER=x DB_PASS=x DB_HOST=x DB_PORT=5432 python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "stoc_project.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "1", "--timeout", "60"]
