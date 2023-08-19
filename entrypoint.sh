#!/bin/bash
RUN_PORT="8001"

/opt/venv/bin/gunicorn bildungsplattform.wsgi.application --bind "0.0.0.0:${RUN_PORT}" --daemon

nginx -g 'daemon off;'
