# Deployment Guide - Workout Tracker PWA

Complete production deployment guide for LXC containers on Proxmox, Docker, and traditional VPS setups.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Security Configuration](#security-configuration)
3. [LXC Container Setup on Proxmox](#lxc-container-setup-on-proxmox)
4. [Docker Deployment](#docker-deployment)
5. [Traditional VPS Deployment](#traditional-vps-deployment)
6. [SSL/HTTPS Setup](#ssl-https-setup)
7. [Monitoring and Maintenance](#monitoring-and-maintenance)
8. [Backup and Recovery](#backup-and-recovery)

## Quick Start

### Automated Setup (Recommended)
```bash
# 1. Generate secure configuration
python3 scripts/generate-secrets.py

# 2. Deploy with Docker
docker-compose up -d

# 3. Access your application
# Check logs: docker-compose logs -f
# Admin credentials displayed during first startup
```

### Manual Setup
```bash
# 1. Set required environment variables
export SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
export JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
export CORS_ORIGINS="https://yourdomain.com"
export FLASK_ENV="production"

# 2. Initialize and start
cd server && python seed.py && python app.py
```

## Security Configuration

### 🚨 Critical Security Updates

#### 1. Secure Secret Management

**What was fixed:** Hard-coded default secrets that could compromise production deployments.

**New behavior:**
- Application **will not start** with default or weak secrets
- Secrets must be at least 32 characters long
- Clear error messages guide proper configuration

**Setup:**

```bash
# Option 1: Use the secret generator script
python3 scripts/generate-secrets.py

# Option 2: Generate manually
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"
```

#### 2. CORS Security Configuration

**What was fixed:** Permissive CORS allowing any origin to make authenticated requests.

**New behavior:**
- CORS origins must be explicitly configured
- Supports multiple domains for development/staging/production
- Credentials support configurable

**Configuration:**

```bash
# Production - Restrict to your domains only
export CORS_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"

# Development - Include localhost for testing
export CORS_ORIGINS="http://localhost:3000,http://localhost:8080,https://yourdomain.com"

# Credentials (usually false for JWT bearer tokens)
export CORS_SUPPORTS_CREDENTIALS="false"
```

#### 3. JWT Token Security

**What was fixed:** Long-lived tokens (30 days) with no revocation mechanism.

**New behavior:**
- Default token expiry: 15 minutes (configurable)
- Encourages implementing refresh token flow
- Configurable via environment variables

**Configuration:**

```bash
# Set token expiry in minutes
export JWT_EXPIRES_MINUTES="15"  # 15 minutes (recommended)
export JWT_EXPIRES_MINUTES="60"  # 1 hour (if needed)
```

#### 4. Access Control Validation

**What was fixed:** Insecure Direct Object Reference allowing users to access other users' data.

**New behavior:**
- All template exercise references validated against user ownership
- Clear error messages for unauthorized access attempts
- Prevents cross-tenant data leakage

#### 5. Production Security Enforcement

**What was fixed:** Debug mode could be accidentally enabled in production.

**New behavior:**
- Production config validates environment settings
- Prevents debug mode in production environments
- Clear error messages for misconfigurations

### 📋 Environment Variable Reference

#### Required Variables (Production)

```bash
# Cryptographic secrets (32+ characters each)
SECRET_KEY="your-super-secret-key-here-minimum-32-characters-long"
JWT_SECRET_KEY="your-jwt-secret-key-here-minimum-32-characters-long"

# CORS security
CORS_ORIGINS="https://yourdomain.com"

# Environment
FLASK_ENV="production"
```

#### Optional Variables

```bash
# JWT configuration
JWT_EXPIRES_MINUTES="15"                    # Token expiry (default: 15 minutes)

# CORS configuration
CORS_SUPPORTS_CREDENTIALS="false"           # Enable credentials (default: false)

# Database
DATABASE_PATH="/opt/workout-tracker/data/workout.db"  # Custom DB path

# Server
PORT="8080"                                 # Server port (default: 8080)
```

#### Development Variables

```bash
# Skip secret validation in development only
SKIP_SECRET_VALIDATION="true"

# Development CORS (includes localhost)
CORS_ORIGINS="http://localhost:3000,http://localhost:8080,http://127.0.0.1:8080"
```

### 🔒 Security Validation

#### Test Configuration

```bash
# Test that default secrets are rejected
cd server
python3 -c "
import os
os.environ['SECRET_KEY'] = 'dev-secret-key-change-in-production'
from config import config
config['production']()
"
# Should exit with error

# Test valid configuration
export SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
export JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
export CORS_ORIGINS="https://yourdomain.com"
python3 -c "from config import config; print('✅ Valid config'); config['production']()"
```

#### Verify CORS Configuration

```bash
# Test CORS restrictions
curl -H "Origin: https://evil.com" http://localhost:8080/api/templates
# Should not include Access-Control-Allow-Origin header

curl -H "Origin: https://yourdomain.com" http://localhost:8080/api/templates  
# Should include Access-Control-Allow-Origin header
```

### 🚀 Deployment Security Checklist

#### Before Production Deployment

- [ ] Generate secure secrets using `scripts/generate-secrets.py`
- [ ] Set `CORS_ORIGINS` to your actual domain(s)
- [ ] Set `FLASK_ENV=production`
- [ ] Verify secrets are at least 32 characters long
- [ ] Test that application starts without errors
- [ ] Verify CORS is working correctly
- [ ] Ensure `.env` file is not committed to git
- [ ] Set proper file permissions: `chmod 600 .env`

#### Production Environment Variables

```bash
# Required for production
export SECRET_KEY="your-production-secret-key-32plus-chars"
export JWT_SECRET_KEY="your-production-jwt-secret-32plus-chars"
export CORS_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"
export FLASK_ENV="production"
export JWT_EXPIRES_MINUTES="15"
export DATABASE_PATH="/opt/workout-tracker/data/workout.db"
```

### 🔄 Secret Rotation

For production secret rotation:

```bash
# Generate new secrets
python3 scripts/generate-secrets.py

# Update environment variables
# Restart application
docker-compose restart workout-tracker
```

### ⚠️ Security Notes

1. **Never use default secrets in production**
2. **Keep CORS_ORIGINS restricted to your domains**
3. **Use HTTPS-only domains in production**
4. **Monitor for authentication failures**
5. **Rotate secrets regularly**
6. **Keep `.env` files secure and out of git**

#### Known Security Considerations

**JWT Token Storage:** Currently using `localStorage` for JWT tokens, which is vulnerable to XSS attacks. Consider implementing:
- Refresh token flow with short-lived access tokens (current: 15 minutes)
- Content Security Policy (CSP) headers to prevent XSS
- Regular security scans for XSS vulnerabilities
- Future migration to `httpOnly` cookies with CSRF protection

## LXC Container Setup on Proxmox

### 1. Create LXC Container

In Proxmox web interface:

1. **Click "Create CT"**
2. **General Tab:**
   - CT ID: 100 (or next available)
   - Hostname: `workout-tracker`
   - Password: Set a secure root password
   - SSH Public Key: (Optional but recommended)

3. **Template Tab:**
   - Storage: local
   - Template: `ubuntu-22.04-standard` (download if not available)

4. **Disks Tab:**
   - Storage: local-lvm
   - Disk size: 8 GB (minimum)

5. **CPU Tab:**
   - Cores: 2

6. **Memory Tab:**
   - Memory: 1024 MB
   - Swap: 512 MB

7. **Network Tab:**
   - Bridge: vmbr0
   - Static IP: Configure as needed (e.g., 192.168.1.100/24)
   - Gateway: Your network gateway

8. **DNS Tab:**
   - DNS domain: your.domain.com
   - DNS servers: 1.1.1.1, 8.8.8.8

### 2. Start and Configure Container

```bash
# Start the container
pct start 100

# Enter the container
pct enter 100

# Update the system
apt update && apt upgrade -y
```

### 3. Configure Network (if needed)

```bash
# Edit network configuration
nano /etc/netplan/10-lxc.yaml

# Example configuration:
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: false
      addresses:
        - 192.168.1.100/24
      gateway4: 192.168.1.1
      nameservers:
        addresses:
          - 1.1.1.1
          - 8.8.8.8

# Apply network configuration
netplan apply
```

## Application Installation

### Option 1: Automated LXC Installation (Recommended)

**Run on Proxmox host to create and configure everything automatically:**

```bash
# Download and run the Proxmox LXC helper script
wget https://github.com/steviebd/webserver-code/raw/main/deployment/scripts/proxmox-lxc-install.sh
chmod +x proxmox-lxc-install.sh

# Basic installation with DHCP
./proxmox-lxc-install.sh --password mypassword

# Installation with static IP
./proxmox-lxc-install.sh --password mypassword --ip 192.168.1.100/24 --gateway 192.168.1.1

# Full customization
./proxmox-lxc-install.sh \
  --ct-id 100 \
  --hostname workout-tracker \
  --password mypassword \
  --ssh-key "$(cat ~/.ssh/id_rsa.pub)" \
  --ip 192.168.1.100/24 \
  --gateway 192.168.1.1 \
  --cores 4 \
  --memory 2048 \
  --disk-size 16
```

This script will:
- Create the LXC container with specified configuration
- Download Ubuntu 22.04 template if needed
- Install and configure the Workout Tracker application
- Set up nginx, systemd service, and all dependencies
- Provide ready-to-use application

### Option 2: Manual Installation Inside Existing Container

1. **Download the application:**
   ```bash
   cd /tmp
   wget https://github.com/steviebd/workout-tracker/archive/refs/heads/mvp.zip
   unzip mvp.zip
   cd workout-tracker-mvp
   ```

2. **Run the installation script:**
   ```bash
   chmod +x deployment/scripts/install.sh
   ./deployment/scripts/install.sh
   ```

3. **The script will:**
   - Install all dependencies
   - Create application user and directories
   - Set up Python virtual environment
   - Configure systemd service
   - Set up nginx
   - Initialize database with test data
   - Configure log rotation and backups

### Option 3: Manual Installation

1. **Install dependencies:**
   ```bash
   apt install -y python3 python3-pip python3-venv nginx sqlite3 curl wget
   ```

2. **Create application user:**
   ```bash
   useradd --system --home-dir /opt/workout-tracker --shell /bin/bash --create-home workout-tracker
   ```

3. **Set up application:**
   ```bash
   # Copy files
   cp -r . /opt/workout-tracker/
   cd /opt/workout-tracker
   
   # Set up Python environment
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements-production.txt
   
   # Configure environment
   cp .env.example .env
   # Edit .env with your values
   nano .env
   
   # Initialize database with admin user
   cd server && python seed.py && cd ..
    # The script will output admin credentials - save them securely!
   
   # Set permissions
   chown -R workout-tracker:workout-tracker /opt/workout-tracker
   ```

4. **Configure services:**
   ```bash
   # Install systemd service
   cp deployment/systemd/workout-tracker.service /etc/systemd/system/
   systemctl daemon-reload
   systemctl enable workout-tracker
   systemctl start workout-tracker
   
   # Configure nginx
   cp deployment/nginx/workout-tracker.conf /etc/nginx/sites-available/
   ln -s /etc/nginx/sites-available/workout-tracker.conf /etc/nginx/sites-enabled/
   rm /etc/nginx/sites-enabled/default
   systemctl restart nginx
   ```

### 3. Verify Installation

```bash
# Check service status
systemctl status workout-tracker
systemctl status nginx

# Test the application
curl http://localhost/health

# Check logs
journalctl -u workout-tracker -f
```

## SSL/HTTPS Setup

### Let's Encrypt with Certbot

```bash
# Install certbot
apt install certbot python3-certbot-nginx

# Get SSL certificate
certbot --nginx -d workout-tracker.yourdomain.com

# Test auto-renewal
certbot renew --dry-run
```

## Monitoring and Maintenance

### 1. Service Status Monitoring

```bash
# Check all services
systemctl status workout-tracker nginx

# View logs
journalctl -u workout-tracker -f
journalctl -u nginx -f
```

### 2. Performance Monitoring

Create `/usr/local/bin/workout-tracker-monitor`:

```bash
#!/bin/bash
# Simple monitoring script

echo "=== Workout Tracker Status $(date) ==="
echo "Application Status:"
systemctl is-active workout-tracker
echo "Nginx Status:"
systemctl is-active nginx

echo "=== Resource Usage ==="
echo "Memory Usage:"
free -h
echo "Disk Usage:"
df -h /opt/workout-tracker

echo "=== Application Health ==="
curl -s http://localhost/health || echo "Health check failed"

echo "=== Recent Errors ==="
journalctl -u workout-tracker --since "1 hour ago" -p err --no-pager
```

### 3. Automated Monitoring with Cron

```bash
# Add to crontab
echo "*/5 * * * * root /usr/local/bin/workout-tracker-monitor > /var/log/workout-tracker-monitor.log 2>&1" >> /etc/crontab
```

## Backup and Recovery

### 1. Database Backup

The installation script creates automatic daily backups. Manual backup:

```bash
# Manual backup
/usr/local/bin/workout-tracker-backup

# List backups
ls -la /opt/workout-tracker/backups/
```

### 2. Full System Backup

```bash
# Create backup script
cat > /usr/local/bin/workout-tracker-full-backup << 'EOF'
#!/bin/bash
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/workout-tracker/backups/full_backup_$BACKUP_DATE"

mkdir -p $BACKUP_DIR

# Backup database
cp /opt/workout-tracker/data/workout.db $BACKUP_DIR/

# Backup configuration
cp /opt/workout-tracker/.env $BACKUP_DIR/

# Backup nginx config
cp /etc/nginx/sites-available/workout-tracker.conf $BACKUP_DIR/

# Backup systemd service
cp /etc/systemd/system/workout-tracker.service $BACKUP_DIR/

# Create archive
tar -czf /opt/workout-tracker/backups/full_backup_$BACKUP_DATE.tar.gz -C /opt/workout-tracker/backups full_backup_$BACKUP_DATE
rm -rf $BACKUP_DIR

echo "Full backup completed: full_backup_$BACKUP_DATE.tar.gz"
EOF

chmod +x /usr/local/bin/workout-tracker-full-backup
```

### 3. Recovery Procedure

```bash
# Stop services
systemctl stop workout-tracker nginx

# Restore database
cp backup_file.sqlite /opt/workout-tracker/data/workout.db
chown workout-tracker:workout-tracker /opt/workout-tracker/data/workout.db

# Restart services
systemctl start workout-tracker nginx
```

## Docker Deployment

### 1. Install Docker
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

### 2. Automated Docker Setup
```bash
# Generate configuration automatically
python3 scripts/generate-secrets.py

# Deploy
docker-compose up -d

# Monitor
docker-compose logs -f
```

### 3. Manual Docker Setup
```bash
# Create environment file
cat > .env << EOF
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
CORS_ORIGINS=https://yourdomain.com
JWT_EXPIRES_MINUTES=15
CORS_SUPPORTS_CREDENTIALS=false
FLASK_ENV=production
EOF

chmod 600 .env
docker-compose up -d
```

## Traditional VPS Deployment

### Ubuntu/Debian Server
```bash
# Install dependencies
sudo apt update && sudo apt install -y python3 python3-pip python3-venv nginx sqlite3

# Create application user
sudo useradd --system --home-dir /opt/workout-tracker --create-home workout-tracker

# Install application
sudo -u workout-tracker git clone https://github.com/your-repo/workout-tracker.git /opt/workout-tracker
cd /opt/workout-tracker

# Run installation script
sudo ./deployment/scripts/install.sh
```

### CentOS/RHEL
```bash
# Install dependencies
sudo yum install -y python3 python3-pip nginx sqlite

# Follow Ubuntu steps above
```

## Role-Based Authentication System

The Workout Tracker now includes a comprehensive role-based authentication system with the following features:

### 👑 Administrator Capabilities

Administrators can:
- Create, edit, and delete user accounts
- Assign roles (Administrator or User)
- Reset user passwords
- Manage all system users through the Settings tab

### 🔐 Security Features

1. **Secure Password Reset**: Users can reset passwords via email with single-use tokens that expire in 1 hour
2. **Forced Password Changes**: New users and password resets require password changes on first login
3. **SMTP Email Integration**: Configurable email service for password resets and user notifications

### ⚙️ Email Configuration

For password reset functionality, configure SMTP settings:

```bash
# Email service configuration
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USERNAME="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
export SMTP_USE_TLS="true"
export FROM_EMAIL="noreply@yourdomain.com"
export APP_URL="https://yourdomain.com"
```

### 🚀 Initial Admin Setup

When you run `python seed.py`, the script will:

1. Create an admin user with username: `admin`
2. Generate a secure temporary password
3. Display the credentials (save them securely!)
4. Force the admin to change the password on first login

**Example output:**
```
Created admin user with ID: 1
Admin username: admin
Admin temporary password: A9x7K3m2P8z!
IMPORTANT: The admin must change their password on first login!
```

### 📧 User Management Workflow

1. **Admin creates user**: Admin sets username, email, role, and temporary password
2. **Email notification**: User receives email with login credentials
3. **First login**: User must change password before accessing the system
4. **Password reset**: Users can reset forgotten passwords via email

### 🛡️ Security Best Practices

- **Regular password rotation**: Admins should regularly reset user passwords
- **Email security**: Use app-specific passwords for email accounts
- **Role separation**: Only create admin accounts when necessary
- **Audit trail**: All authentication events are logged for security monitoring

### 🔧 Email Service Setup Examples

#### Gmail Configuration
```bash
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USERNAME="admin@yourdomain.com"
export SMTP_PASSWORD="your-app-specific-password"
export SMTP_USE_TLS="true"
```

#### SendGrid Configuration
```bash
export SMTP_SERVER="smtp.sendgrid.net"
export SMTP_PORT="587"
export SMTP_USERNAME="apikey"
export SMTP_PASSWORD="your-sendgrid-api-key"
export SMTP_USE_TLS="true"
```

#### Local SMTP (for testing)
```bash
export SMTP_SERVER="localhost"
export SMTP_PORT="25"
export SMTP_USE_TLS="false"
# No username/password needed for local SMTP
```

## Security Considerations

### 1. Firewall Configuration

```bash
# Install UFW
apt install ufw

# Configure firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80
ufw allow 443
ufw enable
```

### 2. Fail2Ban Setup

```bash
# Install fail2ban
apt install fail2ban

# Configure for nginx
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[nginx-http-auth]
enabled = true

[nginx-limit-req]
enabled = true
EOF

systemctl restart fail2ban
```

### 3. Regular Updates

```bash
# Create update script
cat > /usr/local/bin/workout-tracker-update << 'EOF'
#!/bin/bash
echo "Updating system packages..."
apt update && apt upgrade -y

echo "Restarting services..."
systemctl restart workout-tracker nginx

echo "Update completed"
EOF

chmod +x /usr/local/bin/workout-tracker-update

# Schedule monthly updates
echo "0 2 1 * * root /usr/local/bin/workout-tracker-update" >> /etc/crontab
```

## Troubleshooting

### Common Issues

1. **Service won't start:**
   ```bash
   journalctl -u workout-tracker -n 50
   ```

2. **Permission errors:**
   ```bash
   chown -R workout-tracker:workout-tracker /opt/workout-tracker
   ```

3. **Database issues:**
   ```bash
   cd /opt/workout-tracker/server
   sudo -u workout-tracker python seed.py
   ```

4. **Nginx configuration errors:**
   ```bash
   nginx -t
   ```

### Security-Related Issues

1. **Application won't start with security error:**
   ```bash
   ❌ SECURITY ERROR: SECRET_KEY not set or using default value!
   ```
   **Solution:** Set a proper SECRET_KEY environment variable with 32+ characters.

2. **CORS errors in browser:**
   ```
   Access to fetch at 'http://api.example.com' from origin 'https://app.example.com' has been blocked by CORS policy
   ```
   **Solution:** Add your frontend domain to CORS_ORIGINS environment variable.

3. **JWT tokens expire too quickly:**
   **Solution:** Increase JWT_EXPIRES_MINUTES or implement refresh token flow.

### Performance Tuning

For high-traffic deployments:

1. **Increase Gunicorn workers:**
   ```bash
   # Edit systemd service
   nano /etc/systemd/system/workout-tracker.service
   # Change --workers 2 to --workers 4
   systemctl daemon-reload
   systemctl restart workout-tracker
   ```

2. **Configure nginx caching:**
   ```bash
   # Add to nginx config
   proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=app_cache:10m;
   ```

## Support

For issues and questions:
- Check the logs: `journalctl -u workout-tracker -f`
- Verify health endpoint: `curl http://localhost/health`
- Review configuration files


## Next Steps

After successful deployment:
1. Test all features (login, templates, workouts, history)
2. Set up monitoring alerts
3. Configure backup verification
4. Document your specific configuration
5. Train users on the new system
