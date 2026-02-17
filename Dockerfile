FROM python:3.11-slim

# Install Node.js
RUN apt-get update && apt-get install -y nodejs npm && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Backend dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Backend code
COPY backend/ ./backend/

# Frontend dependencies
COPY frontend/package*.json ./frontend/
RUN cd frontend && npm install

# Frontend code + build
COPY frontend/ ./frontend/
RUN cd frontend && npm run build

# Move build to backend static
RUN mkdir -p backend/static && cp -r frontend/dist/* backend/static/

# Create data directories
RUN mkdir -p /app/data /app/uploads

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
