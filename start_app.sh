#!/bin/bash

# # Set environment variables for Saleor
# export DJANGO_SETTINGS_MODULE=saleor.settings
# export DATABASE_URL=postgres://saleor:saleor@db/saleor
# export SECRET_KEY=changeme
# export CELERY_BROKER_URL=redis://redis:6379/1
# export DEFAULT_FROM_EMAIL=noreply@example.com
# export DASHBOARD_URL=http://localhost:9000/
# export EMAIL_URL=smtp://mailpit:1025
# export DEFAULT_CHANNEL_SLUG=default-channel
# export HTTP_IP_FILTER_ALLOW_LOOPBACK_IPS=True

# Activate virtual environment
source .venv/bin/activate

# Start the application
echo "Starting Saleor application..."
# uvicorn saleor.asgi:application --host=0.0.0.0 --port=8000 --lifespan=off

cd /home/lei/workspace/88clipon/saleor && \
source .venv/bin/activate && \
export PYTHONDONTWRITEBYTECODE=1 && \
"uvicorn" "saleor.asgi:application" "--host=0.0.0.0" "--port=8000" "--workers=2" "--lifespan=off" "--ws=none" "--no-server-header" "--no-access-log" "--timeout-keep-alive=35" "--timeout-graceful-shutdown=30" "--limit-max-requests=10000"
