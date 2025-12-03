#!/bin/bash

# Exit on error
set -e

echo "Running database migrations..."
python manage.py migrate --settings=shortdeal.settings.production --noinput

echo "Collecting static files..."
python manage.py collectstatic --settings=shortdeal.settings.production --noinput

echo "Starting gunicorn server..."
exec gunicorn shortdeal.wsgi:application --bind 0.0.0.0:${PORT:-8000}
