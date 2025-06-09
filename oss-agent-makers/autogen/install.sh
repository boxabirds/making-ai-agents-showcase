#!/bin/bash

# AutoGen Python package installation script using uv package manager

# Step 1: Install uv package manager if not already installed
# Refer to https://docs.astral.sh/uv/getting-started/installation/ for installation instructions
# Uncomment the following line if uv is not installed
# curl -fsSL https://get.astral.sh | sh

uv init
# Step 2: Update uv to the recommended version (example: 0.5.18)
uv self update 0.5.18

# Step 3: Create and activate a virtual environment with all dependencies
uv sync --all-extras
source .venv/bin/activate

# Step 4: Install AutoGen packages from PyPI (latest stable versions)
uv pip install -U autogen-agentchat autogen-ext[openai]
uv pip install -U autogenstudio

# Optional: To upgrade packages later, run the above uv pip install commands again

# Notes:
# - Python 3.10 or later is required
# - This script assumes you are running it from the root of the python directory in the project
# - For development, use uv sync --all-extras and source .venv/bin/activate to work with local packages

# End of script