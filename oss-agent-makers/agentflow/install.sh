#!/bin/bash

# Agentflow Installation Script
# This script installs the Agentflow Python package and provides instructions for running it.

# Python package installation using uv (Python package manager)
# Initialize uv environment and create virtual environment with required Python version (assumed 3.8+)

git clone https://github.com/simonmesmith/agentflow src
cd src
uv init
uv venv -p python3
source .venv/bin/activate

# Install dependencies from requirements.txt using uv pip
uv pip install -r requirements.txt

# Usage instructions:
# To run flows from the command line:
# python -m run --flow=example
#
# To pass variables to your flow:
# python -m run --flow=example_with_variables --variables 'market=college students' 'price_point=$50'
#
# To enable verbose output:
# python -m run --flow=example -v

# No separate client/server instructions are needed as this is a Python package run locally.