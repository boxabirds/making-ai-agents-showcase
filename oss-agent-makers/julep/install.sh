#!/bin/bash

# Installation script for Julep project package usage

# ---------------------------
# Client Installation Section
# ---------------------------

# Install Julep Python SDK using uv package manager
uv init
uv venv -p python3
source .venv/bin/activate
uv pip install julep

# Install Julep CLI (Python only, currently beta)
uv pip install julep-cli

# ---------------------------
# Server Installation Section
# ---------------------------

# Create Docker volumes for persistent data storage
docker volume create grafana_data
docker volume create memory_store_data
docker volume create temporal-db-data
docker volume create prometheus_data
docker volume create seaweedfs_data

# Run the project using Docker Compose in Single-Tenant mode (no API key needed)
docker compose --env-file .env --profile temporal-ui --profile single-tenant --profile self-hosted-db --profile blob-store --profile temporal-ui-public up --build --force-recreate --watch

# To run in Multi-Tenant mode (requires JWT token as API key), use:
# docker compose --env-file .env --profile temporal-ui --profile multi-tenant --profile embedding-cpu --profile self-hosted-db --profile blob-store --profile temporal-ui-public up --force-recreate --build --watch

# Generate JWT token for Multi-Tenant mode (requires jwt-cli installed)
# Replace JWT_SHARED_KEY with your key from .env file
# jwt encode --secret JWT_SHARED_KEY --alg HS512 --exp=$(date -d '+10 days' +%s) --sub '00000000-0000-0000-0000-000000000000' '{}'

# ---------------------------
# Notes:
# - For Python usage, activate the virtual environment before running your scripts.
# - Use the JWT token as API key in Multi-Tenant mode when initializing the Julep client.
# - For Node.js usage, install the SDK with bun or npm as preferred (not included here per instructions).
# ---------------------------