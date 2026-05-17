<div align="center">

# CloudVault

**Комплексная облачная платформа для хранения, обмена и совместной работы с файлами — личный Google Drive / Dropbox под вашим контролем.**

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.x-092E20?style=flat&logo=django&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat&logo=redis&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-5-37814A?style=flat&logo=celery&logoColor=white)
![MinIO](https://img.shields.io/badge/MinIO-S3-C72E49?style=flat&logo=minio&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-Reverse_Proxy-009639?style=flat&logo=nginx&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

</div>

---

## Содержание

1. [О проекте](#1-о-проекте)
2. [Ключевые возможности](#2-ключевые-возможности)
3. [Технологический стек](#3-технологический-стек)
4. [Структура репозитория](#4-структура-репозитория)
5. [Архитектура и как это работает](#5-архитектура-и-как-это-работает)
6. [Доменная модель (крупными блоками)](#6-доменная-модель-крупными-блоками)
7. [Сервисы в Docker Compose](#7-сервисы-в-docker-compose)
8. [Быстрый старт (локально, Docker)](#8-быстрый-старт-локально-docker)
9. [Основные команды Makefile](#9-основные-команды-makefile)
10. [Ручной запуск frontend и backend](#10-ручной-запуск-frontend-и-backend)
11. [Конфигурация и переменные окружения](#11-конфигурация-и-переменные-окружения)
12. [API, очереди и интеграции](#12-api-очереди-и-интеграции)
13. [Мониторинг и эксплуатация](#13-мониторинг-и-эксплуатация)
14. [CI/CD](#14-cicd)
15. [Безопасность и хранение файлов](#15-безопасность-и-хранение-файлов)
16. [Роли компонентов в продакшене](#16-роли-компонентов-в-продакшене)
17. [Лицензия](#17-лицензия)
18. [Поддержка](#18-поддержка)

---

## 1. О проекте

**CloudVault** — это **продуктовая облачная SaaS-платформа** для хранения, организации и совместной работы с файлами: загрузка, версии, шаринг, корзина, поиск, квоты и аудит — всё в одном окне. Система рассчитана на конечных пользователей (веб-интерфейс), команды (workspace + sharing) и интеграторов (REST API), с возможностью эксплуатации в Docker — от локальной разработки до production.

### Что это за тип системы

По архитектуре CloudVault — **многосервисная распределённая платформа** (не монолит «в одном процессе»):

| Аспект | Описание |
|--------|----------|
| **Продукт** | B2C/B2B-сервис хранения файлов с квотами, шарингом, версионированием и аудитом |
| **Архитектура** | Многосервисная: Django API, React SPA, Celery workers, MinIO Object Storage |
| **Хранилище** | PostgreSQL (метаданные) + MinIO/S3 (бинарные файлы) + Redis (кэш и брокер) |
| **Доставка** | Nginx как единая точка входа (reverse proxy для frontend и API) |
| **Очереди** | Celery + Redis — фоновые задачи: превью, миниатюры, очистка корзины, рассылки |
| **Эксплуатация** | Полный Docker Compose stack — `up` и всё работает |

### Для кого

- **Частные пользователи** — личное облако для документов, фото, видео без лимитов корпоративных сервисов.
- **Небольшие команды** — общие папки, шаринг по ссылке с правами, аудит активности.
- **Разработчики и интеграторы** — REST API + JWT для встраивания файлового хранилища в свои продукты.
- **Self-hosting энтузиасты** — развёртывание на собственной инфраструктуре с полным контролем над данными.

---

## 2. Ключевые возможности

### Управление файлами
- **Загрузка**: одиночная и множественная, drag-and-drop, прогресс-бар, отмена.
- **Скачивание**: прямые ссылки через MinIO presigned URLs (минуя backend).
- **Превью в браузере**: изображения, PDF, видео, аудио, текст — без скачивания.
- **Переименование, перемещение, копирование** между папками.
- **Версионирование**: автоматическое сохранение версий при перезаписи, откат к любой версии.

### Управление папками
- **Иерархия любой вложенности** с breadcrumbs-навигацией.
- **Массовые операции**: выделение нескольких объектов, групповое перемещение/удаление.
- **Drag-and-drop** между папками в дереве.

### Шаринг и совместная работа
- **Публичные ссылки** с настройкой прав (просмотр / скачивание / редактирование).
- **Время жизни ссылки**: одноразовая, по дате, бессрочная.
- **Пароль на ссылку** для приватного обмена.
- **Шаринг конкретному пользователю** по email с уведомлением.
- **Раздел «Поделились со мной»** — все файлы, к которым вам дали доступ.

### Корзина и восстановление
- **Soft-delete** с хранением 30 дней.
- **Восстановление** в исходную папку или в корень.
- **Окончательное удаление** вручную или автоматически после истечения срока.

### Поиск и навигация
- **Полнотекстовый поиск** по именам, расширениям, метаданным, тегам.
- **Фильтры**: тип файла, дата, владелец, размер.
- **Сортировка** по любому полю.

### Безопасность и контроль
- **JWT-аутентификация** (access + refresh токены, ротация).
- **Квоты на пользователя** с трекингом использования в реальном времени.
- **Журнал активности** — полный аудит всех операций (кто, что, когда).
- **Уведомления** о действиях (шаринг, истечение ссылок, заполнение квоты).

### Производительность
- **Асинхронные задачи** (Celery): превью, миниатюры, очистка корзины, нотификации.
- **Кеширование** часто запрашиваемых данных (Redis).
- **Прямой upload/download** в MinIO через presigned URLs — backend не пропускает байты файлов через себя.

---

## 3. Технологический стек

### Backend
| Компонент | Технология | Назначение |
|-----------|------------|------------|
| Язык | **Python 3.12+** | Основной язык backend |
| Web-фреймворк | **Django 5.1** | ORM, миграции, admin, auth |
| API | **Django REST Framework 3.15** | REST-эндпоинты, сериализация |
| Auth | **djangorestframework-simplejwt 5.4** | JWT access/refresh |
| Очереди | **Celery 5.4** | Фоновые задачи |
| Планировщик | **django-celery-beat 2.7** | Периодические задачи (cron-стиль) |
| Object Storage SDK | **boto3 1.35** + **django-storages 1.14** | S3/MinIO интеграция |
| Документация API | **drf-spectacular 0.28** | OpenAPI 3.0 / Swagger UI |
| Изображения | **Pillow 11** | Миниатюры, превью |
| Определение MIME | **python-magic 0.4** | Валидация типов файлов |
| WSGI | **Gunicorn 23** | Production-сервер |

### Frontend
| Компонент | Технология |
|-----------|------------|
| Фреймворк | **React 18** |
| State Management | **Redux Toolkit** |
| Сборка | Webpack / CRA |
| HTTP-клиент | Axios |
| Стили | CSS Modules + кастомные темы |

### Инфраструктура
| Компонент | Технология |
|-----------|------------|
| База данных | **PostgreSQL 16** |
| Кеш / брокер | **Redis 7** |
| Object Storage | **MinIO** (S3-совместимое) |
| Reverse Proxy | **Nginx Alpine** |
| Контейнеризация | **Docker + Docker Compose** |

---

## 4. Структура репозитория

```
CloudVault/
├── backend/                      # Django REST API
│   ├── apps/                     # Бизнес-домены (Django apps)
│   │   ├── accounts/             # Пользователи, JWT, профили, квоты
│   │   ├── files/                # Файлы, версии, превью, загрузка
│   │   ├── folders/              # Папки, иерархия, перемещение
│   │   ├── sharing/              # Публичные ссылки, права доступа
│   │   ├── trash/                # Корзина, восстановление
│   │   ├── search/               # Полнотекстовый поиск
│   │   ├── activity/             # Журнал активности и аудит
│   │   ├── notifications/        # Уведомления (in-app, email)
│   │   └── teams/                # Команды и workspaces
│   ├── config/                   # Настройки Django проекта
│   │   ├── settings/             # dev / prod / base разделение
│   │   ├── celery.py             # Конфиг Celery
│   │   ├── urls.py               # Корневой роутинг
│   │   └── wsgi.py               # WSGI entrypoint
│   ├── utils/                    # Общие утилиты
│   │   ├── storage_backend.py    # Кастомный S3/MinIO backend
│   │   ├── pagination.py         # Пагинация для DRF
│   │   └── exceptions.py         # Кастомные исключения
│   ├── manage.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                     # React SPA
│   ├── public/
│   ├── src/
│   │   ├── api/                  # Axios клиенты по доменам
│   │   ├── components/           # UI-компоненты
│   │   ├── pages/                # Страницы (Files, Trash, Shared, Login...)
│   │   ├── hooks/                # Custom React hooks
│   │   ├── store/                # Redux Toolkit slices
│   │   ├── styles/               # CSS / тематика
│   │   └── utils/                # Хелперы
│   └── Dockerfile
│
├── nginx/
│   └── nginx.conf                # Reverse proxy + раздача статики
│
├── docker-compose.yml            # Полный stack: db, redis, minio, backend, celery, frontend, nginx
└── README.md
```

---

## 5. Архитектура и как это работает

CloudVault — это **классическая многоуровневая SaaS-архитектура** с разделением хранения **метаданных** (PostgreSQL) и **бинарных данных** (MinIO/S3). Все запросы проходят через Nginx, который выступает единой точкой входа.

### Схема

```
                           ┌─────────────────┐
                           │     Клиенты     │
                           │  Browser / API  │
                           └────────┬────────┘
                                    │ HTTPS
                                    ▼
                           ┌─────────────────┐
                           │      Nginx      │
                           │   :80 / :443    │
                           │ reverse proxy   │
                           └────┬────────┬───┘
                                │        │
                ┌───────────────┘        └────────────────┐
                ▼                                         ▼
       ┌────────────────┐                       ┌──────────────────┐
       │  React SPA     │                       │   Django API     │
       │  (frontend)    │                       │   (backend)      │
       │   :3000        │                       │   :8000          │
       └────────────────┘                       └────┬──────┬──────┘
                                                     │      │
                            ┌────────────────────────┘      │
                            │                               │
                            ▼                               ▼
                   ┌────────────────┐              ┌────────────────┐
                   │  PostgreSQL    │              │     Redis      │
                   │  метаданные    │              │ cache + broker │
                   │   :5432        │              │    :6379       │
                   └────────────────┘              └────┬───────────┘
                                                       │
                                                       ▼
                                            ┌────────────────────┐
                                            │   Celery Workers   │
                                            │  + Celery Beat     │
                                            │  фоновые задачи    │
                                            └─────────┬──────────┘
                                                      │
                                                      ▼
                                            ┌────────────────────┐
                                            │      MinIO         │
                                            │  S3-совместимое    │
                                            │  хранилище файлов  │
                                            │   :9000 / :9001    │
                                            └────────────────────┘
```

### Поток типичных операций

**Загрузка файла:**
1. Frontend → `POST /api/files/upload/` с multipart-данными.
2. Django валидирует размер, MIME, квоту пользователя.
3. Файл стримом сохраняется в MinIO через `django-storages`.
4. В PostgreSQL пишется метаданные (имя, размер, путь, владелец, версия).
5. Celery-задача генерирует миниатюру/превью в фоне.
6. В журнал активности добавляется запись.

**Скачивание файла:**
1. Frontend → `GET /api/files/{id}/download/`.
2. Django проверяет права доступа.
3. Возвращается **presigned URL MinIO** с TTL.
4. Браузер скачивает файл напрямую из MinIO — backend не нагружается передачей байтов.

**Шаринг по ссылке:**
1. Пользователь создаёт ссылку с параметрами (TTL, пароль, права).
2. Backend генерирует уникальный токен, сохраняет в PostgreSQL.
3. Получатель открывает `/api/s/{token}/` — backend валидирует токен и отдаёт presigned URL.

---

## 6. Доменная модель (крупными блоками)

Бизнес-логика разбита на **Django apps по доменам** (DDD-стиль):

| Домен | Назначение | Ключевые сущности |
|-------|------------|-------------------|
| **accounts** | Пользователи, аутентификация, квоты | `User`, `Profile`, `StorageQuota` |
| **files** | Файлы и их версии | `File`, `FileVersion`, `Thumbnail` |
| **folders** | Иерархия папок | `Folder` (с self-referential parent) |
| **sharing** | Шаринг и публичный доступ | `ShareLink`, `Permission`, `SharedAccess` |
| **trash** | Soft-delete и восстановление | `TrashedItem` |
| **search** | Поиск по контенту и метаданным | (использует PG full-text search) |
| **activity** | Аудит и журнал действий | `ActivityLog` |
| **notifications** | Уведомления пользователю | `Notification` |
| **teams** | Команды и workspaces | `Team`, `Membership` |

Каждый app имеет стандартную Django-структуру: `models.py`, `serializers.py`, `views.py`, `urls.py`, `tasks.py` (Celery), `tests/`.

---

## 7. Сервисы в Docker Compose

Полный production-ready stack из **8 сервисов**, описанных в `docker-compose.yml`:

| Сервис | Образ / Сборка | Порт | Назначение |
|--------|----------------|------|------------|
| `db` | `postgres:16-alpine` | 5432 | Основная БД метаданных |
| `redis` | `redis:7-alpine` | 6379 | Кеш + брокер Celery (с паролем) |
| `minio` | `minio/minio:latest` | 9000 / 9001 | Object storage + Web Console |
| `minio-init` | `minio/mc:latest` | — | Инициализация бакетов при старте |
| `backend` | `./backend/Dockerfile` | 8000 | Django + Gunicorn (4 workers × 2 threads) |
| `celery_worker` | `./backend/Dockerfile` | — | Worker для фоновых задач (concurrency=4) |
| `celery_beat` | `./backend/Dockerfile` | — | Планировщик периодических задач |
| `frontend` | `./frontend/Dockerfile` | 3000 | React dev / build server |
| `nginx` | `nginx:alpine` | 80 / 443 | Reverse proxy + раздача статики |

### Бакеты MinIO

При первом запуске `minio-init` автоматически создаёт три бакета:
- `cloudvault-files` — основные файлы пользователей.
- `cloudvault-files-versions` — исторические версии.
- `cloudvault-files-thumbnails` — миниатюры и превью.

### Healthchecks

Все ключевые сервисы (db, redis, minio) имеют **healthcheck**, и backend стартует только после `service_healthy` — корректный порядок инициализации.

---

## 8. Быстрый старт (локально, Docker)

### Требования

- **Docker 24+** и **Docker Compose v2**
- Минимум **4 GB RAM** свободной памяти
- Свободные порты: `80`, `3000`, `5432`, `6379`, `8000`, `9000`, `9001`

### За 4 шага

```bash
# 1. Клонировать репозиторий
git clone <repository-url>
cd CloudVault

# 2. Скопировать переменные окружения
cp .env.example .env

# 3. Поднять весь stack
docker compose up --build -d

# 4. Создать суперпользователя для админки
docker compose exec backend python manage.py createsuperuser
```

Готово. Открывайте:

| Сервис | URL | Описание |
|--------|-----|----------|
| **Веб-приложение** | <http://localhost> | Основной интерфейс |
| **API** | <http://localhost/api/> | REST API |
| **Swagger UI** | <http://localhost/api/docs/> | Интерактивная документация |
| **Django Admin** | <http://localhost/admin/> | Админ-панель |
| **MinIO Console** | <http://localhost:9001> | Управление хранилищем |

### Остановить / перезапустить

```bash
docker compose stop          # остановить без удаления
docker compose down          # удалить контейнеры
docker compose down -v       # удалить контейнеры + volumes (полный сброс)
docker compose logs -f backend   # смотреть логи backend
```

---

## 9. Основные команды Makefile

> Если в проекте нет Makefile — рекомендуется добавить, чтобы упростить рутину.

| Команда | Назначение |
|---------|------------|
| `make up` | Поднять весь stack |
| `make down` | Остановить и удалить контейнеры |
| `make build` | Пересобрать образы |
| `make logs` | Просмотр логов всех сервисов |
| `make migrate` | Применить миграции Django |
| `make makemigrations` | Создать новые миграции |
| `make shell` | Войти в Django shell |
| `make superuser` | Создать суперпользователя |
| `make test` | Запустить тесты backend |
| `make lint` | Запустить линтер |
| `make celery-logs` | Логи Celery worker |
| `make psql` | Открыть psql внутри контейнера БД |
| `make clean` | Полная очистка (контейнеры + volumes) |

---

## 10. Ручной запуск frontend и backend

Если нужно запустить backend или frontend локально **без Docker** (для отладки):

### Backend (Django)

```bash
cd backend
python -m venv venv
# Linux / macOS:
source venv/bin/activate
# Windows PowerShell:
venv\Scripts\Activate.ps1

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

> При локальном запуске PostgreSQL, Redis и MinIO всё равно удобно держать в Docker — поднимите только их: `docker compose up -d db redis minio`.

### Celery Worker

```bash
cd backend
celery -A config worker -l info --concurrency=4
```

### Celery Beat (планировщик)

```bash
cd backend
celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### Frontend (React)

```bash
cd frontend
npm install
npm start
# Откроется http://localhost:3000
```

---

## 11. Конфигурация и переменные окружения

Все настройки управляются через `.env` файл в корне проекта. Шаблон — в `.env.example`.

### Ключевые группы переменных

#### Django

| Переменная | По умолчанию | Назначение |
|------------|--------------|------------|
| `DJANGO_SECRET_KEY` | — | Секретный ключ (обязательно сменить в prod) |
| `DJANGO_DEBUG` | `True` | Режим отладки (False в prod) |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Разрешённые хосты |
| `DJANGO_SETTINGS_MODULE` | `config.settings.dev` | Какой модуль настроек использовать |

#### PostgreSQL

| Переменная | По умолчанию |
|------------|--------------|
| `POSTGRES_DB` | `cloudvault` |
| `POSTGRES_USER` | `cloudvault` |
| `POSTGRES_PASSWORD` | `cloudvault_secret` |
| `POSTGRES_HOST` | `db` |
| `POSTGRES_PORT` | `5432` |

#### Redis

| Переменная | По умолчанию |
|------------|--------------|
| `REDIS_HOST` | `redis` |
| `REDIS_PORT` | `6379` |
| `REDIS_PASSWORD` | `cloudvault_redis` |

#### MinIO / Object Storage

| Переменная | По умолчанию |
|------------|--------------|
| `MINIO_ROOT_USER` | `cloudvault_minio` |
| `MINIO_ROOT_PASSWORD` | `cloudvault_minio_secret` |
| `MINIO_BUCKET_NAME` | `cloudvault-files` |
| `MINIO_ENDPOINT` | `http://minio:9000` |
| `MINIO_USE_SSL` | `False` |

#### JWT

| Переменная | Назначение |
|------------|------------|
| `JWT_ACCESS_LIFETIME_MIN` | TTL access токена (мин) |
| `JWT_REFRESH_LIFETIME_DAYS` | TTL refresh токена (дни) |

#### Квоты и лимиты

| Переменная | Назначение |
|------------|------------|
| `DEFAULT_USER_QUOTA_MB` | Стартовая квота на пользователя |
| `MAX_UPLOAD_SIZE_MB` | Максимальный размер одного файла |
| `TRASH_RETENTION_DAYS` | Сколько дней хранить в корзине |

#### Frontend

| Переменная | Назначение |
|------------|------------|
| `REACT_APP_API_URL` | URL backend API для фронта |

---

## 12. API, очереди и интеграции

### REST API

Базовый префикс: `/api/`. Аутентификация — JWT через заголовок `Authorization: Bearer <token>`.

#### Аутентификация

| Метод | Endpoint | Описание |
|-------|----------|----------|
| `POST` | `/api/auth/register/` | Регистрация |
| `POST` | `/api/auth/login/` | Логин (выдача access + refresh) |
| `POST` | `/api/auth/refresh/` | Обновление access-токена |
| `GET` | `/api/auth/profile/` | Профиль пользователя |
| `PUT` | `/api/auth/profile/` | Обновление профиля |

#### Файлы

| Метод | Endpoint | Описание |
|-------|----------|----------|
| `GET` | `/api/files/` | Список файлов |
| `POST` | `/api/files/upload/` | Загрузка файла |
| `GET` | `/api/files/{id}/` | Информация о файле |
| `PUT` | `/api/files/{id}/` | Обновление метаданных |
| `DELETE` | `/api/files/{id}/` | Перемещение в корзину |
| `GET` | `/api/files/{id}/download/` | Получение presigned URL |
| `GET` | `/api/files/{id}/preview/` | Превью файла |
| `GET` | `/api/files/{id}/versions/` | Список версий |
| `POST` | `/api/files/{id}/versions/{v}/restore/` | Восстановить версию |

#### Папки

| Метод | Endpoint | Описание |
|-------|----------|----------|
| `GET` | `/api/folders/` | Список папок |
| `POST` | `/api/folders/` | Создать папку |
| `GET` | `/api/folders/{id}/contents/` | Содержимое папки |
| `POST` | `/api/folders/{id}/move/` | Переместить папку |
| `DELETE` | `/api/folders/{id}/` | Удалить папку |

#### Шаринг

| Метод | Endpoint | Описание |
|-------|----------|----------|
| `POST` | `/api/sharing/links/` | Создать публичную ссылку |
| `GET` | `/api/sharing/links/` | Список своих ссылок |
| `DELETE` | `/api/sharing/links/{id}/` | Отозвать ссылку |
| `POST` | `/api/sharing/permissions/` | Поделиться с пользователем |
| `GET` | `/api/sharing/shared-with-me/` | Файлы, к которым дали доступ |
| `GET` | `/api/s/{token}/` | Открыть по публичной ссылке |

#### Корзина

| Метод | Endpoint | Описание |
|-------|----------|----------|
| `GET` | `/api/trash/` | Список удалённого |
| `POST` | `/api/trash/{id}/restore/` | Восстановить |
| `DELETE` | `/api/trash/{id}/` | Удалить окончательно |
| `POST` | `/api/trash/empty/` | Очистить корзину |

#### Поиск

| Метод | Endpoint | Описание |
|-------|----------|----------|
| `GET` | `/api/search/?q=...` | Поиск по файлам и папкам |

> **Интерактивная документация Swagger**: `/api/docs/` (drf-spectacular) — пробовать запросы прямо в браузере.

### Очереди Celery

Фоновые задачи разделены по доменам:

| Задача | Очередь | Триггер |
|--------|---------|---------|
| Генерация миниатюр | `default` | При загрузке изображения |
| Извлечение превью PDF/видео | `media` | При загрузке медиа |
| Очистка просроченной корзины | `maintenance` | Cron (раз в сутки) |
| Удаление истёкших share-links | `maintenance` | Cron (раз в час) |
| Отправка email-уведомлений | `notifications` | По событию |
| Обновление статистики квот | `default` | После загрузки/удаления |

---

## 13. Мониторинг и эксплуатация

### Логи

```bash
docker compose logs -f                       # все сервисы
docker compose logs -f backend               # только backend
docker compose logs -f celery_worker         # только worker
docker compose logs -f --tail=200 nginx      # последние 200 строк nginx
```

### Health-проверки

| Сервис | Команда |
|--------|---------|
| Backend | `curl http://localhost/api/health/` |
| PostgreSQL | `docker compose exec db pg_isready` |
| Redis | `docker compose exec redis redis-cli -a $REDIS_PASSWORD ping` |
| MinIO | `curl http://localhost:9000/minio/health/live` |

### Бэкапы

**PostgreSQL:**
```bash
docker compose exec db pg_dump -U cloudvault cloudvault > backup_$(date +%F).sql
```

**MinIO:** использовать `mc mirror` или snapshot volume `minio_data`.

### Метрики (рекомендации для production)

- **Prometheus + Grafana** для метрик Django/Celery/PostgreSQL.
- **Sentry** для отслеживания исключений в backend и frontend.
- **Loki / ELK** для централизованных логов.

---

## 14. CI/CD

Рекомендуемый pipeline (например, GitHub Actions):

| Этап | Действие |
|------|----------|
| **Lint** | `flake8` / `black --check` для Python, `eslint` для JS |
| **Тесты backend** | `pytest` / `python manage.py test` |
| **Тесты frontend** | `npm test -- --watchAll=false` |
| **Сборка образов** | `docker build` backend + frontend |
| **Push в registry** | DockerHub / GHCR / приватный registry |
| **Deploy** | SSH + `docker compose pull && up -d` или Kubernetes manifests |

### Стратегии деплоя

- **Staging-окружение** на отдельном поддомене перед prod.
- **Blue/green** для zero-downtime обновлений.
- **Миграции БД** запускаются как pre-deploy шаг, обратно совместимые.

---

## 15. Безопасность и хранение файлов

### Аутентификация и авторизация
- **JWT** с коротким TTL access-токена и ротацией refresh-токена.
- **Permission-классы DRF** на каждом endpoint — никаких «глобально открытых» роутов.
- **Object-level permissions**: владелец файла или явно добавленный share-permission.

### Защита данных
- **HTTPS** обязателен в prod (сертификаты в Nginx).
- **Пароли пользователей** хешируются через стандартный `Argon2` / `PBKDF2` (Django default).
- **Пароли на share-link** хешируются перед сохранением.
- **MinIO bucket policies** — закрытый доступ по умолчанию, выдача только через presigned URLs.

### Валидация загрузок
- Проверка **MIME-типа** через `python-magic` (а не только по расширению).
- Лимиты на размер файла и общую квоту пользователя.
- Антивирусная проверка опционально (интеграция с ClamAV).

### Аудит
- Все изменения логируются в `activity.ActivityLog` (актор, действие, объект, IP, timestamp).

---

## 16. Роли компонентов в продакшене

| Компонент | Роль | Масштабирование |
|-----------|------|-----------------|
| **Nginx** | Точка входа, TLS, кеш статики, rate-limiting | Горизонтально (LB сверху) |
| **Django (Gunicorn)** | Бизнес-логика, валидация, авторизация | Горизонтально (несколько контейнеров) |
| **Celery Worker** | Фоновые задачи: превью, нотификации, очистка | Горизонтально (worker pool) |
| **Celery Beat** | Cron-планировщик | Единственный инстанс (lock через БД) |
| **PostgreSQL** | Метаданные, транзакции | Read-replica + connection pool |
| **Redis** | Кеш + брокер очередей | Sentinel / Cluster |
| **MinIO** | Хранилище бинарных файлов | Distributed mode (4+ узла) |
| **Frontend (React)** | SPA, рендеринг UI | CDN для статики |

### Рекомендации для production

- Не использовать **dev-настройки**. `DJANGO_SETTINGS_MODULE=config.settings.prod`.
- Заменить **все дефолтные пароли** (Postgres, Redis, MinIO, `SECRET_KEY`).
- Включить **HTTPS** + `Secure` / `HttpOnly` cookies.
- Настроить **бэкапы** PostgreSQL и MinIO с тестированием восстановления.
- Подключить **мониторинг и алерты** (Sentry, Prometheus).

---

## 17. Лицензия

Проект распространяется под лицензией **MIT**. Подробнее см. [LICENSE](LICENSE).

---

## 18. Поддержка

- **Issues**: открыть issue в репозитории проекта.
- **Discussions**: обсуждения и вопросы — во вкладке Discussions.
- **Pull Requests**: предложения улучшений приветствуются.

### Как помочь проекту

1. Поставьте **star** репозиторию — это мотивирует развивать его дальше.
2. Откройте **issue** с багом или предложением фичи.
3. Сделайте **pull request** — fork → branch → PR в `main`.
4. Поделитесь проектом с теми, кому он может пригодиться.

---

<div align="center">

**Сделано с ♥ для тех, кто хочет своё облако.**

[⬆ Наверх](#cloudvault)

</div>
