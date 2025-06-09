#!/bin/bash

# AgentVerse Installation Script
# This script installs the AgentVerse Python package and provides instructions for running client and server components if needed.

# --- Python Package Installation ---

# Initialize a uv environment with Python 3.9+ (adjust version if needed)
uv init
uv venv -p python3.9
source .venv/bin/activate

# Install AgentVerse package in editable mode (recommended)
uv pip install -e .

# If you want to use local models such as LLaMA, install additional dependencies
# Uncomment the following line if needed
# uv pip install -r requirements_local.txt

# Alternatively, you can install AgentVerse from PyPI (uncomment if preferred)
# uv pip install -U agentverse

# --- Environment Variables ---

# Export your OpenAI API key (replace with your actual key)
echo "export OPENAI_API_KEY=\"your_api_key_here\"" >> ~/.bashrc
export OPENAI_API_KEY="your_api_key_here"

# If using Azure OpenAI services, export these variables as well
echo "export AZURE_OPENAI_API_KEY=\"your_api_key_here\"" >> ~/.bashrc
echo "export AZURE_OPENAI_API_BASE=\"your_api_base_here\"" >> ~/.bashrc
export AZURE_OPENAI_API_KEY="your_api_key_here"
export AZURE_OPENAI_API_BASE="your_api_base_here"

# --- Running Simulation Framework ---

# To run a simulation example (e.g., NLP Classroom with 9 players)
# Use the CLI command below after activating the environment
# agentverse-simulation --task simulation/nlp_classroom_9players

# To run the GUI version of the simulation
# agentverse-simulation-gui --task simulation/nlp_classroom_9players
# Then open your browser at http://127.0.0.1:7860/

# --- Running Task-Solving Framework ---

# To run a benchmark dataset (e.g., Humaneval with gpt-3.5-turbo)
# agentverse-benchmark --task tasksolving/humaneval/gpt-3.5 --dataset_path data/humaneval/test.jsonl --overwrite

# To run a specific task-solving problem
# agentverse-tasksolving --task tasksolving/brainstorming

# To run task-solving cases with tools, first build and run the ToolServer from XAgent repo:
# https://github.com/OpenBMB/XAgent#%EF%B8%8F-build-and-setup-toolserver
# Then run:
# agentverse-tasksolving --task tasksolving/tool_using/24point

# --- Running Pokemon Game (Simulation with UI) ---

# 1. Launch the local server for Pokemon game
# uvicorn pokemon_server:app --reload --port 10002

# 2. In another terminal, navigate to the UI directory and install dependencies
cd ui
# If npm is not installed, install it first: https://docs.npmjs.com/downloading-and-installing-node-js-and-npm
npm install
npm run watch

# Wait for compilation to complete, then use WASD keys to move and SPACE to interact in the game UI

# End of script