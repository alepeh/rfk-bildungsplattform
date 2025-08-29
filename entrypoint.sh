#!/bin/bash
RUN_PORT="8001"

# Run migrations at startup
echo "Running database migrations..."
/opt/venv/bin/python manage.py migrate --noinput

# Start gunicorn in the background
/opt/venv/bin/gunicorn bildungsplattform.wsgi:application --bind "0.0.0.0:${RUN_PORT}" --daemon

# Start nginx in the foreground
nginx -g 'daemon off;'
