# Stage 1: Build the Vue frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./
RUN npm install

# Copy frontend source
COPY frontend/ ./
# Build the production bundle
RUN npm run build

# Stage 2: Build the FastAPI backend
FROM python:3.11-slim
WORKDIR /app

# Ensure curl is installed for potential healthchecks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend source code and CLI
COPY backend/ ./backend/
COPY cli.py ./

# Copy the entrypoint script
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

# Copy the built frontend from Stage 1 into the expected location
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create directories for data and uploads
RUN mkdir -p /app/data /app/uploads

# Expose the API port
EXPOSE 8000

# Run migrations then start Uvicorn
CMD ["./entrypoint.sh"]
