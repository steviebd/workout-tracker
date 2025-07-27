#!/bin/bash

echo "🧪 Testing Workout Tracker Role-Based Authentication Setup"
echo "=========================================================="

# Clean up any existing files
echo "🧹 Cleaning up existing files..."
rm -f .env server/workout.db

# Run the generator in development mode with local SMTP
echo "🔐 Running generate-secrets.py with test configuration..."
python3 scripts/generate-secrets.py << 'EOF'
http://localhost:8080
development

Y
Y
4

Y
Y
EOF

if [ $? -eq 0 ]; then
    echo "✅ Configuration generated successfully!"
else
    echo "❌ Configuration generation failed!"
    exit 1
fi

# Test seed script manually
echo "🌱 Testing seed script manually..."
source .venv/bin/activate 2>/dev/null || echo "⚠️  Virtual environment not found"
python3 server/seed.py

if [ $? -eq 0 ]; then
    echo "✅ Database seeded successfully!"
else
    echo "❌ Database seeding failed!"
    exit 1
fi

# Test Docker Compose
echo "🐳 Testing Docker Compose deployment..."
docker-compose down -v --remove-orphans
docker-compose up -d

echo "⏳ Waiting for services to start..."
sleep 10

# Test health endpoint
echo "🏥 Testing health endpoint..."
if curl -f -s http://localhost/health > /dev/null; then
    echo "✅ Health check passed!"
else
    echo "❌ Health check failed!"
    docker-compose logs
    exit 1
fi

# Test admin login (this will fail since Docker creates its own admin, but that's expected)
echo "🔑 Testing API endpoint availability..."
RESPONSE=$(curl -s -X POST http://localhost/api/auth/login -H "Content-Type: application/json" -d '{"username": "test", "password": "invalid"}')
if echo "$RESPONSE" | grep -q "error"; then
    echo "✅ Authentication API is responding correctly!"
else
    echo "❌ Authentication API not responding properly!"
    echo "Response: $RESPONSE"
fi

echo ""
echo "🎉 Setup test completed!"
echo "📋 Next steps:"
echo "   1. Open http://localhost in your browser"
echo "   2. Login with the admin credentials from the Docker build output"
echo "   3. Go to Settings → User Management to test admin features"
echo "   4. Use 'Forgot Password' to test email functionality"
echo ""
echo "🐳 Docker services are running. Use 'docker-compose down' to stop."
