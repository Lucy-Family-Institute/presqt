#!/bin/sh
# Start the Django Development Server once the database is 
# available after bootstraping process

set -e

until python docker/postgres_health_check.py; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

python manage.py migrate
python manage.py collectstatic --no-input

if [ "$ENVIRONMENT" = "development" ]
then
python manage.py runserver 0.0.0.0:8000
else
gunicorn config.wsgi:application --bind 0.0.0.0:8000
fi
