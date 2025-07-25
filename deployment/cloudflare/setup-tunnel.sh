#!/bin/bash
set -e

# Cloudflare Tunnel Setup Script
# Run this script after setting up the main application

echo "☁️ Setting up Cloudflare Tunnel..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_header() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root"
   exit 1
fi

# Download and install cloudflared
print_header "Installing cloudflared..."
if ! command -v cloudflared &> /dev/null; then
    # Detect architecture
    ARCH=$(uname -m)
    case $ARCH in
        x86_64)
            CLOUDFLARED_ARCH="amd64"
            ;;
        aarch64|arm64)
            CLOUDFLARED_ARCH="arm64"
            ;;
        armv7l)
            CLOUDFLARED_ARCH="arm"
            ;;
        *)
            print_error "Unsupported architecture: $ARCH"
            exit 1
            ;;
    esac
    
    wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${CLOUDFLARED_ARCH}.deb
    dpkg -i cloudflared-linux-${CLOUDFLARED_ARCH}.deb
    rm cloudflared-linux-${CLOUDFLARED_ARCH}.deb
    
    print_status "cloudflared installed successfully"
else
    print_status "cloudflared is already installed"
fi

# Create cloudflared user
if ! id "cloudflared" &>/dev/null; then
    print_status "Creating cloudflared user..."
    useradd --system --home /var/lib/cloudflared --shell /bin/false cloudflared
    mkdir -p /var/lib/cloudflared
    chown cloudflared:cloudflared /var/lib/cloudflared
fi

# Create config directory
mkdir -p /etc/cloudflared
chown cloudflared:cloudflared /etc/cloudflared

print_header "Manual Configuration Required"
echo
print_warning "To complete the Cloudflare Tunnel setup, you need to:"
echo
echo "1. Log in to Cloudflare Dashboard (https://dash.cloudflare.com/)"
echo "2. Go to Zero Trust > Access > Tunnels"
echo "3. Create a new tunnel and note the tunnel ID"
echo "4. Download the credentials file (JSON)"
echo "5. Save the credentials file as: /etc/cloudflared/YOUR_TUNNEL_ID.json"
echo
echo "6. Create your tunnel configuration:"
echo "   cp deployment/cloudflare/tunnel-config.yml /etc/cloudflare/config.yml"
echo "   # Edit the config.yml file with your tunnel ID and domain"
echo
echo "7. Set up the systemd service:"

cat > /etc/systemd/system/cloudflared.service << 'EOF'
[Unit]
Description=Cloudflare Tunnel
After=network.target

[Service]
TimeoutStartSec=0
Type=notify
ExecStart=/usr/local/bin/cloudflared tunnel --config /etc/cloudflared/config.yml run
Restart=on-failure
RestartSec=5s
User=cloudflared
Group=cloudflared

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload

print_status "Systemd service created"
echo
print_header "After manual configuration, run:"
echo "sudo chown cloudflared:cloudflared /etc/cloudflared/YOUR_TUNNEL_ID.json"
echo "sudo chmod 600 /etc/cloudflared/YOUR_TUNNEL_ID.json"
echo "sudo systemctl enable cloudflared"
echo "sudo systemctl start cloudflared"
echo "sudo systemctl status cloudflared"
echo
print_header "DNS Configuration"
echo "In your Cloudflare DNS settings, create CNAME records:"
echo "workout-tracker.yourdomain.com -> YOUR_TUNNEL_ID.cfargotunnel.com"
echo
print_status "Cloudflare Tunnel setup preparation complete!"
