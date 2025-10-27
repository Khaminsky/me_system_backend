# Docker Setup Guide

This project is now fully dockerized with both the Django application and PostgreSQL database running in containers.

## Prerequisites

- Docker (version 20.10+)
- Docker Compose (version 1.29+)

## Quick Start

### 1. Clone and Setup

```bash
# Navigate to project directory
cd me_system_backend

# Copy environment file
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env` file with your settings:

```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DB_PASSWORD=your-secure-password
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 3. Build and Run

```bash
# Build images and start containers
docker-compose up -d

# View logs
docker-compose logs -f web

# Run migrations (if not auto-run)
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

### 4. Access Application

- **API**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **API Documentation**: http://localhost:8000/api/docs (if drf-yasg is configured)

## Common Commands

### Development

```bash
# Start services
docker-compose up

# Start in background
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f web
docker-compose logs -f db

# Run Django commands
docker-compose exec web python manage.py shell
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

### Database

```bash
# Access PostgreSQL shell
docker-compose exec db psql -U postgres -d me_system_db

# Backup database
docker-compose exec db pg_dump -U postgres me_system_db > backup.sql

# Restore database
docker-compose exec -T db psql -U postgres me_system_db < backup.sql
```

### Cleanup

```bash
# Stop and remove containers
docker-compose down

# Remove volumes (WARNING: deletes data)
docker-compose down -v

# Remove all images
docker-compose down --rmi all
```

## File Structure

```
.
├── Dockerfile              # Django application container
├── docker-compose.yml      # Multi-container orchestration
├── .dockerignore          # Files to exclude from Docker build
├── .env.example           # Environment variables template
├── requirements.txt       # Python dependencies
├── manage.py              # Django management script
├── core/                  # Django project settings
├── surveys/               # Surveys app
├── users/                 # Users app
└── DOCKER_SETUP.md        # This file
```

## Services

### Web Service
- **Image**: Built from Dockerfile
- **Port**: 8000 (configurable via WEB_PORT)
- **Database**: PostgreSQL (db service)
- **Volumes**: 
  - Application code (development)
  - uploads/ (survey files)
  - cleaned_uploads/ (processed files)

### Database Service
- **Image**: postgres:16-alpine
- **Port**: 5432 (configurable via DB_PORT)
- **Volume**: postgres_data (persistent storage)
- **Health Check**: Enabled

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| DEBUG | True | Django debug mode |
| SECRET_KEY | dev-secret-key-change-in-production | Django secret key |
| DB_NAME | me_system_db | PostgreSQL database name |
| DB_USER | postgres | PostgreSQL username |
| DB_PASSWORD | postgres | PostgreSQL password |
| DB_HOST | db | PostgreSQL host (service name) |
| DB_PORT | 5432 | PostgreSQL port |
| WEB_PORT | 8000 | Django application port |
| ALLOWED_HOSTS | localhost,127.0.0.1 | Allowed hosts |

## Production Deployment

For production, modify docker-compose.yml:

1. Set `DEBUG=False`
2. Use a strong `SECRET_KEY`
3. Configure proper `ALLOWED_HOSTS`
4. Use environment-specific `.env` file
5. Consider using nginx as reverse proxy
6. Enable HTTPS/SSL
7. Use managed database service instead of container

## Troubleshooting

### Database Connection Error
```bash
# Check if db service is healthy
docker-compose ps

# View db logs
docker-compose logs db

# Restart db service
docker-compose restart db
```

### Port Already in Use
```bash
# Change port in .env
WEB_PORT=8001
DB_PORT=5433

# Rebuild and restart
docker-compose down
docker-compose up -d
```

### Permission Denied
```bash
# On Linux, you may need to use sudo
sudo docker-compose up -d
```

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Django Deployment Guide](https://docs.djangoproject.com/en/5.2/howto/deployment/)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)

