#!/bin/sh
echo "Starting Delice Express on port ${PORT:-5000}"
exec gunicorn --bind "0.0.0.0:${PORT:-5000}" --workers 2 --threads 2 --timeout 120 app:app
