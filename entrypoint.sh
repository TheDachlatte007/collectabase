#!/bin/sh
set -e

echo "=== Collectabase startup ==="

# Ensure data directory exists
mkdir -p /app/data /app/uploads

# Run Alembic migrations – creates all tables on first run, applies future migrations safely
echo "Running database migrations..."
cd /app
python -m alembic --config backend/alembic.ini upgrade head
echo "Migrations complete."

# Start the application
echo "Starting Uvicorn..."
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000
