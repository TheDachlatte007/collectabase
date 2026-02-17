#!/bin/bash
cd $(dirname "$0")/backend
python3 -c "from database import init_db; init_db()"
cd ..
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000
