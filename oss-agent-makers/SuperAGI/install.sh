#!/bin/bash

# SuperAGI Installation Script

# This script installs and runs SuperAGI using Docker as per the official installation instructions.

# ---------------------------
# Client and Server Setup
# ---------------------------

# Clone the SuperAGI repository
git clone https://github.com/TransformerOptimus/SuperAGI.git

# Navigate to the cloned directory
cd SuperAGI

# Create a copy of the config template
cp config_template.yaml config.yaml

# Ensure Docker is installed and running before proceeding
# Docker installation instructions: https://docs.docker.com/get-docker/

# Run SuperAGI using Docker Compose (regular usage)
docker compose -f docker-compose.yaml up --build

# If you want to use SuperAGI with Local LLMs and have GPU support, use:
# docker compose -f docker-compose-gpu.yml up --build

# After the containers are up, access the SuperAGI GUI at:
# http://localhost:3000

# End of script