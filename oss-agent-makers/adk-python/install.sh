#!/bin/bash

# Installation script for ADK Python agents
echo "Setting up ADK Python agents..."

# Create virtual environment
echo "Creating virtual environment..."
uv venv -p 3.10

# Activate virtual environment
source .venv/bin/activate

# Install the package and dependencies
echo "Installing dependencies..."
pip install google-adk
