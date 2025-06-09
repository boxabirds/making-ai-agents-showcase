#!/bin/bash

# Pippin Digital Being Framework Installation Script

# Step 1: Fork & Clone the repository (replace <your-username> with your GitHub username)
# git clone https://github.com/<your-username>/pippin-draft.git
# cd pippin-draft

# Step 2: Install UV package manager if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Step 3: Create and activate a virtual environment using UV
uv venv
source .venv/bin/activate  # On Unix/MacOS
# .venv\Scripts\activate   # On Windows (uncomment if on Windows)

# Step 4: Install project dependencies using UV pip
uv pip install -r requirements.txt

# Step 5: Onboarding & Configuration
# Copy the sample config folder
cp -r config_sample config

# You can choose one of the following onboarding methods:

# CLI Onboarding:
# python -m tools.onboard

# Web UI Onboarding:
# python -m server
# Then open http://localhost:8000 in your browser and follow the onboarding prompts.

# Step 6: Launch the Agent

# CLI Launch:
# python -m framework.main

# Web UI Launch:
# After onboarding via the web UI, click the Start button to run the main loop.

# Notes:
# - Ensure Python 3.9+ is installed.
# - A GitHub account is needed to fork the repo.
# - A Composio developer key is optional but recommended for OAuth-based skill connections.

# End of installation script