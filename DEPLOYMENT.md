# 🏋️ Workout Tracker PWA - Production Deployment Guide

This guide covers deploying the Workout Tracker PWA in production using LXC containers on Proxmox with Cloudflare Tunnels.

## Table of Contents

1. [LXC Container Setup on Proxmox](#lxc-container-setup-on-proxmox)
2. [Application Installation](#application-installation)
3. [Cloudflare Tunnel Configuration](#cloudflare-tunnel-configuration)
4. [SSL/HTTPS Setup](#ssl-https-setup)
5. [Monitoring and Maintenance](#monitoring-and-maintenance)
6. [Backup and Recovery](#backup-and-recovery)
7. [Docker Deployment (Alternative)](#docker-deployment-alternative)

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

### Option 1: Automated Installation (Recommended)

1. **Download the application:**
   ```bash
   cd /tmp
   wget https://github.com/your-repo/workout-tracker/archive/main.zip
   unzip main.zip
   cd workout-tracker-main
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

### Option 2: Manual Installation

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
   
   # Initialize database
   cd server && python seed.py && cd ..
   
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

## Cloudflare Tunnel Configuration

### 1. Set up Cloudflare Tunnel

```bash
# Run the Cloudflare setup script
./deployment/cloudflare/setup-tunnel.sh
```

### 2. Manual Cloudflare Configuration

1. **Create Tunnel in Cloudflare Dashboard:**
   - Go to [Cloudflare Zero Trust](https://dash.cloudflare.com/)
   - Navigate to **Access > Tunnels**
   - Click **Create a tunnel**
   - Choose **Cloudflared**
   - Name your tunnel: `workout-tracker`
   - Note the **Tunnel ID**

2. **Download Credentials:**
   - Download the JSON credentials file
   - Save as `/etc/cloudflared/YOUR_TUNNEL_ID.json`
   - Set proper permissions:
     ```bash
     chown cloudflared:cloudflared /etc/cloudflared/YOUR_TUNNEL_ID.json
     chmod 600 /etc/cloudflared/YOUR_TUNNEL_ID.json
     ```

3. **Configure Tunnel:**
   ```bash
   # Copy and edit tunnel configuration
   cp deployment/cloudflare/tunnel-config.yml /etc/cloudflared/config.yml
   nano /etc/cloudflared/config.yml
   
   # Update with your tunnel ID and domain
   ```

4. **Start Cloudflare Tunnel:**
   ```bash
   systemctl enable cloudflared
   systemctl start cloudflared
   systemctl status cloudflared
   ```

### 3. DNS Configuration

In your Cloudflare DNS settings, create CNAME records:

- **Name:** `workout-tracker` (or subdomain of choice)
- **Target:** `YOUR_TUNNEL_ID.cfargotunnel.com`
- **Proxied:** Yes (orange cloud)

## SSL/HTTPS Setup

### Option 1: Cloudflare Tunnel (Automatic SSL)

When using Cloudflare Tunnels, SSL is automatically handled by Cloudflare.

### Option 2: Let's Encrypt with Certbot

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
systemctl status workout-tracker nginx cloudflared

# View logs
journalctl -u workout-tracker -f
journalctl -u nginx -f
journalctl -u cloudflared -f
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
echo "Cloudflare Tunnel Status:"
systemctl is-active cloudflared

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

## Docker Deployment (Alternative)

If you prefer Docker deployment:

### 1. Install Docker

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

### 2. Deploy with Docker Compose

```bash
# Clone repository
git clone https://github.com/your-repo/workout-tracker.git
cd workout-tracker

# Set environment variables
cp .env.example .env
nano .env

# Start services
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f
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
- Check Cloudflare tunnel status in dashboard

## Next Steps

After successful deployment:
1. Test all features (login, templates, workouts, history)
2. Set up monitoring alerts
3. Configure backup verification
4. Document your specific configuration
5. Train users on the new system
