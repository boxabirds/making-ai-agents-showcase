#!/bin/bash

# AutoGPT Installation Script for Package Use (Python-focused with uv package manager)

# Note: The official instructions recommend using Docker for self-hosting.
# This script provides a Python package installation approach using uv,
# adapting from the local build instructions.

# System requirements:
# - Linux (Ubuntu 20.04+), macOS (10.15+), or Windows 10/11 with WSL2
# - Docker Engine 20.10.0+, Docker Compose 2.0.0+, Git 2.30+, Node.js 16+, npm 8+
# - VSCode or any modern code editor recommended

# ---------------------------
# Python Environment Setup
# ---------------------------

# Initialize uv environment with Python 3.10 (or adjust as needed)
uv init
uv venv -p python3.10
source .venv/bin/activate

# Install Python dependencies (assuming requirements.txt or similar)
# The repo does not provide explicit uv instructions, so we adapt pip install commands
uv pip install -r requirements.txt

# ---------------------------
# Clone and Setup Project
# ---------------------------

# Clone the repo (replace <YOUR_REPO_PATH> with your fork or main repo URL)
# git clone https://github.com/<YOUR_REPO_PATH>
# cd AutoGPT

# Run setup script to install dependencies and configure GitHub token
# ./run setup

# ---------------------------
# Running the AutoGPT Agent
# ---------------------------

# Create your agent (replace YOUR_AGENT_NAME with your chosen name)
# ./run agent create YOUR_AGENT_NAME

# Start your agent (runs server on http://localhost:8000/)
# ./run agent start YOUR_AGENT_NAME

# To stop the agent
# ./run agent stop

# ---------------------------
# Frontend and Server Notes
# ---------------------------

# The frontend is accessible at http://localhost:8000/
# Login with Google or GitHub account to interact with your agent.

# The official recommended deployment is via Docker for full platform hosting.
# For Docker-based setup, refer to the official docs: https://docs.agpt.co/platform/getting-started/

# ---------------------------
# End of Script
# ---------------------------