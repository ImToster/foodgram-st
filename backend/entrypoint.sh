#!/bin/sh

python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py loaddata db.json

python3 manage.py collectstatic
cp -r /app/collected_static/. /backend_static/static/

gunicorn --bind 0.0.0.0:8000 foodgram_backend.wsgi