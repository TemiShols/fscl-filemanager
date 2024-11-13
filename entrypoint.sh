#!/bin/sh

set -e

# Wait for Redis to be ready
echo "Waiting for Redis to be ready..."
until nc -z redis 6379; do
    sleep 1
done
echo "Redis is ready"

# Wait for PostgreSQL to start
echo "Waiting for PostgreSQL to start..."
python << END
import socket
import time
import os
import psycopg

host = "fileapp_db"
port = 5432
max_attempts = 30
attempt = 0

while attempt < max_attempts:
    try:
        with socket.create_connection((host, port), timeout=1):
            print(f"Successfully connected to {host}:{port}")
            break
    except socket.error as e:
        attempt += 1
        print(f"Attempt {attempt}/{max_attempts}: Cannot connect to {host}:{port}. Error: {e}")
        time.sleep(2)
else:
    print(f"Failed to connect to {host}:{port} after {max_attempts} attempts")
    exit(1)

print("Attempting to connect to the database...")
attempt = 0
while attempt < max_attempts:
    try:
        conn = psycopg.connect(os.environ['DATABASE_URL'])
        print("Successfully connected to PostgreSQL")
        conn.close()
        break
    except psycopg.OperationalError as e:
        attempt += 1
        print(f"Failed to connect to PostgreSQL (attempt {attempt}/{max_attempts}): {e}")
        time.sleep(2)
else:
    print("Failed to connect to PostgreSQL after maximum attempts")
    exit(1)

END

# Run migrations
echo "Running migrations..."
python manage.py migrate
echo "Migrations complete"

# Start Celery worker
echo "Starting Celery worker..."
celery -A fileapp worker --pool=solo -l info &

# Start Django server
echo "Starting Django server..."
python manage.py runserver 0.0.0.0:8000
