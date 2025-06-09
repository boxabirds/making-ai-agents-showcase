#!/bin/bash

# Agent Zero Installation Script
# This script installs and runs Agent Zero using Docker, the recommended package form.

# -------------------------
# Client and Server Setup
# -------------------------

# Step 1: Install Docker Desktop
# For Windows, macOS, and Linux, download and install Docker Desktop from:
# https://www.docker.com/products/docker-desktop/
# Linux users can alternatively install docker-ce (Community Edition) and add user to docker group:
# sudo usermod -aG docker $USER
# Then log out and back in.

# Step 2: Pull the Agent Zero Docker image
docker pull frdel/agent-zero-run

# Step 3: Create a data directory for persistence
# Replace /path/to/your/data with your preferred directory path
DATA_DIR="/path/to/your/data"
mkdir -p "$DATA_DIR"

# Step 4: Run the Agent Zero container
# Replace $PORT with your desired port number (e.g., 50080)
PORT=50080
docker run -p $PORT:80 -v "$DATA_DIR":/a0 frdel/agent-zero-run

# Step 5: Access the Web UI
# Open your browser and go to http://localhost:$PORT

# -------------------------
# Optional: Hacking Edition
# -------------------------
# To run the Hacking Edition (based on Kali Linux), use the following image instead:
# docker pull frdel/agent-zero-run:hacking
# docker run -p $PORT:80 -v "$DATA_DIR":/a0 frdel/agent-zero-run:hacking

# -------------------------
# Notes:
# - All Agent Zero data (memory, knowledge, instruments, prompts, settings) will be stored in the data directory.
# - You can configure Agent Zero through the Web UI settings page.
# - For updates, stop and remove the container and image, then pull the latest image and run again.
# - For full development environment setup or running without Docker, refer to the documentation.

# End of script