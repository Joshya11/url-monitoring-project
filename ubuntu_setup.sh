#!/bin/bash
set -e
# Run on Ubuntu 20.04+ as root or with sudo
# Installs docker, docker-compose (v2 via plugin) and launches the stack

echo "Updating apt..."
apt-get update

echo "Installing prerequisites..."
apt-get install -y ca-certificates curl gnupg lsb-release

echo "Installing Docker..."
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo   "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu   $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

echo "Adding current user to docker group (you might need to re-login)..."
usermod -aG docker $SUDO_USER || true

echo "Starting docker-compose stack..."
# Run docker-compose in repository directory (assumes this script is placed in repo root)
docker compose up -d --build

echo "Stack started. Wait a few seconds and check containers with: docker ps"
