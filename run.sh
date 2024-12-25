#!/bin/sh


# Start Gunicorn
gunicorn --bind :${PORT} --workers 2 config.wsgi

# Start Celery worker
celery -A data_compare worker -l INFO --concurrency=2 &
