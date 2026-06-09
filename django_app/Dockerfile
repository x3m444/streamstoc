# Multi-stage build — optimized for Ampere ARM64
FROM python:3.11-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY . .

RUN SECRET_KEY=build-dummy DB_NAME=x DB_USER=x DB_PASS=x DB_HOST=x DB_PORT=5432 \
    python manage.py collectstatic --noinput --clear

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request, sys; r=urllib.request.urlopen('http://localhost:8000/health/'); sys.exit(0 if r.status < 500 else 1)"

CMD ["gunicorn", "stoc_project.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-"]
