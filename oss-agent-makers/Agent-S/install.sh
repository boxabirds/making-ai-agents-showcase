#!/bin/bash

# Installation script for Agent S2 Python package and setup

# Install the Python package using pip (preferred package manager mentioned)
uv pip install gui-agents

# Set environment variables for API keys (replace <YOUR_API_KEY> with actual keys)
# You can uncomment and export these in your shell profile (~/.bashrc or ~/.zshrc)
# export OPENAI_API_KEY=<YOUR_API_KEY>
# export ANTHROPIC_API_KEY=<YOUR_ANTHROPIC_API_KEY>
# export HF_TOKEN=<YOUR_HF_TOKEN>

# Setup Perplexica for web knowledge retrieval (optional but recommended)
# 1. Ensure Docker Desktop is installed and running
# 2. Initialize Perplexica submodule and rename config file
cd Perplexica
git submodule update --init
mv sample.config.toml config.toml

# Edit config.toml to add your API keys for OpenAI, Ollama, Groq, Anthropic as needed

# 3. Start Perplexica Docker container
docker compose up -d

# 4. Export Perplexica URL environment variable (adjust port if different)
export PERPLEXICA_URL=http://localhost:3000/api/search

# Usage notes:
# - Run the agent CLI with `agent_s2` command and specify model/provider options
# - Use the gui_agents SDK in Python scripts as shown in the README for advanced usage

# Warning: The agent runs Python code to control your computer. Use with caution.