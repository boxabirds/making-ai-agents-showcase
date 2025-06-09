#!/bin/bash

# Potpie AI Installation Script
# This script installs and runs Potpie AI using the official instructions from the README.md

# --- Prerequisites ---
# Make sure Docker and Git are installed and running
# Make sure Python 3.10.x is installed

# --- Setup Python Virtual Environment ---
python3.10 -m venv venv
source venv/bin/activate

# --- Install Python dependencies ---
uv pip install -r requirements.txt

# --- Initialize UI Submodule ---
git submodule update --init

# --- Setup Potpie UI ---
cd potpie-ui || exit
git checkout main
git pull origin main

# Copy environment template and edit as needed
cp .env.template .env
echo "Please edit potpie-ui/.env to configure environment variables as needed."

# Build and start the frontend UI
pnpm build
pnpm start &

# Return to root directory
cd ..

# --- Start Potpie Services ---
chmod +x start.sh
./start.sh

# --- To stop Potpie services ---
# ./stop.sh

# --- Notes ---
# - The .env file in the root directory should be created based on .env.template and configured with:
#   - PostgreSQL, Neo4j, Redis connection strings
#   - API keys for providers
#   - Model names for inference and chat
# - The start.sh script will start Docker services, apply migrations, start FastAPI app and Celery worker
# - Use the API endpoints to authenticate, parse repos, create conversations, and interact with agents as described in the README

# --- End of script ---