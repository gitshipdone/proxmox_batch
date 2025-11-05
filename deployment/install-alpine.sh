#!/bin/sh
# Installation script for Alpine Linux LXC

set -e

echo "=========================================="
echo "Proxmox Batch Processor - Alpine Setup"
echo "=========================================="

# Update package index
echo "[1/8] Updating package index..."
apk update

# Install Python and pip
echo "[2/8] Installing Python and dependencies..."
apk add --no-cache \
    python3 \
    py3-pip \
    python3-dev \
    gcc \
    musl-dev \
    linux-headers \
    git \
    curl

# Create application directory
echo "[3/8] Creating application directory..."
mkdir -p /opt/proxmox-batch
cd /opt/proxmox-batch

# Clone or copy application files
echo "[4/8] Setting up application files..."
# If running from the repo directory:
if [ -d "/root/proxmox_batch" ]; then
    cp -r /root/proxmox_batch/* /opt/proxmox-batch/
else
    echo "Please copy the application files to /opt/proxmox-batch"
    exit 1
fi

# Install Python dependencies
echo "[5/8] Installing Python dependencies..."
cd /opt/proxmox-batch/backend
pip3 install --no-cache-dir -r requirements.txt

# Create environment file
echo "[6/8] Creating environment file..."
if [ ! -f "/opt/proxmox-batch/.env" ]; then
    cp /opt/proxmox-batch/.env.example /opt/proxmox-batch/.env
    echo "Please edit /opt/proxmox-batch/.env with your configuration"
fi

# Create systemd service (if using OpenRC, adapt accordingly)
echo "[7/8] Creating service..."
cat > /etc/init.d/proxmox-batch << 'EOF'
#!/sbin/openrc-run

name="proxmox-batch"
description="Proxmox Batch Processor"

command="/usr/bin/python3"
command_args="/opt/proxmox-batch/backend/main.py"
command_background="yes"
pidfile="/run/${RC_SVCNAME}.pid"
directory="/opt/proxmox-batch/backend"

depend() {
    need net
}
EOF

chmod +x /etc/init.d/proxmox-batch

# Create output directories
echo "[8/8] Creating output directories..."
mkdir -p /opt/proxmox-batch/backend/output
mkdir -p /opt/proxmox-batch/backend/data

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit configuration: nano /opt/proxmox-batch/.env"
echo "2. Start the service: rc-service proxmox-batch start"
echo "3. Enable on boot: rc-update add proxmox-batch"
echo "4. Access the web UI at: http://YOUR_IP:8000/app"
echo ""
echo "View logs: tail -f /var/log/proxmox-batch.log"
echo "=========================================="
