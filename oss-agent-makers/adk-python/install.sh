#!/bin/bash

# Installation script for the Agent Development Kit (ADK) Python package

# -------------------------
# Python Package Installation
# -------------------------
# Install the latest stable version of ADK using pip
# Recommended for most users as it represents the most recent official release
#pip install google-adk

# If you want to install the development version (latest code from main branch)
# Uncomment the following line:
# pip install git+https://github.com/google/adk-python.git@main

# -------------------------
# Notes
# -------------------------
# - The stable release is updated weekly.
# - The development version may contain experimental changes or bugs.
# - For more details and documentation, visit: https://google.github.io/adk-docs

# -------------------------
# Using uv package manager (commented out version)
# -------------------------

# Initialize uv environment with required Python version (example: 3.10)
uv init
uv venv -p 3.10
source .venv/bin/activate

# Install the stable release using uv pip
uv pip install google-adk

# For development version, uncomment and use:
# uv pip install git+https://github.com/google/adk-python.git@main