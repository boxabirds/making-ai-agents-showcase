#!/bin/bash

# Semantic Kernel Installation Script
# This script installs the Semantic Kernel Python package using the uv package manager.
# It also sets environment variables for Azure OpenAI or OpenAI API keys.
# Adjust the environment variable values before running the script.

# --- Environment Setup ---
# Set your AI service API key environment variables here:
# Uncomment and replace with your actual keys before running

# export AZURE_OPENAI_API_KEY="your_azure_openai_api_key_here"
# or
# export OPENAI_API_KEY="your_openai_api_key_here"

# --- Python Package Installation using uv ---
# Initialize uv environment with Python 3.10+
uv init
uv venv -p 3.12
source .venv/bin/activate

# Install semantic-kernel package using uv pip
uv pip install semantic-kernel

# --- Notes ---
# For .NET or Java usage, please refer to their respective package managers and instructions.
# This script focuses on Python installation as per user preference.

# End of script