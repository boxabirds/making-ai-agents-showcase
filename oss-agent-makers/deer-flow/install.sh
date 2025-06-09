#!/bin/bash

# DeerFlow Installation Script
# This script installs DeerFlow Python package and sets up the environment.
# It also includes instructions for running the client (web UI) and server (backend).

# -------------------------
# Server (Python backend) Setup
# -------------------------

# Clone the repository
git clone https://github.com/bytedance/deer-flow.git
cd deer-flow

# Use uv to sync dependencies and create virtual environment
uv sync

# Copy example environment file and configuration
cp .env.example .env
cp conf.yaml.example conf.yaml

# Install marp-cli for ppt generation (macOS with Homebrew)
brew install marp-cli

# -------------------------
# Client (Web UI) Setup
# -------------------------

# Change to web directory and install dependencies with pnpm
cd web
pnpm install

# -------------------------
# Running the Project
# -------------------------

# To run the console UI (backend only)
# uv run main.py

# To run both backend and frontend servers in development mode (from project root)
# On macOS/Linux
# ./bootstrap.sh -d

# On Windows
# bootstrap.bat -d

# Open browser at http://localhost:3000 to access the web UI

# -------------------------
# Docker (Optional)
# -------------------------

# Build Docker image for backend
# docker build -t deer-flow-api .

# Run Docker container for backend
# docker run -d -t -p 8000:8000 --env-file .env --name deer-flow-api-app deer-flow-api

# Stop Docker container
# docker stop deer-flow-api-app

# Docker Compose to run backend and frontend together
# docker compose build
# docker compose up