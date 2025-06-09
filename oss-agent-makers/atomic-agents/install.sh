#!/bin/bash

# Installation script for Atomic Agents Python package

# Install the atomic-agents package from PyPI
uv pip install atomic-agents

# Install example provider packages (OpenAI and Groq as examples)
uv pip install openai groq

# Notes:
# - The atomic-agents package includes the CLI tool "Atomic Assembler"
# - To run the CLI, use: uv run atomic
# - For local development, you can clone the repo and use poetry (not included here)

# Client usage example (commented out, for reference):
# uv run atomic

# If you want to install from source for development:
# git clone https://github.com/BrainBlend-AI/atomic-agents.git
# cd atomic-agents
# poetry install

# End of script