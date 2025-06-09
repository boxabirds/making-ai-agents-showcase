#!/bin/bash

# Installation script for Integuru Python package using poetry (as per README.md)

# Setup OpenAI API key environment variable before running this script
# export OPENAI_API_KEY="your_openai_api_key_here"

# Install dependencies using poetry
poetry install

# Activate poetry shell
poetry shell

# Register the Poetry virtual environment with Jupyter
poetry run ipython kernel install --user --name=integuru

# Instructions for running the client (browser interaction)
echo "To spawn a browser and create HAR file, run:"
echo "poetry run python create_har.py"
echo "Log into your platform and perform the desired action (e.g., downloading a utility bill)."

# Instructions for running the server/agent
echo "To run Integuru agent, use:"
echo "poetry run integuru --prompt \"download utility bills\" --model <gpt-4o|o3-mini|o1|o1-mini>"

# To run unit tests
echo "To run unit tests:"
echo "poetry run pytest"