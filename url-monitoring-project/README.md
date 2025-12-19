# URL Monitoring Project-by Joshya

This repository contains a solution for the assignment:
- Reads target list from MySQL
- Runs HTTP checks (concurrent)
- Pushes metrics to Prometheus Pushgateway
- Frontend that displays latest metrics
- Docker Compose setup to bring up MySQL, Prometheus, Pushgateway, Grafana, and the Flask app
- Setup script to install Docker & start the stack on Ubuntu

See `ubuntu_setup.sh` for one-command setup on an Ubuntu machine.
