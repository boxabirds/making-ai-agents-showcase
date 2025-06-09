#!/bin/bash

# AgentStack Installation Script

# This script installs AgentStack using the recommended Python package manager "uv".
# It assumes Python 3.10+ is installed on the system.

# Initialize uv environment and create a virtual environment with Python 3.10+
uv init
uv venv -p 3.10
source .venv/bin/activate

# Install AgentStack package
uv pip install agentstack

# Initialize a new AgentStack project (replace <project_name> with your desired project name)
# agentstack init <project_name>

# Change directory to your new project folder (uncomment after creating the project)
# cd <project_name>

# Install project dependencies inside the project folder
# uv pip install

# Run the default agent (uncomment to run)
# agentstack run

# Notes:
# - For more details and usage, visit https://docs.agentstack.sh/
# - This script uses uv exclusively for Python package management as per instructions.