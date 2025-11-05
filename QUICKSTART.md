# Quick Start Guide

Get your Proxmox Batch Processor up and running in 5 minutes!

## Prerequisites

- Proxmox VE 9.0+ cluster running
- Anthropic API key ([Get one here](https://console.anthropic.com/))
- LXC container or Docker environment

## Fast Track: Ubuntu LXC (Recommended)

### 1. Create LXC Container

From your Proxmox host:
```bash
pct create 101 local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst \
  --hostname proxmox-batch \
  --memory 2048 \
  --cores 2 \
  --net0 name=eth0,bridge=vmbr0,ip=dhcp \
  --storage local-lvm \
  --rootfs 10

pct start 101
pct enter 101
```

### 2. Install Application

```bash
# Install git
apt-get update && apt-get install -y git

# Clone repository
cd /root
git clone https://github.com/YOUR_USERNAME/proxmox_batch.git
cd proxmox_batch

# Run installation
chmod +x deployment/install-ubuntu.sh
./deployment/install-ubuntu.sh
```

### 3. Configure

Edit configuration file:
```bash
nano /opt/proxmox-batch/.env
```

Minimum required settings:
```env
PROXMOX_HOST=your-proxmox-host.example.com
PROXMOX_USER=root@pam
PROXMOX_PASSWORD=your-password
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

### 4. Start Service

```bash
systemctl start proxmox-batch
systemctl status proxmox-batch
```

### 5. Access Web UI

```
http://YOUR_LXC_IP:8000/app
```

## Fast Track: Docker

### 1. Clone and Configure

```bash
git clone https://github.com/YOUR_USERNAME/proxmox_batch.git
cd proxmox_batch

# Configure
cp .env.example .env
nano .env  # Edit with your settings
```

### 2. Start with Docker Compose

```bash
cd deployment
docker-compose up -d
```

### 3. Access

```
http://localhost:8000/app
```

## First Analysis

1. Open web dashboard
2. Verify connection status (green indicators)
3. Review cluster overview
4. Click "Start Batch Analysis"
5. Monitor progress
6. Download results when complete

## Verify Installation

Check service health:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "proxmox_connected": true,
  "claude_initialized": true
}
```

## Getting Your Anthropic API Key

1. Visit [Anthropic Console](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to API Keys
4. Create new key
5. Copy and paste into `.env` file

## Getting Proxmox API Token (Recommended)

For better security than passwords:

1. Login to Proxmox web interface
2. Datacenter → Permissions → API Tokens
3. Add new token:
   - User: `root@pam`
   - Token ID: `batch-processor`
   - Uncheck "Privilege Separation"
4. Copy token and update `.env`:
   ```env
   PROXMOX_TOKEN_NAME=batch-processor
   PROXMOX_TOKEN_VALUE=your-token-here
   # Comment out PROXMOX_PASSWORD
   ```

## Troubleshooting

### Can't connect to Proxmox?

Test connectivity:
```bash
curl -k https://YOUR_PROXMOX_HOST:8006/api2/json
```

### Service won't start?

Check logs:
```bash
# Ubuntu
journalctl -u proxmox-batch -f

# Alpine
tail -f /var/log/messages

# Docker
docker logs proxmox-batch-processor
```

### Web UI not loading?

1. Verify service is running
2. Check firewall rules
3. Ensure port 8000 is accessible
4. Try accessing from LXC container:
   ```bash
   curl http://localhost:8000/health
   ```

## What's Next?

- Read the full [README.md](README.md) for detailed documentation
- Customize analysis settings in `.env`
- Set up scheduled analyses
- Explore the generated Terraform and Ansible templates

## Support

- 📚 Documentation: See [README.md](README.md)
- 🐛 Issues: GitHub Issues
- 💡 Feature Requests: GitHub Discussions

---

**Pro Tip**: Start with a small test run on a few VMs to estimate costs before analyzing your entire infrastructure!
