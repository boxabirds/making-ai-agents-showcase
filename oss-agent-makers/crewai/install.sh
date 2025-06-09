#!/bin/bash

# CrewAI Installation Script
# This script installs the CrewAI Python package using uv package manager as per the README instructions.
# It also includes instructions to create a new CrewAI project and run it.

# Step 1: Initialize uv environment and create virtual environment with required Python version
uv init
uv venv -p 3.10
source .venv/bin/activate

# Step 2: Install CrewAI package (basic)
uv pip install crewai

# Optional: Install CrewAI with additional tools
uv pip install 'crewai[tools]'

# Step 3: Create a new CrewAI project (replace <project_name> with your desired project name)
# crewai create crew <project_name>

# Step 4: Navigate to your project directory
# cd <project_name>

# Step 5: Install dependencies locked by uv (optional)
# crewai install

# Step 6: Run your CrewAI project
# Using the CLI
# crewai run

# Or using Python directly
# python src/<project_name>/main.py

# Notes:
# - Ensure you have Python >=3.10 and <3.14 installed on your system.
# - Set environment variables for API keys in your .env file before running:
#   OPENAI_API_KEY=sk-...
#   SERPER_API_KEY=YOUR_KEY_HERE

# End of script