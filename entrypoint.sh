#!/bin/sh
set -e

echo "=== Collectabase startup ==="

# Ensure data directories exist
mkdir -p /app/data /app/uploads /app/backups

# Run Alembic migrations – creates all tables on first run, applies future migrations safely
echo "Running database migrations..."
cd /app
python -m alembic --config backend/alembic.ini upgrade head
echo "Migrations complete."

# Start the application
echo "Starting Uvicorn..."
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000
