# CloudVault - Cloud File Storage Platform

A production-grade cloud file storage platform similar to Google Drive and Dropbox, built with Django, React, PostgreSQL, Redis, Celery, and MinIO.

## Features

- **File Management**: Upload, download, rename, move, copy files with drag-and-drop support
- **Folder Management**: Create, rename, move, and delete folders with nested hierarchy
- **File Sharing**: Share files/folders via links with configurable permissions (view, edit, download)
- **Version History**: Automatic file versioning with rollback capability
- **File Preview**: In-browser preview for images, PDFs, text, audio, and video files
- **Trash & Recovery**: Soft delete with 30-day retention and restore functionality
- **Search**: Full-text search across file names, types, and metadata
- **Storage Quotas**: Per-user configurable storage limits with usage tracking
- **Activity Logging**: Complete audit trail of all file operations
- **Authentication**: JWT-based auth with registration, login, and profile management

## Tech Stack

| Component     | Technology                          |
|---------------|-------------------------------------|
| Backend       | Django 5.x + Django REST Framework  |
| Frontend      | React 18 + Redux Toolkit           |
| Database      | PostgreSQL 16                       |
| Cache/Broker  | Redis 7                             |
| Task Queue    | Celery 5                            |
| Object Storage| MinIO (S3-compatible)               |
| Reverse Proxy | Nginx                               |
| Containers    | Docker + Docker Compose             |

## Architecture

```
                    +----------+
                    |  Nginx   |
                    |  :80     |
                    +----+-----+
                         |
              +----------+----------+
              |                     |
        +-----+------+      +------+-----+
        |  React App |      | Django API |
        |  :3000     |      |  :8000     |
        +------------+      +------+-----+
                                   |
                    +--------------+--------------+
                    |              |              |
              +-----+----+  +----+-----+  +-----+-----+
              |PostgreSQL |  |  Redis   |  |   MinIO   |
              |  :5432    |  |  :6379   |  |   :9000   |
              +----------+  +----------+  +-----------+
                                   |
                             +-----+-----+
                             |  Celery   |
                             |  Worker   |
                             +-----------+
```

## Getting Started

### Prerequisites

- Docker and Docker Compose installed
- At least 4GB RAM available for containers

### Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/cloudvault.git
   cd cloudvault
   ```

2. Copy environment file:
   ```bash
   cp .env.example .env
   ```

3. Build and start all services:
   ```bash
   docker-compose up --build -d
   ```

4. Run database migrations:
   ```bash
   docker-compose exec backend python manage.py migrate
   ```

5. Create a superuser:
   ```bash
   docker-compose exec backend python manage.py createsuperuser
   ```

6. Access the application:
   - Frontend: http://localhost
   - API: http://localhost/api/
   - Admin: http://localhost/admin/
   - MinIO Console: http://localhost:9001

### Development Setup

**Backend (without Docker):**

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

**Frontend (without Docker):**

```bash
cd frontend
npm install
npm start
```

**Celery Worker:**

```bash
cd backend
celery -A config worker -l info
```

## API Documentation

### Authentication

| Method | Endpoint                  | Description          |
|--------|---------------------------|----------------------|
| POST   | `/api/auth/register/`     | Register new user    |
| POST   | `/api/auth/login/`        | Login (obtain JWT)   |
| POST   | `/api/auth/refresh/`      | Refresh JWT token    |
| GET    | `/api/auth/profile/`      | Get user profile     |
| PUT    | `/api/auth/profile/`      | Update profile       |

### Files

| Method | Endpoint                          | Description            |
|--------|-----------------------------------|------------------------|
| GET    | `/api/files/`                     | List files             |
| POST   | `/api/files/upload/`              | Upload file            |
| GET    | `/api/files/{id}/`                | Get file details       |
| PUT    | `/api/files/{id}/`                | Update file metadata   |
| DELETE | `/api/files/{id}/`                | Move to trash          |
| GET    | `/api/files/{id}/download/`       | Download file          |
| GET    | `/api/files/{id}/versions/`       | List file versions     |
| POST   | `/api/files/{id}/versions/{v}/restore/` | Restore version  |
| GET    | `/api/files/{id}/preview/`        | Preview file           |

### Folders

| Method | Endpoint                    | Description          |
|--------|-----------------------------|----------------------|
| GET    | `/api/folders/`             | List folders         |
| POST   | `/api/folders/`             | Create folder        |
| GET    | `/api/folders/{id}/`        | Get folder details   |
| PUT    | `/api/folders/{id}/`        | Update folder        |
| DELETE | `/api/folders/{id}/`        | Delete folder        |
| GET    | `/api/folders/{id}/contents/` | List folder contents |
| POST   | `/api/folders/{id}/move/`   | Move folder          |

### Sharing

| Method | Endpoint                         | Description           |
|--------|----------------------------------|-----------------------|
| POST   | `/api/sharing/links/`            | Create shared link    |
| GET    | `/api/sharing/links/`            | List shared links     |
| DELETE | `/api/sharing/links/{id}/`       | Revoke shared link    |
| POST   | `/api/sharing/permissions/`      | Share with user       |
| GET    | `/api/sharing/shared-with-me/`   | Files shared with me  |
| GET    | `/api/s/{token}/`                | Access shared link    |

### Trash

| Method | Endpoint                     | Description           |
|--------|------------------------------|-----------------------|
| GET    | `/api/trash/`                | List trashed items    |
| POST   | `/api/trash/{id}/restore/`   | Restore item          |
| DELETE | `/api/trash/{id}/`           | Permanently delete    |
| POST   | `/api/trash/empty/`          | Empty trash           |

### Search

| Method | Endpoint                    | Description           |
|--------|-----------------------------|-----------------------|
| GET    | `/api/search/?q=term`       | Search files/folders  |

## Environment Variables

See `.env.example` for all configurable environment variables including database credentials, JWT settings, MinIO configuration, and storage quota defaults.

## Deployment

For production deployment:

1. Update `.env` with secure credentials
2. Set `DJANGO_SETTINGS_MODULE=config.settings.prod`
3. Configure SSL certificates in Nginx
4. Set up proper backup strategies for PostgreSQL and MinIO
5. Configure monitoring and log aggregation

## License

MIT License - see LICENSE file for details.
