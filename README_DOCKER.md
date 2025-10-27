# ME System Backend - Docker Setup

A fully dockerized Django REST Framework application for survey data management with PostgreSQL database.

## 🚀 Quick Start

### Prerequisites
- Docker (20.10+)
- Docker Compose (1.29+)

### Setup (5 minutes)

```bash
# 1. Clone repository
cd me_system_backend

# 2. Configure environment (optional - defaults are provided)
# Edit .env file if needed
nano .env

# 3. Build and start
docker-compose up -d

# 4. Create superuser
docker-compose exec web python manage.py createsuperuser

# 5. Access application
# API: http://localhost:8000
# Admin: http://localhost:8000/admin
```

## 📋 Available Commands

### Using Docker Compose Directly

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f web

# Run Django commands
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py shell

# Stop services
docker-compose down
```

### Using Makefile (Recommended)

```bash
make up                 # Start containers
make down               # Stop containers
make logs               # View app logs
make migrate            # Run migrations
make createsuperuser    # Create superuser
make shell              # Django shell
make bash               # Bash in container
make db-shell           # PostgreSQL shell
make backup-db          # Backup database
make clean              # Remove containers & volumes
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         Docker Network                  │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────┐    ┌──────────────┐  │
│  │   Django     │    │  PostgreSQL  │  │
│  │   Web App    │───→│  Database    │  │
│  │ (Port 8000)  │    │ (Port 5432)  │  │
│  └──────────────┘    └──────────────┘  │
│                                         │
│  Volumes:                               │
│  - uploads/                             │
│  - cleaned_uploads/                     │
│  - postgres_data/                       │
│                                         │
└─────────────────────────────────────────┘
```

## 📁 Project Structure

```
.
├── Dockerfile                 # Django container definition
├── docker-compose.yml         # Development setup
├── docker-compose.prod.yml    # Production setup
├── entrypoint.sh             # Container initialization script
├── .dockerignore             # Files excluded from build
├── .env                      # Environment variables
├── .env.example              # Environment template
├── Makefile                  # Convenient commands
├── requirements.txt          # Python dependencies
├── manage.py                 # Django CLI
├── core/                     # Django project
│   ├── settings.py          # Configuration
│   ├── urls.py              # URL routing
│   ├── wsgi.py              # WSGI application
│   └── asgi.py              # ASGI application
├── surveys/                  # Survey management app
│   ├── models.py            # Survey models
│   ├── serializers.py       # DRF serializers
│   ├── views.py             # API views
│   └── migrations/          # Database migrations
├── users/                    # User management app
│   ├── models.py            # CustomUser model
│   ├── serializers.py       # User serializers
│   └── migrations/          # Database migrations
└── DOCKER_SETUP.md          # Detailed Docker guide
```

## 🔧 Configuration

### Environment Variables

Edit `.env` file to customize:

| Variable | Default | Purpose |
|----------|---------|---------|
| DEBUG | True | Django debug mode |
| SECRET_KEY | dev-key | Django secret key |
| DB_NAME | me_system_db | Database name |
| DB_USER | postgres | Database user |
| DB_PASSWORD | yourpassword | Database password |
| DB_HOST | db | Database host |
| DB_PORT | 5432 | Database port |
| WEB_PORT | 8000 | Application port |
| ALLOWED_HOSTS | localhost,127.0.0.1,web | Allowed hosts |

### Database

PostgreSQL 16 Alpine runs in a separate container with:
- Persistent volume storage
- Health checks
- Automatic initialization

## 🧪 Development Workflow

### Running Tests

```bash
# Run all tests
docker-compose exec web python manage.py test

# Run specific app tests
docker-compose exec web python manage.py test surveys

# Run with coverage
docker-compose exec web coverage run --source='.' manage.py test
docker-compose exec web coverage report
```

### Database Migrations

```bash
# Create migrations
docker-compose exec web python manage.py makemigrations

# Apply migrations
docker-compose exec web python manage.py migrate

# View migration status
docker-compose exec web python manage.py showmigrations
```

### Django Shell

```bash
# Access Django shell
docker-compose exec web python manage.py shell

# Example commands
>>> from surveys.models import Survey
>>> Survey.objects.all()
>>> from users.models import CustomUser
>>> CustomUser.objects.all()
```

## 🗄️ Database Management

### Backup

```bash
# Using Makefile
make backup-db

# Manual backup
docker-compose exec db pg_dump -U postgres me_system_db > backup.sql
```

### Restore

```bash
# Using Makefile
make restore-db

# Manual restore
docker-compose exec -T db psql -U postgres me_system_db < backup.sql
```

### Access PostgreSQL

```bash
# Using Makefile
make db-shell

# Manual access
docker-compose exec db psql -U postgres -d me_system_db
```

## 🚨 Troubleshooting

### Port Already in Use

```bash
# Change port in .env
WEB_PORT=8001
DB_PORT=5433

# Restart
docker-compose down
docker-compose up -d
```

### Database Connection Failed

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### Permission Issues (Linux)

```bash
# Use sudo
sudo docker-compose up -d

# Or add user to docker group
sudo usermod -aG docker $USER
```

### Container Won't Start

```bash
# View detailed logs
docker-compose logs web

# Rebuild image
docker-compose build --no-cache
docker-compose up -d
```

## 📦 Production Deployment

For production, use `docker-compose.prod.yml`:

```bash
# Set production environment
export DEBUG=False
export SECRET_KEY=your-secure-key
export ALLOWED_HOSTS=yourdomain.com

# Start with production config
docker-compose -f docker-compose.prod.yml up -d
```

### Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Use strong `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Use environment-specific `.env`
- [ ] Set up reverse proxy (nginx)
- [ ] Enable HTTPS/SSL
- [ ] Use managed database service
- [ ] Configure logging and monitoring
- [ ] Set up automated backups

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Guide](https://docs.docker.com/compose/)
- [Django Deployment](https://docs.djangoproject.com/en/5.2/howto/deployment/)
- [PostgreSQL Docker](https://hub.docker.com/_/postgres)

## 📝 License

[Your License Here]

## 👥 Support

For issues or questions, please open an issue on GitHub.

