#!/bin/bash
# Run migrations before starting the application

echo "Running database migrations..."
cd /opt/render/project/src
pip install -r requirements.txt -q
alembic upgrade head

echo "Starting application..."
exec gunicorn -b 0.0.0.0:$PORT "src.app:create_app()"
