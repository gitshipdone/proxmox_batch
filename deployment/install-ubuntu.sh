#!/bin/bash
# Installation script for Ubuntu/Debian LXC

set -e

echo "=========================================="
echo "Proxmox Batch Processor - Ubuntu Setup"
echo "=========================================="

# Update package index
echo "[1/8] Updating package index..."
apt-get update

# Install Python and dependencies
echo "[2/8] Installing Python and dependencies..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    gcc \
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

# Create virtual environment
echo "[5/8] Creating Python virtual environment..."
python3 -m venv /opt/proxmox-batch/venv

# Install Python dependencies
echo "[6/8] Installing Python dependencies..."
/opt/proxmox-batch/venv/bin/pip install --upgrade pip
/opt/proxmox-batch/venv/bin/pip install -r /opt/proxmox-batch/backend/requirements.txt

# Create environment file
echo "[7/8] Creating environment file..."
if [ ! -f "/opt/proxmox-batch/.env" ]; then
    cp /opt/proxmox-batch/.env.example /opt/proxmox-batch/.env
    echo "Please edit /opt/proxmox-batch/.env with your configuration"
fi

# Create systemd service
echo "[8/8] Creating systemd service..."
cat > /etc/systemd/system/proxmox-batch.service << 'EOF'
[Unit]
Description=Proxmox Batch Processor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/proxmox-batch/backend
Environment="PATH=/opt/proxmox-batch/venv/bin"
ExecStart=/opt/proxmox-batch/venv/bin/python main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
systemctl daemon-reload

# Create output directories
mkdir -p /opt/proxmox-batch/backend/output
mkdir -p /opt/proxmox-batch/backend/data

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit configuration: nano /opt/proxmox-batch/.env"
echo "2. Start the service: systemctl start proxmox-batch"
echo "3. Enable on boot: systemctl enable proxmox-batch"
echo "4. Access the web UI at: http://YOUR_IP:8000/app"
echo ""
echo "View logs: journalctl -u proxmox-batch -f"
echo "Check status: systemctl status proxmox-batch"
echo "=========================================="
