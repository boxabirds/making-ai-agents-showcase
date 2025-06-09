#!/bin/bash

# Installation script for n8n - Secure Workflow Automation for Technical Teams
# This script installs and runs n8n using the package form (npm via npx) and also provides Docker deployment instructions.

# ---------------------------
# Client and Server Installation and Run (Using npx)
# ---------------------------

# Ensure Node.js is installed (recommended version can be checked at https://nodejs.org/en/)
# Then run n8n instantly using npx:
npx n8n

# ---------------------------
# Server Deployment Using Docker
# ---------------------------

# Create a Docker volume for persistent data storage
docker volume create n8n_data

# Run the n8n Docker container with port 5678 exposed and volume mounted
docker run -it --rm --name n8n -p 5678:5678 -v n8n_data:/home/node/.n8n docker.n8n.io/n8nio/n8n

# Access the n8n editor at http://localhost:5678

# End of script