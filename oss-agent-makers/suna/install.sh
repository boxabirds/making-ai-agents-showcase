#!/bin/bash

# Suna Installation Script
# This script installs and runs the Suna project in its package form.
# It includes client (frontend) and server (backend) setup instructions.

# ---------------------------
# Backend (Server) Installation
# ---------------------------

# Clone the repository
git clone https://github.com/kortix-ai/suna.git
cd suna

# Run the setup wizard (Python)
python setup.py

# Start the backend services using Docker Compose
docker compose down && docker compose up --build

# Notes:
# - For local development, you can run Redis and RabbitMQ separately:
#   docker compose up redis rabbitmq
# - Then run the API and worker locally:
#   cd backend
#   poetry run python3.11 api.py
#   cd ../frontend
#   poetry run python3.11 -m dramatiq run_agent_background
# - Make sure to configure your .env file for Redis and RabbitMQ hosts accordingly.

# ---------------------------
# Frontend (Client) Installation
# ---------------------------

# Navigate to frontend directory
cd frontend

# Install dependencies and run the development server
npm install
npm run dev

# Open http://localhost:3000 in your browser to access the frontend UI

# ---------------------------
# Additional Notes
# ---------------------------

# For production deployment of backend services, use:
# docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# For detailed manual setup and self-hosting instructions, refer to:
# ./docs/SELF-HOSTING.md in the repository

# End of script