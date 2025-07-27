#!/bin/bash

echo "🗑️  Resetting Workout Tracker Database"
echo "======================================"

# Stop any running Docker containers
echo "🛑 Stopping Docker containers..."
docker-compose down -v --remove-orphans 2>/dev/null || echo "No Docker containers to stop"

# Remove old database files
echo "🧹 Cleaning up old database files..."
rm -f server/workout.db
rm -f ./workout.db
rm -f /tmp/workout.db

# Remove old .env if it exists
if [ -f .env ]; then
    echo "🔄 Backing up existing .env to .env.backup"
    cp .env .env.backup
    rm -f .env
fi

# Run generate-secrets.py with development defaults
echo "🔐 Generating new configuration with development settings..."

# Generate secrets
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
ADMIN_PASSWORD=$(python3 -c "import secrets, string; alphabet = string.ascii_letters + string.digits + '!@#+-='; password = ''.join(secrets.choice(alphabet) for i in range(12)); password = 'A' + password[1:] if not any(c.isupper() for c in password) else password; password = 'a' + password[1:] if not any(c.islower() for c in password) else password; password = '1' + password[1:] if not any(c.isdigit() for c in password) else password; password = '!' + password[1:] if not any(c in '!@#+-=' for c in password) else password; print(password)")

# Create a basic development .env file
cat > .env << EOF
# Development Environment Configuration
SECRET_KEY=${SECRET_KEY}
JWT_SECRET_KEY=${JWT_SECRET_KEY}
CORS_ORIGINS=http://localhost:8080
FLASK_ENV=development
JWT_EXPIRES_MINUTES=15
DATABASE_PATH=./server/workout.db
CORS_SUPPORTS_CREDENTIALS=false
RATE_LIMIT_DEFAULT="2000 per hour, 200 per minute"
RATE_LIMIT_AUTH_LOGIN="10 per minute" 
RATE_LIMIT_AUTH_REGISTER="5 per minute"
RATE_LIMIT_STORAGE_URI=memory://
PASSWORD_MIN_LENGTH=6
PASSWORD_MAX_LENGTH=128
PASSWORD_REQUIRE_UPPERCASE=false
PASSWORD_REQUIRE_LOWERCASE=false
PASSWORD_REQUIRE_NUMBERS=false
PASSWORD_REQUIRE_SPECIAL=false
PASSWORD_BLOCK_COMMON=true
PORT=8080
SKIP_SECRET_VALIDATION=true
ADMIN_TEMP_PASSWORD=${ADMIN_PASSWORD}
APP_URL=http://localhost:8080
SMTP_SERVER=localhost
SMTP_PORT=25
SMTP_USE_TLS=false
FROM_EMAIL=noreply@localhost
EOF

# Set secure permissions
chmod 600 .env

echo "✅ Created development .env file"

if [ $? -eq 0 ]; then
    echo "✅ Configuration generated successfully!"
    
    # Initialize the database
    echo "🗄️  Initializing database..."
    source .venv/bin/activate 2>/dev/null || echo "⚠️  No virtual environment found"
    python3 server/seed.py
    
    # Show the admin credentials
    echo ""
    echo "👑 ADMIN CREDENTIALS (save these!):"
    echo "=================================="
    echo "Username: admin"
    echo "Password: ${ADMIN_PASSWORD}"
    echo "=================================="
    echo ""
    
    echo "🚀 Deploying with Docker Compose using your .env credentials..."
    echo "🗑️  Removing old Docker volumes to force fresh database initialization..."
    docker-compose down -v --remove-orphans
    
    echo "🏗️  Building and starting containers with fresh database..."
    docker-compose up --build -d
    
    echo "⏳ Waiting for containers to start..."
    sleep 5
    
    echo "🔍 Verifying database initialization..."
    # Check if the database was properly initialized
    if docker-compose logs workout-tracker | grep -q "Using admin password from environment"; then
        echo "✅ Database properly initialized with .env password"
    else
        echo "⚠️  Database initialization may have issues. Check logs:"
        docker-compose logs workout-tracker | tail -10
    fi
    
    echo ""
    echo "🧪 Testing admin login..."
    sleep 2  # Give the server a moment more to fully start
    
    # Test the admin login
    LOGIN_RESPONSE=$(curl -s -X POST http://localhost/api/auth/login \
        -H "Content-Type: application/json" \
        -d "{\"username\": \"admin\", \"password\": \"${ADMIN_PASSWORD}\"}")
    
    if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
        echo "✅ Admin login test PASSED!"
        echo "🎉 Role-based authentication system is fully functional!"
    else
        echo "❌ Admin login test FAILED!"
        echo "🔍 Login response: $LOGIN_RESPONSE"
        echo "💡 Try manually: curl -X POST http://localhost/api/auth/login -H \"Content-Type: application/json\" -d '{\"username\": \"admin\", \"password\": \"${ADMIN_PASSWORD}\"}'"
    fi
    
    echo ""
    echo "✅ Deployment complete!"
    echo "🌐 Access your app at: http://localhost"
    echo "📋 Check Docker logs with: docker-compose logs workout-tracker"
else
    echo "❌ Configuration generation failed!"
    if [ -f .env.backup ]; then
        echo "🔄 Restoring backup .env file"
        mv .env.backup .env
    fi
    exit 1
fi
