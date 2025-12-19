URL Monitoring System
1. Overview

This project is a URL monitoring system that:

Reads a list of URLs / IP:Port combinations from a MySQL database

Performs HTTP (curl-like) health checks

Publishes results to Prometheus (time-series database)

Displays the status on a simple frontend dashboard

The system is fully Dockerized so it can be run easily on any machine.

2. High-Level Flow (Simple)

URLs are stored in MySQL

Backend application reads the URLs

HTTP checks are executed (with retries)

Results are pushed to Prometheus

Frontend displays the results

MySQL → Backend App → Pushgateway → Prometheus → Frontend

3. Project Structure (What Each File Does)
url-monitoring-project/
│
├── app/
│   ├── app.py          # Main backend application
│   ├── config.py       # Configuration (DB, retries, endpoints)
│   ├── secrets.py      # Handles encrypted credentials
│   ├── __init__.py     # Python package marker
│   └── static/
│       └── index.html  # Frontend UI
│
├── mysql-init/
│   └── init.sql        # Creates DB tables & inserts 20+ sample URLs
│
├── prometheus/
│   └── prometheus.yml  # Prometheus configuration
│
├── Dockerfile          # Builds backend application image
├── docker-compose.yml  # Runs all services together
├── ubuntu_setup.sh     # Automated setup for Ubuntu systems
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── .gitignore          # Prevents secrets from being committed
└── README.md           # Documentation

4. Prerequisites

Docker

Docker Compose

Docker is used to ensure the project runs the same way on all machines.

5. Setup Instructions (Step-by-Step)
Step 1: Clone the Repository
git clone https://github.com/Joshya11/url-monitoring-project
cd url-monitoring-project

Step 2: Create Environment File
cp .env.example .env


Secrets are intentionally not included in GitHub for security.

Step 3: Start the Application
docker compose up --build


This will start:

MySQL (with sample data)

Backend application

Prometheus

Pushgateway

Frontend UI

6. Access the Application

Frontend UI: http://localhost:5000

Health Check: http://localhost:5000/health

Prometheus UI: http://localhost:9090

7. Sample Execution Flow

Docker containers start

MySQL initializes with 20+ sample URLs

Backend reads URLs from the database

HTTP checks are executed

Results are stored in Prometheus

Frontend displays the status

8. Ubuntu Setup (Optional)

For Ubuntu systems, an automated setup script is provided:

chmod +x ubuntu_setup.sh
./ubuntu_setup.sh


This installs Docker and runs the project automatically.

9. Security Notes

No passwords or secrets are stored in GitHub

Credentials are handled using environment variables

.env file is ignored by Git

10. Summary

Fully working end-to-end solution

Dockerized and portable

Secure credential handling

Simple setup and usage

Author: Joshya
