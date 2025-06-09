#!/bin/bash

# OpenHands Installation and Run Script

# This script installs and runs OpenHands using the package form for the frontend (JavaScript/TypeScript).
# It also includes instructions to run the OpenHands server locally using Docker.

# ---------------------------
# Client (Frontend) Setup
# ---------------------------

echo "Installing OpenHands frontend dependencies..."
cd output/cache/All-Hands-AI/OpenHands/frontend || exit 1

# Ensure Node.js version 20 or later is installed
NODE_VERSION=$(node -v | sed 's/v//;s/\..*//')
if [ "$NODE_VERSION" -lt 20 ]; then
  echo "Node.js version 20 or later is required. Please install or upgrade Node.js."
  exit 1
fi

# Install dependencies using npm (preferred package manager here)
npm install

echo "OpenHands frontend dependencies installed."

# To run frontend in development mode with mocked backend:
# npm run dev

# To build frontend for production:
# npm run build

# To serve the built frontend:
# npm start

# ---------------------------
# Server Setup (Local Docker)
# ---------------------------

echo "Pulling OpenHands Docker runtime image..."
docker pull docker.all-hands.dev/all-hands-ai/runtime:0.41-nikolaik

echo "Running OpenHands Docker container..."
docker run -it --rm --pull=always \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.41-nikolaik \
    -e LOG_ALL_EVENTS=true \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v ~/.openhands-state:/.openhands-state \
    -p 3000:3000 \
    --add-host host.docker.internal:host-gateway \
    --name openhands-app \
    docker.all-hands.dev/all-hands-ai/openhands:0.41

echo "OpenHands server is running at http://localhost:3000"
echo "OpenHands frontend can be accessed at http://localhost:3001 (if running dev server)"

# Notes:
# - When opening the application, you will be prompted to choose an LLM provider and add an API key.
# - Anthropic's Claude Sonnet 4 is recommended but many options are supported.
# - For more advanced deployment options or multi-tenant setups, contact the OpenHands team.

exit 0