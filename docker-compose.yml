version: '3.9'

services:
  db:
    image: postgres:16-alpine
    container_name: cloudvault_db
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-cloudvault}
      POSTGRES_USER: ${POSTGRES_USER:-cloudvault}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-cloudvault_secret}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-cloudvault}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: cloudvault_redis
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD:-cloudvault_redis}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD:-cloudvault_redis}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  minio:
    image: minio/minio:latest
    container_name: cloudvault_minio
    restart: unless-stopped
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER:-cloudvault_minio}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD:-cloudvault_minio_secret}
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"
      - "9001:9001"
    healthcheck:
      test: ["CMD", "mc", "ready", "local"]
      interval: 10s
      timeout: 5s
      retries: 5

  minio-init:
    image: minio/mc:latest
    container_name: cloudvault_minio_init
    depends_on:
      minio:
        condition: service_healthy
    entrypoint: >
      /bin/sh -c "
      mc alias set myminio http://minio:9000 ${MINIO_ROOT_USER:-cloudvault_minio} ${MINIO_ROOT_PASSWORD:-cloudvault_minio_secret};
      mc mb myminio/${MINIO_BUCKET_NAME:-cloudvault-files} --ignore-existing;
      mc mb myminio/${MINIO_BUCKET_NAME:-cloudvault-files}-versions --ignore-existing;
      mc mb myminio/${MINIO_BUCKET_NAME:-cloudvault-files}-thumbnails --ignore-existing;
      exit 0;
      "

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: cloudvault_backend
    restart: unless-stopped
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.dev
    env_file:
      - .env
    volumes:
      - ./backend:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      minio:
        condition: service_healthy
    command: >
      sh -c "python manage.py migrate --noinput &&
             python manage.py collectstatic --noinput &&
             gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 --threads 2 --timeout 120"

  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: cloudvault_celery_worker
    restart: unless-stopped
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.dev
    env_file:
      - .env
    volumes:
      - ./backend:/app
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      minio:
        condition: service_healthy
    command: celery -A config worker -l info --concurrency=4

  celery_beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: cloudvault_celery_beat
    restart: unless-stopped
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.dev
    env_file:
      - .env
    volumes:
      - ./backend:/app
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: cloudvault_frontend
    restart: unless-stopped
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=${REACT_APP_API_URL:-http://localhost:8000/api}
    depends_on:
      - backend

  nginx:
    image: nginx:alpine
    container_name: cloudvault_nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - static_volume:/app/staticfiles:ro
      - media_volume:/app/media:ro
    depends_on:
      - backend
      - frontend

volumes:
  postgres_data:
  redis_data:
  minio_data:
  static_volume:
  media_volume:
