# Proxmox Batch Processor

**Batch-Process Your Entire Proxmox Lab Infrastructure with AI**

Like a factory assembly line where Claude AI reviews each machine, this system analyzes and documents all your VMs/LXCs from your Proxmox cluster. Get comprehensive infrastructure audits, security reviews, optimization recommendations, and Infrastructure as Code (IaC) templates—all automatically generated.

## Features

- **Comprehensive Analysis**: Deep-dive into every VM and LXC container configuration
- **Security Reviews**: Automated security assessments with actionable recommendations
- **Optimization Suggestions**: Performance and cost efficiency recommendations
- **Infrastructure as Code**: Auto-generate Terraform and Ansible templates
- **Documentation Generation**: Professional documentation for your entire infrastructure
- **Batch Processing**: Process multiple resources concurrently for efficiency
- **Web Dashboard**: Lightweight, responsive UI for monitoring and management
- **Export Capabilities**: Download all generated artifacts as organized archives

## Architecture

```
┌─────────────────────┐
│   Web Frontend      │ ← Lightweight HTML/CSS/JS Dashboard
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   FastAPI Backend   │ ← REST API Server
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    │             │
┌───▼────┐   ┌───▼────┐
│Proxmox │   │Claude  │
│  API   │   │  API   │
└────────┘   └────────┘
```

## System Requirements

### LXC Container (Recommended)
- **OS**: Alpine Linux 3.19+ or Ubuntu 22.04+
- **CPU**: 2 cores minimum, 4+ recommended
- **RAM**: 2GB minimum, 4GB+ recommended
- **Storage**: 10GB minimum (scales with output)
- **Network**: Internet access for Proxmox and Claude APIs

### Dependencies
- Python 3.11+
- Proxmox VE 9.0+ cluster
- Anthropic API key (Claude)
- Network access to Proxmox API

## Installation

### Option 1: LXC Container on Alpine Linux

1. **Create Alpine LXC container in Proxmox:**
   ```bash
   pct create 100 local:vztmpl/alpine-3.19-default_20231129_amd64.tar.xz \
     --hostname proxmox-batch \
     --memory 2048 \
     --cores 2 \
     --net0 name=eth0,bridge=vmbr0,ip=dhcp \
     --storage local-lvm \
     --rootfs 10
   ```

2. **Start container and enter:**
   ```bash
   pct start 100
   pct enter 100
   ```

3. **Clone repository:**
   ```bash
   apk add git
   cd /root
   git clone <your-repo-url> proxmox_batch
   cd proxmox_batch
   ```

4. **Run installation script:**
   ```bash
   chmod +x deployment/install-alpine.sh
   ./deployment/install-alpine.sh
   ```

5. **Configure environment:**
   ```bash
   nano /opt/proxmox-batch/.env
   ```

6. **Start service:**
   ```bash
   rc-service proxmox-batch start
   rc-update add proxmox-batch
   ```

### Option 2: LXC Container on Ubuntu

1. **Create Ubuntu LXC container in Proxmox:**
   ```bash
   pct create 101 local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst \
     --hostname proxmox-batch \
     --memory 2048 \
     --cores 2 \
     --net0 name=eth0,bridge=vmbr0,ip=dhcp \
     --storage local-lvm \
     --rootfs 10
   ```

2. **Start container and enter:**
   ```bash
   pct start 101
   pct enter 101
   ```

3. **Clone repository:**
   ```bash
   apt-get update && apt-get install -y git
   cd /root
   git clone <your-repo-url> proxmox_batch
   cd proxmox_batch
   ```

4. **Run installation script:**
   ```bash
   chmod +x deployment/install-ubuntu.sh
   ./deployment/install-ubuntu.sh
   ```

5. **Configure environment:**
   ```bash
   nano /opt/proxmox-batch/.env
   ```

6. **Start service:**
   ```bash
   systemctl start proxmox-batch
   systemctl enable proxmox-batch
   ```

### Option 3: Docker/Docker Compose

1. **Clone repository:**
   ```bash
   git clone <your-repo-url> proxmox_batch
   cd proxmox_batch
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   nano .env
   ```

3. **Start with Docker Compose:**
   ```bash
   cd deployment
   docker-compose up -d
   ```

## Configuration

### Required Environment Variables

Edit `.env` file with your configuration:

```env
# Proxmox Configuration
PROXMOX_HOST=proxmox.example.com
PROXMOX_USER=root@pam

# Authentication: Use EITHER password OR token
PROXMOX_PASSWORD=your-secure-password
# OR (recommended for security)
# PROXMOX_TOKEN_NAME=batch-processor
# PROXMOX_TOKEN_VALUE=your-token-value

PROXMOX_VERIFY_SSL=false

# Claude API Configuration
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
CLAUDE_MODEL=claude-sonnet-4-20250514
CLAUDE_MAX_TOKENS=8000

# Application Settings
APP_HOST=0.0.0.0
APP_PORT=8000
BATCH_SIZE=5

# Feature Toggles
ENABLE_TERRAFORM=true
ENABLE_ANSIBLE=true
ENABLE_SECURITY_REVIEW=true
ENABLE_OPTIMIZATION=true
```

### Creating Proxmox API Token (Recommended)

For better security, use API tokens instead of passwords:

1. Login to Proxmox web interface
2. Go to **Datacenter → Permissions → API Tokens**
3. Click **Add** and create a token:
   - User: `root@pam`
   - Token ID: `batch-processor`
   - Privilege Separation: Unchecked (for full access)
4. Copy the token value and add to `.env`

## Usage

### Web Interface

1. **Access Dashboard:**
   ```
   http://YOUR_LXC_IP:8000/app
   ```

2. **Start Batch Analysis:**
   - Review cluster overview
   - Click "Start Batch Analysis"
   - Monitor progress in real-time

3. **View Results:**
   - Check job history
   - Click on completed jobs to view details
   - Download generated artifacts

### API Endpoints

The system exposes a REST API for automation:

#### Get Cluster Info
```bash
curl http://localhost:8000/cluster/info
```

#### Get All Resources
```bash
curl http://localhost:8000/cluster/resources
```

#### Start Batch Job
```bash
curl -X POST http://localhost:8000/batch/start
```

#### Check Job Status
```bash
curl http://localhost:8000/batch/jobs/{job_id}/status
```

#### Download Job Outputs
```bash
curl -O http://localhost:8000/batch/jobs/{job_id}/download
```

### Output Structure

After completion, outputs are organized as:

```
output/
└── job_{id}/
    ├── infrastructure_summary.md
    ├── qemu_webserver_100/
    │   ├── analysis.md
    │   ├── security_review.md
    │   ├── optimization_recommendations.md
    │   ├── main.tf
    │   ├── playbook.yml
    │   └── config.json
    ├── lxc_database_101/
    │   └── ...
    ├── terraform/
    │   ├── main.tf
    │   ├── variables.tf
    │   └── README.md
    └── ansible/
        ├── site.yml
        ├── playbooks/
        └── README.md
```

## Generated Artifacts

### For Each VM/LXC:
- **analysis.md**: Comprehensive analysis of purpose, configuration, and role
- **security_review.md**: Security assessment with recommendations
- **optimization_recommendations.md**: Performance and efficiency improvements
- **main.tf**: Terraform configuration to recreate the resource
- **playbook.yml**: Ansible playbook for provisioning
- **config.json**: Raw Proxmox configuration

### Infrastructure-Wide:
- **infrastructure_summary.md**: Executive summary of entire infrastructure
- **terraform/**: Consolidated Terraform project for all resources
- **ansible/**: Consolidated Ansible playbooks for all resources

## Cost Considerations

This system uses Claude API which has per-token pricing:

- **Small lab** (5-10 VMs): ~$2-5 per full analysis
- **Medium lab** (20-30 VMs): ~$10-20 per full analysis
- **Large lab** (50+ VMs): ~$30-50+ per full analysis

Costs depend on:
- Number of VMs/LXCs
- Complexity of configurations
- Enabled features (security, optimization, IaC)

**Tip**: Start with a small batch to estimate costs for your environment.

## Troubleshooting

### Service Won't Start

**Ubuntu:**
```bash
journalctl -u proxmox-batch -n 50
systemctl status proxmox-batch
```

**Alpine:**
```bash
rc-service proxmox-batch status
tail -f /var/log/messages
```

### Connection Issues

1. **Verify Proxmox connectivity:**
   ```bash
   curl -k https://YOUR_PROXMOX_HOST:8006/api2/json
   ```

2. **Test API credentials:**
   ```bash
   cd /opt/proxmox-batch/backend
   python3 -c "from config import settings; print(settings.proxmox_host)"
   ```

3. **Check firewall rules:**
   - LXC needs access to Proxmox API (port 8006)
   - LXC needs internet access for Claude API

### Database Issues

Reset database if needed:
```bash
cd /opt/proxmox-batch/backend
rm proxmox_batch.db
# Service will recreate on next start
```

## Security Considerations

1. **API Tokens**: Use Proxmox API tokens instead of passwords
2. **Network Isolation**: Consider running in isolated network segment
3. **Access Control**: Restrict web UI access via firewall
4. **Credentials**: Never commit `.env` file to version control
5. **Output Data**: Contains sensitive infrastructure information—protect accordingly

## Development

### Project Structure
```
proxmox_batch/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── database.py          # SQLite database operations
│   ├── proxmox_client.py    # Proxmox API client
│   ├── claude_analyzer.py   # Claude API integration
│   ├── batch_processor.py   # Batch processing engine
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── index.html          # Web UI
│   ├── style.css           # Styles
│   └── app.js              # Frontend logic
├── deployment/
│   ├── Dockerfile          # Docker image
│   ├── docker-compose.yml  # Docker Compose config
│   ├── install-alpine.sh   # Alpine installation
│   └── install-ubuntu.sh   # Ubuntu installation
└── README.md               # This file
```

### Running in Development Mode

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

Access at: `http://localhost:8000`

## Roadmap

- [ ] Support for Proxmox backup configurations
- [ ] Network topology visualization
- [ ] Cost analysis and recommendations
- [ ] Integration with monitoring systems
- [ ] Multi-cluster support
- [ ] Scheduled automatic audits
- [ ] Slack/Discord notifications
- [ ] Custom analysis templates

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues, questions, or feature requests:
- GitHub Issues: [Create an issue]
- Documentation: This README
- Logs: Check service logs for debugging

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [Anthropic Claude](https://www.anthropic.com/)
- Proxmox API via [Proxmoxer](https://github.com/proxmoxer/proxmoxer)

---

**Happy Infrastructure Management! 🚀**
