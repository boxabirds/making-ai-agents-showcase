#!/bin/bash

# AG2 Installation Script
# This script installs the AG2 Python package and provides instructions for running example agents.

# Python package installation using uv (Python package manager)
uv init
uv venv -p 3.9
source .venv/bin/activate
uv pip install ag2[openai]

# Setup your API keys
# Create a file named OAI_CONFIG_LIST with your OpenAI API keys in JSON format.
# Example content:
# [
#   {
#     "model": "gpt-4o",
#     "api_key": "<your OpenAI API key here>"
#   }
# ]

# Run your first agent example (Python)
# Save the following code in a script or Jupyter Notebook and run it after activating the virtual environment.


# Notes:
# - AG2 requires Python version >= 3.9 and < 3.14.
# - The package is installed from PyPI as "ag2" or alias "autogen".
# - API keys must be set up in the OAI_CONFIG_LIST file for LLM access.
# - The example above demonstrates running an assistant and user proxy agent interaction.

# End of script