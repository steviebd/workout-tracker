FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    PORT=8080

# Create app user
RUN groupadd -r workout && useradd -r -g workout workout

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements-production.txt .
RUN pip install --no-cache-dir -r requirements-production.txt

# Copy application code
COPY server/ ./server/
COPY public/ ./public/
COPY .env.example .env

# Create necessary directories
RUN mkdir -p data logs backups && \
    chown -R workout:workout /app

# Switch to non-root user
USER workout

# Initialize database
RUN cd server && DATABASE_PATH=/app/data/workout.db python seed.py

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Start application
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "120", "--chdir", "server", "wsgi:application"]
