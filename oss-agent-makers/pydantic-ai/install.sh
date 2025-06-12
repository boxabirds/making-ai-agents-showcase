#!/bin/bash

# PydanticAI Installation Script using uv (Python package manager)

# Initialize uv environment
uv init

# Create a virtual environment with Python 3.9 or higher (minimum required is 3.9)
uv venv -p python3.12

# Activate the virtual environment
source .venv/bin/activate

# Install the pydantic-ai package from PyPI using uv pip
uv pip install pydantic-ai

# Note: pydantic-ai has optional dependencies and integrations.
# You can install additional optional dependencies as needed, for example:
# uv pip install "pydantic-ai[examples]"
# uv pip install "logfire>=3.11.0"  # for Pydantic Logfire integration

# There is no indication of a required server or client to run locally.
# Usage is via Python import and API as shown in the README examples.

# Example usage (commented out):
# python -c "from pydantic_ai import Agent; print('PydanticAI installed and ready to use')"