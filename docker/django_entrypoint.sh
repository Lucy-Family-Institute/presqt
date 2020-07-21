#!/bin/sh
# Start the Django Development Server once the database is 
# available after bootstraping process

set -e

python manage.py collectstatic --no-input

python manage.py validate_target_json
python manage.py delete_outdated_mediafiles

if [ "$ENVIRONMENT" = "development" ]
then
python manage.py runserver 0.0.0.0:8000
elif [ "$ENVIRONMENT" = "ci" ]
then
python manage.py test
else
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --timeout 600
fi
