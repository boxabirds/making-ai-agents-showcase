#!/bin/bash

# GPT Researcher Installation Script
# This script installs and runs GPT Researcher as a Python package using uv package manager.

# Step 1: Ensure Python 3.11 or later is installed
# (User should verify this manually or install Python 3.11+ before running this script)

# Step 2: Initialize uv environment and create virtual environment with Python 3.11
uv init
uv venv -p 3.11
source .venv/bin/activate

# Step 3: Install GPT Researcher package from PyPI using uv pip
uv pip install gpt-researcher

# Step 4: Set required environment variables for API keys (replace placeholders with your keys)
export OPENAI_API_KEY={Your OpenAI API Key here}
export TAVILY_API_KEY={Your Tavily API Key here}

# Step 5: Run the GPT Researcher server using uv
uv pip install uvicorn  # Ensure uvicorn is installed in the environment
uv run uvicorn main:app --reload

# The server will be available at http://localhost:8000

# Optional: If you want to run the frontend React app locally (default port 3000),
# you need to clone the repo and run the frontend separately (not covered here).

# Docker alternative (if you prefer Docker):
# 1. Install Docker
# 2. Clone the repo and copy .env.example to .env, add your API keys there
# 3. Run:
#    docker-compose up --build
# This will start both the Python server (localhost:8000) and React frontend (localhost:3000)

# End of script