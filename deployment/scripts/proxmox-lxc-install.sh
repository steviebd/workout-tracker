#!/bin/bash
set -e

# Proxmox LXC Helper Script for Workout Tracker PWA
# Run this script on your Proxmox host to automatically create and configure an LXC container

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
    echo -e "${BLUE}[PROXMOX]${NC} $1"
}

# Default configuration
CT_ID=""
CT_HOSTNAME="workout-tracker"
CT_PASSWORD=""
CT_SSH_KEY=""
CT_STORAGE="local-lvm"
CT_TEMPLATE_STORAGE="local"
CT_TEMPLATE="ubuntu-22.04-standard"
CT_CORES="2"
CT_MEMORY="1024"
CT_SWAP="512"
CT_DISK_SIZE="8"
CT_BRIDGE="vmbr0"
CT_IP=""
CT_GATEWAY=""
CT_DNS="1.1.1.1,8.8.8.8"
REPO_URL="https://github.com/steviebd/webserver-code"

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --ct-id ID          Container ID (auto-detect if not specified)"
    echo "  --hostname NAME     Container hostname (default: workout-tracker)"
    echo "  --password PASS     Root password (required)"
    echo "  --ssh-key KEY       SSH public key (optional)"
    echo "  --ip ADDRESS        Static IP address (e.g., 192.168.1.100/24)"
    echo "  --gateway IP        Gateway IP address"
    echo "  --dns SERVERS       DNS servers (default: 1.1.1.1,8.8.8.8)"
    echo "  --cores NUM         CPU cores (default: 2)"
    echo "  --memory MB         Memory in MB (default: 1024)"
    echo "  --disk-size GB      Disk size in GB (default: 8)"
    echo "  --storage STORAGE   Storage for container (default: local-lvm)"
    echo "  --template-storage  Storage for template (default: local)"
    echo "  --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --password mypassword --ip 192.168.1.100/24 --gateway 192.168.1.1"
    echo "  $0 --ct-id 100 --password mypass --ssh-key \"\$(cat ~/.ssh/id_rsa.pub)\""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --ct-id)
            CT_ID="$2"
            shift 2
            ;;
        --hostname)
            CT_HOSTNAME="$2"
            shift 2
            ;;
        --password)
            CT_PASSWORD="$2"
            shift 2
            ;;
        --ssh-key)
            CT_SSH_KEY="$2"
            shift 2
            ;;
        --ip)
            CT_IP="$2"
            shift 2
            ;;
        --gateway)
            CT_GATEWAY="$2"
            shift 2
            ;;
        --dns)
            CT_DNS="$2"
            shift 2
            ;;
        --cores)
            CT_CORES="$2"
            shift 2
            ;;
        --memory)
            CT_MEMORY="$2"
            shift 2
            ;;
        --disk-size)
            CT_DISK_SIZE="$2"
            shift 2
            ;;
        --storage)
            CT_STORAGE="$2"
            shift 2
            ;;
        --template-storage)
            CT_TEMPLATE_STORAGE="$2"
            shift 2
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate required parameters
if [ -z "$CT_PASSWORD" ]; then
    print_error "Password is required. Use --password option."
    show_usage
    exit 1
fi

# Auto-detect next available CT ID if not specified
if [ -z "$CT_ID" ]; then
    print_status "Auto-detecting next available container ID..."
    for i in {100..999}; do
        if ! pct status $i &>/dev/null; then
            CT_ID=$i
            break
        fi
    done
    
    if [ -z "$CT_ID" ]; then
        print_error "Could not find available container ID"
        exit 1
    fi
    
    print_status "Using container ID: $CT_ID"
fi

# Validate CT ID is available
if pct status $CT_ID &>/dev/null; then
    print_error "Container ID $CT_ID is already in use"
    exit 1
fi

print_header "🏋️ Creating Workout Tracker LXC Container"
echo
print_status "Configuration:"
echo "  Container ID: $CT_ID"
echo "  Hostname: $CT_HOSTNAME"
echo "  Cores: $CT_CORES"
echo "  Memory: ${CT_MEMORY}MB"
echo "  Disk: ${CT_DISK_SIZE}GB"
echo "  Storage: $CT_STORAGE"
echo "  Network: $CT_BRIDGE"
if [ -n "$CT_IP" ]; then
    echo "  IP: $CT_IP"
    echo "  Gateway: $CT_GATEWAY"
fi
echo "  DNS: $CT_DNS"
echo

# Check if template exists
if ! pveam list $CT_TEMPLATE_STORAGE | grep -q "$CT_TEMPLATE"; then
    print_warning "Template $CT_TEMPLATE not found in $CT_TEMPLATE_STORAGE"
    print_status "Downloading template..."
    pveam download $CT_TEMPLATE_STORAGE $CT_TEMPLATE
    
    # Wait for download to complete
    while ! pveam list $CT_TEMPLATE_STORAGE | grep -q "$CT_TEMPLATE"; do
        print_status "Waiting for template download..."
        sleep 5
    done
fi

# Prepare container creation command
CREATE_CMD="pct create $CT_ID $CT_TEMPLATE_STORAGE:vztmpl/$CT_TEMPLATE.tar.zst"
CREATE_CMD="$CREATE_CMD --hostname $CT_HOSTNAME"
CREATE_CMD="$CREATE_CMD --password $CT_PASSWORD"
CREATE_CMD="$CREATE_CMD --cores $CT_CORES"
CREATE_CMD="$CREATE_CMD --memory $CT_MEMORY"
CREATE_CMD="$CREATE_CMD --swap $CT_SWAP"
CREATE_CMD="$CREATE_CMD --rootfs $CT_STORAGE:$CT_DISK_SIZE"
CREATE_CMD="$CREATE_CMD --net0 name=eth0,bridge=$CT_BRIDGE,firewall=1"

# Add network configuration
if [ -n "$CT_IP" ]; then
    CREATE_CMD="$CREATE_CMD,ip=$CT_IP"
    if [ -n "$CT_GATEWAY" ]; then
        CREATE_CMD="$CREATE_CMD,gw=$CT_GATEWAY"
    fi
else
    CREATE_CMD="$CREATE_CMD,ip=dhcp"
fi

# Add SSH key if provided
if [ -n "$CT_SSH_KEY" ]; then
    CREATE_CMD="$CREATE_CMD --ssh-public-keys <(echo '$CT_SSH_KEY')"
fi

# Add other options
CREATE_CMD="$CREATE_CMD --nameserver $CT_DNS"
CREATE_CMD="$CREATE_CMD --onboot 1"
CREATE_CMD="$CREATE_CMD --start 1"

print_status "Creating LXC container..."
eval $CREATE_CMD

# Wait for container to start
print_status "Waiting for container to start..."
sleep 10

# Wait for container to be ready
print_status "Waiting for container to be ready..."
for i in {1..30}; do
    if pct exec $CT_ID -- systemctl is-system-running --wait &>/dev/null; then
        break
    fi
    sleep 2
done

# Update system and install basic tools
print_status "Updating system packages..."
pct exec $CT_ID -- apt update
pct exec $CT_ID -- apt upgrade -y
pct exec $CT_ID -- apt install -y curl wget unzip git

# Download and extract the application
print_status "Downloading Workout Tracker application..."
pct exec $CT_ID -- bash -c "cd /tmp && wget -O workout-tracker.zip $REPO_URL/archive/main.zip"
pct exec $CT_ID -- bash -c "cd /tmp && unzip -q workout-tracker.zip"
pct exec $CT_ID -- bash -c "cd /tmp && mv webserver-code-main workout-tracker"

# Run the installation script
print_status "Running application installation script..."
pct exec $CT_ID -- bash -c "cd /tmp/workout-tracker && chmod +x deployment/scripts/install.sh"
pct exec $CT_ID -- bash -c "cd /tmp/workout-tracker && ./deployment/scripts/install.sh"

# Clean up
print_status "Cleaning up temporary files..."
pct exec $CT_ID -- rm -rf /tmp/workout-tracker /tmp/workout-tracker.zip

# Get container IP for display
if [ -z "$CT_IP" ]; then
    CT_ACTUAL_IP=$(pct exec $CT_ID -- hostname -I | awk '{print $1}')
else
    CT_ACTUAL_IP=$(echo $CT_IP | cut -d'/' -f1)
fi

print_header "🎉 Installation completed successfully!"
echo
print_status "Container Details:"
echo "  Container ID: $CT_ID"
echo "  Hostname: $CT_HOSTNAME"
echo "  IP Address: $CT_ACTUAL_IP"
echo "  Access: http://$CT_ACTUAL_IP"
echo
print_status "Default test credentials:"
echo "  Username: testuser"
echo "  Password: password123"
echo
print_status "Management commands:"
echo "  Start container:    pct start $CT_ID"
echo "  Stop container:     pct stop $CT_ID"
echo "  Enter container:    pct enter $CT_ID"
echo "  Container console:  pct console $CT_ID"
echo
print_status "Application commands (run inside container):"
echo "  Check status:       systemctl status workout-tracker"
echo "  View logs:          journalctl -u workout-tracker -f"
echo "  Restart app:        systemctl restart workout-tracker"
echo "  Run backup:         /usr/local/bin/workout-tracker-backup"
echo
print_warning "Next steps:"
echo "1. Test the application at http://$CT_ACTUAL_IP"
echo "2. Configure SSL certificate if needed (certbot)"
echo "3. Update nginx server_name in /etc/nginx/sites-available/workout-tracker.conf"
echo "4. Set up firewall rules if required"
echo
print_status "For troubleshooting, check:"
echo "  Container status:   pct status $CT_ID"
echo "  Container logs:     pct exec $CT_ID -- journalctl -xe"
echo "  Application health: curl http://$CT_ACTUAL_IP/health"
