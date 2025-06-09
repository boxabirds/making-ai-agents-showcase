#!/bin/bash

# Letta (previously MemGPT) installation and usage script
# This script installs the Letta Python package and provides instructions
# for running the Letta server both via pip and Docker.

# ---------------------------
# Python package installation
# ---------------------------

# Using uv package manager for Python environment setup and installation

# Initialize uv environment
uv init

# Create a virtual environment with the required Python version (default to system python)
uv venv -p python3

# Activate the virtual environment
source .venv/bin/activate

# Install Letta package using uv pip
uv pip install -U letta

# Set environment variables for your LLM / embedding providers
# Replace the placeholder with your actual API keys or URLs
export OPENAI_API_KEY="your_openai_api_key"
# Example for Ollama provider:
# export OLLAMA_BASE_URL="http://localhost:11434"

# ---------------------------
# Running Letta server (pip)
# ---------------------------

# Run the Letta server (defaults to SQLite database backend)
# For PostgreSQL, set LETTA_PG_URI environment variable before running
# Example:
# export LETTA_PG_URI="postgresql://user:password@localhost:5432/letta_db"
letta server

# ---------------------------
# Running Letta server (Docker)
# ---------------------------

# Recommended way to run Letta server with PostgreSQL backend using Docker

# Replace ~/.letta/.persist/pgdata with your desired persistent storage path
# Replace your_openai_api_key with your actual OpenAI API key

# Run the Letta server container
docker run \
  -v ~/.letta/.persist/pgdata:/var/lib/postgresql/data \
  -p 8283:8283 \
  -e OPENAI_API_KEY="your_openai_api_key" \
  letta/letta:latest

# Alternatively, use a .env file to pass environment variables
# docker run \
#   -v ~/.letta/.persist/pgdata:/var/lib/postgresql/data \
#   -p 8283:8283 \
#   --env-file .env \
#   letta/letta:latest

# To enable password protection on the server, add these environment variables:
# -e SECURE=true \
# -e LETTA_SERVER_PASSWORD=yourpassword \

# ---------------------------
# Accessing the Agent Development Environment (ADE)
# ---------------------------

# 1. Start your Letta server (via Docker or pip)
# 2. Visit https://app.letta.com
# 3. Select "Local server" in the left panel to connect to your local server

# ---------------------------
# Using the Letta CLI
# ---------------------------

# If running Letta server in Docker, you can access the CLI inside the container:
# docker exec -it $(docker ps -q -f ancestor=letta/letta) letta run

# If running locally, simply run:
# letta run

# This CLI allows you to create and chat with agents interactively.

# End of script