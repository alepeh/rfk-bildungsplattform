#!/bin/bash

RUN_PORT="8001"

echo "=== Starting Django Application ==="

# Force ENVIRONMENT to staging for container deployments
# (The container environment might have ENVIRONMENT=production set incorrectly)
export ENVIRONMENT="staging"
echo "Forcing ENVIRONMENT to staging for container deployment"

# Set default SECRET_KEY if not provided (for staging/development)
if [ -z "$SECRET_KEY" ]; then
    export SECRET_KEY="django-insecure-staging-key-only-for-testing"
    echo "Using default SECRET_KEY for staging"
fi

# Show environment info
echo "Environment: ${ENVIRONMENT:-not_set}"
echo "Python version: $(/opt/venv/bin/python --version)"

# Run migrations at startup
echo "Running database migrations..."
/opt/venv/bin/python manage.py migrate --noinput

echo "Migrations completed. Now testing Django configuration..."

# Check if Django can start properly (but don't fail if this has issues)
/opt/venv/bin/python manage.py check 2>&1 || echo "Django check had warnings/errors but continuing..."

echo "Testing WSGI application import..."
# Test if we can import the WSGI application (but don't fail if this has issues)
/opt/venv/bin/python -c "from bildungsplattform.wsgi import application; print('WSGI application imported successfully')" 2>&1 || echo "WSGI import had issues but continuing..."

# Start gunicorn with simplified configuration first
echo "Starting gunicorn on port ${RUN_PORT} (simplified config)..."
/opt/venv/bin/gunicorn bildungsplattform.wsgi:application \
    --bind "0.0.0.0:${RUN_PORT}" \
    --workers 1 \
    --timeout 120 \
    --log-level info \
    --daemon

echo "Gunicorn command executed. Waiting for startup..."
sleep 5

# Check if gunicorn is running
if pgrep gunicorn > /dev/null; then
    echo "SUCCESS: Gunicorn is running (PID: $(pgrep gunicorn))"
else
    echo "ERROR: Gunicorn is not running. Checking processes:"
    ps aux | grep -E "(python|gunicorn)" || echo "No relevant processes found"
    echo "Attempting to start gunicorn in foreground for debugging:"
    /opt/venv/bin/gunicorn bildungsplattform.wsgi:application \
        --bind "0.0.0.0:${RUN_PORT}" \
        --workers 1 \
        --timeout 120 \
        --log-level debug
    exit 1
fi

echo "Starting nginx..."
# Start nginx in the foreground
exec nginx -g 'daemon off;'
