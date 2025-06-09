#!/bin/bash

# PySpur Installation and Usage Script
# This script installs PySpur as a Python package and provides instructions to start the server.

# Step 1: Install PySpur package using uv (Python package manager)
uv pip install pyspur

# Step 2: Initialize a new PySpur project
# Replace 'my-project' with your desired project directory name
pyspur init my-project
cd my-project

# Step 3: Start the PySpur server with SQLite (default)
pyspur serve --sqlite

# Optional: Configure your environment and add API keys
# - To add provider keys (OpenAI, Anthropic, etc.), use the App UI API Keys tab
# - Or manually edit the .env file (recommended to configure PostgreSQL for stability)
# After editing .env, restart the server with:
# pyspur serve

# End of script