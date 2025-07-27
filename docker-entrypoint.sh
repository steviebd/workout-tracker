#!/bin/bash
set -e

echo "🚀 Starting Workout Tracker..."

# Initialize database if it doesn't exist
if [ ! -f "/app/data/workout.db" ]; then
    echo "🗄️  Initializing database..."
    cd /app/server
    
    # Check if we have admin password from environment
    if [ -n "$ADMIN_TEMP_PASSWORD" ]; then
        echo "🔑 Using admin password from environment"
        python seed.py
    else
        echo "⚠️  No ADMIN_TEMP_PASSWORD set, generating random password"
        python seed.py
    fi
    
    echo "✅ Database initialized successfully!"
else
    echo "📂 Database already exists, skipping initialization"
fi

echo "🏃 Starting Gunicorn server..."

# Start the application
cd /app
exec gunicorn --bind 0.0.0.0:8080 --workers 2 --timeout 120 --chdir server wsgi:application
