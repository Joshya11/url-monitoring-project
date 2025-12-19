#!/bin/bash
set -e

echo "========================================"
echo " URL Monitoring Project - Ubuntu Setup"
echo "========================================"

# ------------------------------
# 1. Update system
# ------------------------------
echo "[1/7] Updating system packages..."
sudo apt update -y && sudo apt upgrade -y

# ------------------------------
# 2. Install required tools
# ------------------------------
echo "[2/7] Installing Docker, Git, Curl, Python3..."

# Install git & curl
sudo apt install -y git curl python3 python3-pip

# Install Docker
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com | sudo bash
else
    echo "Docker already installed."
fi

# Enable Docker
sudo systemctl enable docker
sudo systemctl start docker

# Install Docker Compose plugin
if ! command -v docker compose &> /dev/null; then
    echo "Installing Docker Compose plugin..."
    sudo apt install -y docker-compose-plugin
else
    echo "Docker Compose plugin already installed."
fi

# ------------------------------
# 3. Clone project repo (if needed)
# ------------------------------
PROJECT_DIR="url-monitoring-project"

if [ ! -d "$PROJECT_DIR" ]; then
    echo "[3/7] Cloning project repository..."
    git clone https://github.com/Joshya11/url-monitoring-project.git
else
    echo "Project folder already exists. Pulling latest changes..."
    cd $PROJECT_DIR
    git pull
    cd ..
fi

cd $PROJECT_DIR

# ------------------------------
# 4. Insert sample data into MySQL
# ------------------------------
echo "[4/7] Preparing MySQL sample data..."
# Automatically applies SQL when MySQL container starts

# ------------------------------
# 5. Build & start full Docker stack
# ------------------------------
echo "[5/7] Starting Docker containers..."
sudo docker compose up -d --build

sleep 10

# ------------------------------
# 6. Verify containers
# ------------------------------
echo "[6/7] Checking container status..."
sudo docker compose ps

# ------------------------------
# 7. Final message
# ------------------------------
echo "============================================"
echo "Setup complete!"
echo "Your services are now running:"
echo "App:        http://localhost:5000"
echo "Prometheus: http://localhost:9090"
echo "Pushgateway:http://localhost:9091"
echo "Grafana:    http://localhost:3000  (admin/admin)"
echo "============================================"
