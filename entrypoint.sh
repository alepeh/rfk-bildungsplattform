#!/bin/bash
RUN_PORT="8001"

# Set default SECRET_KEY if not provided (for staging/development)
if [ -z "$SECRET_KEY" ]; then
    export SECRET_KEY="django-insecure-staging-key-only-for-testing"
fi

# Run migrations at startup
echo "Running database migrations..."
/opt/venv/bin/python manage.py migrate --noinput

# Check if Django can start properly
echo "Testing Django configuration..."
/opt/venv/bin/python manage.py check

# Start gunicorn in the background with more verbose logging
echo "Starting gunicorn on port ${RUN_PORT}..."
/opt/venv/bin/gunicorn bildungsplattform.wsgi:application \
    --bind "0.0.0.0:${RUN_PORT}" \
    --workers 2 \
    --timeout 30 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    --daemon

# Wait a moment for gunicorn to start
sleep 2

# Check if gunicorn is running
if ! pgrep gunicorn > /dev/null; then
    echo "ERROR: Gunicorn failed to start"
    exit 1
fi

echo "Gunicorn started successfully"

# Start nginx in the foreground
nginx -g 'daemon off;'
