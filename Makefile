.PHONY: help build up down logs shell migrate createsuperuser clean test lint

help:
	@echo "Available commands:"
	@echo "  make build              - Build Docker images"
	@echo "  make up                 - Start containers in background"
	@echo "  make down               - Stop containers"
	@echo "  make logs               - View application logs"
	@echo "  make logs-db            - View database logs"
	@echo "  make shell              - Open Django shell"
	@echo "  make migrate            - Run database migrations"
	@echo "  make createsuperuser    - Create Django superuser"
	@echo "  make clean              - Remove containers and volumes"
	@echo "  make test               - Run tests"
	@echo "  make lint               - Run code linting"
	@echo "  make bash               - Open bash in web container"
	@echo "  make db-shell           - Open PostgreSQL shell"
	@echo "  make backup-db          - Backup database"
	@echo "  make restore-db         - Restore database from backup"

build:
	docker-compose build

up:
	docker-compose up -d
	@echo "Application started at http://localhost:8000"

down:
	docker-compose down

logs:
	docker-compose logs -f web

logs-db:
	docker-compose logs -f db

shell:
	docker-compose exec web python manage.py shell

migrate:
	docker-compose exec web python manage.py migrate

makemigrations:
	docker-compose exec web python manage.py makemigrations

createsuperuser:
	docker-compose exec web python manage.py createsuperuser

bash:
	docker-compose exec web bash

db-shell:
	docker-compose exec db psql -U postgres -d me_system_db

backup-db:
	docker-compose exec db pg_dump -U postgres me_system_db > backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Database backed up successfully"

restore-db:
	@read -p "Enter backup file path: " backup_file; \
	docker-compose exec -T db psql -U postgres me_system_db < $$backup_file
	@echo "Database restored successfully"

test:
	docker-compose exec web python manage.py test

lint:
	docker-compose exec web flake8 . --exclude=migrations,venv

clean:
	docker-compose down -v
	@echo "Containers and volumes removed"

ps:
	docker-compose ps

restart:
	docker-compose restart

restart-web:
	docker-compose restart web

restart-db:
	docker-compose restart db

