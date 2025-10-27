# Docker Quick Reference Card

## 🚀 Getting Started (Copy & Paste)

```bash
# Start everything
docker-compose up -d

# Create admin user
docker-compose exec web python manage.py createsuperuser

# View logs
docker-compose logs -f web

# Stop everything
docker-compose down
```

## 📋 Essential Commands

| Task | Command |
|------|---------|
| **Start** | `docker-compose up -d` |
| **Stop** | `docker-compose down` |
| **Logs** | `docker-compose logs -f web` |
| **Status** | `docker-compose ps` |
| **Restart** | `docker-compose restart` |
| **Rebuild** | `docker-compose build` |

## 🔧 Django Commands

| Task | Command |
|------|---------|
| **Migrations** | `docker-compose exec web python manage.py migrate` |
| **Make Migrations** | `docker-compose exec web python manage.py makemigrations` |
| **Superuser** | `docker-compose exec web python manage.py createsuperuser` |
| **Shell** | `docker-compose exec web python manage.py shell` |
| **Tests** | `docker-compose exec web python manage.py test` |
| **Collect Static** | `docker-compose exec web python manage.py collectstatic` |

## 🗄️ Database Commands

| Task | Command |
|------|---------|
| **PostgreSQL Shell** | `docker-compose exec db psql -U postgres -d me_system_db` |
| **Backup** | `docker-compose exec db pg_dump -U postgres me_system_db > backup.sql` |
| **Restore** | `docker-compose exec -T db psql -U postgres me_system_db < backup.sql` |
| **List Tables** | `docker-compose exec db psql -U postgres -d me_system_db -c "\dt"` |

## 🐚 Container Access

| Task | Command |
|------|---------|
| **Bash in Web** | `docker-compose exec web bash` |
| **Bash in DB** | `docker-compose exec db sh` |
| **Python Shell** | `docker-compose exec web python` |
| **Install Package** | `docker-compose exec web pip install package-name` |

## 📊 Monitoring

| Task | Command |
|------|---------|
| **View All Logs** | `docker-compose logs` |
| **Web Logs** | `docker-compose logs -f web` |
| **DB Logs** | `docker-compose logs -f db` |
| **Last 100 Lines** | `docker-compose logs --tail=100 web` |
| **Container Stats** | `docker stats` |

## 🧹 Cleanup

| Task | Command |
|------|---------|
| **Stop All** | `docker-compose down` |
| **Remove Volumes** | `docker-compose down -v` |
| **Remove Images** | `docker-compose down --rmi all` |
| **Prune System** | `docker system prune -a` |

## 🔌 Ports & Access

| Service | URL | Port |
|---------|-----|------|
| **API** | http://localhost:8000 | 8000 |
| **Admin** | http://localhost:8000/admin | 8000 |
| **Database** | localhost | 5432 |

## 📝 Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Environment variables |
| `Dockerfile` | App container definition |
| `docker-compose.yml` | Development setup |
| `docker-compose.prod.yml` | Production setup |
| `entrypoint.sh` | Container startup script |
| `.dockerignore` | Files to exclude from build |

## 🆘 Troubleshooting

### Port Already in Use
```bash
# Change port in .env
WEB_PORT=8001

# Restart
docker-compose down && docker-compose up -d
```

### Database Won't Connect
```bash
# Check status
docker-compose ps

# View logs
docker-compose logs db

# Restart
docker-compose restart db
```

### Container Won't Start
```bash
# View detailed logs
docker-compose logs web

# Rebuild
docker-compose build --no-cache
docker-compose up -d
```

### Permission Denied (Linux)
```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

## 🎯 Using Makefile (Easier!)

```bash
make up                 # Start
make down               # Stop
make logs               # View logs
make migrate            # Run migrations
make createsuperuser    # Create admin
make shell              # Django shell
make bash               # Container bash
make db-shell           # PostgreSQL shell
make backup-db          # Backup database
make clean              # Remove everything
make help               # Show all commands
```

## 📚 Documentation

- **Full Setup Guide**: `DOCKER_SETUP.md`
- **Quick Start**: `README_DOCKER.md`
- **Implementation Details**: `DOCKER_FILES_SUMMARY.md`
- **This Card**: `DOCKER_QUICK_REFERENCE.md`

## 🔐 Security Reminders

⚠️ **Development Only**:
- DEBUG=True
- Default SECRET_KEY
- Default DB password

✅ **Before Production**:
- Set DEBUG=False
- Generate strong SECRET_KEY
- Use strong DB password
- Configure ALLOWED_HOSTS
- Set up HTTPS/SSL
- Use environment-specific .env

## 💡 Pro Tips

1. **Use Makefile** - Easier than typing full commands
2. **Check Logs First** - Most issues visible in logs
3. **Backup Before Changes** - `make backup-db`
4. **Use .env** - Never hardcode secrets
5. **Read Documentation** - Refer to DOCKER_SETUP.md

## 🔗 Useful Links

- [Docker Docs](https://docs.docker.com/)
- [Docker Compose Docs](https://docs.docker.com/compose/)
- [Django Docs](https://docs.djangoproject.com/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)

---

**Last Updated**: 2025-10-27
**Version**: 1.0

