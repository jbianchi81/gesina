#!/bin/sh
echo "Waiting for Database..."

while ! nc -z database 5432; do
  sleep 0.1
done

echo "Database up and running!"

gunicorn --bind 0.0.0.0:5000 -w 4 --timeout 90 --pythonpath src src.app:app