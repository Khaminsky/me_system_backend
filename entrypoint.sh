#!/bin/sh

# Exit on error
set -e

echo "Waiting for PostgreSQL..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.1
done
echo "PostgreSQL started"

echo "Running migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput || true

echo "Setting up admin user..."
python manage.py setup_admin || echo "Note: Could not run setup_admin command"

echo "Starting application..."
exec "$@"

