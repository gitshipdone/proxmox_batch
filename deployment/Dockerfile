# Multi-stage build for Proxmox Batch Processor
FROM python:3.11-slim as backend

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Create output directory
RUN mkdir -p /app/output

EXPOSE 8000

CMD ["python", "main.py"]
