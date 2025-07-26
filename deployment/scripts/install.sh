#!/bin/bash
set -e

# Workout Tracker PWA Installation Script for Ubuntu/Debian LXC
# Run as root

echo "🏋️ Installing Workout Tracker PWA..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root"
   exit 1
fi

# Variables
APP_USER="workout-tracker"
APP_DIR="/opt/workout-tracker"
SERVICE_NAME="workout-tracker"

print_status "Updating system packages..."
apt update && apt upgrade -y

print_status "Installing required packages..."
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    nginx \
    sqlite3 \
    curl \
    wget \
    unzip \
    logrotate \
    cron

# Create application user
if ! id "$APP_USER" &>/dev/null; then
    print_status "Creating application user..."
    useradd --system --home-dir $APP_DIR --shell /bin/bash --create-home $APP_USER
else
    print_status "Application user already exists"
fi

# Create directory structure
print_status "Creating directory structure..."
mkdir -p $APP_DIR/{data,logs,backups,public,server}
chown -R $APP_USER:$APP_USER $APP_DIR

# Copy application files (assuming they're in current directory)
print_status "Installing application files..."
cp -r server/* $APP_DIR/server/
cp -r public/* $APP_DIR/public/
cp requirements-production.txt $APP_DIR/
cp .env.example $APP_DIR/

# Set up Python virtual environment
print_status "Setting up Python virtual environment..."
su - $APP_USER -c "cd $APP_DIR && python3 -m venv venv"
su - $APP_USER -c "cd $APP_DIR && venv/bin/pip install --upgrade pip"
su - $APP_USER -c "cd $APP_DIR && venv/bin/pip install -r requirements-production.txt"

# Set up environment file
if [ ! -f "$APP_DIR/.env" ]; then
    print_status "Creating environment file..."
    cp $APP_DIR/.env.example $APP_DIR/.env
    
    # Generate secure keys
    SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
    JWT_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
    
    sed -i "s/your-super-secret-key-here-minimum-32-characters-long/$SECRET_KEY/" $APP_DIR/.env
    sed -i "s/your-jwt-secret-key-here-minimum-32-characters-long/$JWT_SECRET_KEY/" $APP_DIR/.env
    
    chown $APP_USER:$APP_USER $APP_DIR/.env
    chmod 600 $APP_DIR/.env
    
    print_warning "Generated secure keys in $APP_DIR/.env"
    print_warning "Please review and customize the configuration"
else
    print_status "Environment file already exists"
fi

# Initialize database
print_status "Initializing database..."
su - $APP_USER -c "cd $APP_DIR/server && FLASK_ENV=production DATABASE_PATH=$APP_DIR/data/workout.db ../venv/bin/python seed.py"

# Set up systemd service
print_status "Installing systemd service..."
cp deployment/systemd/workout-tracker.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable $SERVICE_NAME

# Set up nginx
print_status "Configuring nginx..."
cp deployment/nginx/workout-tracker.conf /etc/nginx/sites-available/
ln -sf /etc/nginx/sites-available/workout-tracker.conf /etc/nginx/sites-enabled/

# Remove default nginx site
if [ -f "/etc/nginx/sites-enabled/default" ]; then
    rm /etc/nginx/sites-enabled/default
fi

# Test nginx configuration
nginx -t

# Set up log rotation
print_status "Setting up log rotation..."
cat > /etc/logrotate.d/workout-tracker << EOF
$APP_DIR/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 $APP_USER $APP_USER
    postrotate
        systemctl reload $SERVICE_NAME
    endscript
}
EOF

# Set up backup script
print_status "Installing backup script..."
cat > /usr/local/bin/workout-tracker-backup << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/workout-tracker/backups"
DB_PATH="/opt/workout-tracker/data/workout.db"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/workout_backup_$DATE.sqlite"

mkdir -p $BACKUP_DIR
sqlite3 $DB_PATH ".backup $BACKUP_FILE"
gzip $BACKUP_FILE

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "workout_backup_*.sqlite.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE.gz"
EOF

chmod +x /usr/local/bin/workout-tracker-backup

# Set up daily backup cron job
echo "0 2 * * * root /usr/local/bin/workout-tracker-backup" > /etc/cron.d/workout-tracker-backup

# Set correct permissions
print_status "Setting file permissions..."
chown -R $APP_USER:$APP_USER $APP_DIR
chmod -R 755 $APP_DIR
chmod 700 $APP_DIR/data
chmod 600 $APP_DIR/.env

# Start services
print_status "Starting services..."
systemctl start $SERVICE_NAME
systemctl restart nginx

# Check service status
if systemctl is-active --quiet $SERVICE_NAME; then
    print_status "✅ Workout Tracker service is running"
else
    print_error "❌ Workout Tracker service failed to start"
    systemctl status $SERVICE_NAME
    exit 1
fi

if systemctl is-active --quiet nginx; then
    print_status "✅ Nginx is running"
else
    print_error "❌ Nginx failed to start"
    systemctl status nginx
    exit 1
fi

print_status "🎉 Installation completed successfully!"
echo
print_status "Next steps:"
echo "1. Configure your domain/IP in nginx config: $APP_DIR/deployment/nginx/workout-tracker.conf"
echo "2. Set up SSL certificate (recommended: certbot for Let's Encrypt)"

echo "3. Test the application at http://your-server-ip"
echo
print_status "Default test credentials:"
echo "Username: testuser"
echo "Password: password123"
echo
print_status "Service management commands:"
echo "• systemctl status $SERVICE_NAME"
echo "• systemctl restart $SERVICE_NAME"
echo "• systemctl stop $SERVICE_NAME"
echo "• journalctl -u $SERVICE_NAME -f"
