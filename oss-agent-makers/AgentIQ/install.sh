#!/bin/bash

# NVIDIA Agent Intelligence Toolkit Installation Script

# ============================
# Prerequisites
# ============================
# Make sure you have the following installed:
# - Git
# - Git Large File Storage (LFS)
# - uv (Python package manager)
# - Python 3.11 or 3.12

# ============================
# Install From Source
# ============================

# Clone the AIQ toolkit repository
git clone git@github.com:NVIDIA/AIQToolkit.git aiqtoolkit
cd aiqtoolkit

# Initialize, fetch, and update submodules
git submodule update --init --recursive

# Fetch the data sets by downloading the LFS files
git lfs install
git lfs fetch
git lfs pull

uv init
# If you want to specify Python version explicitly (3.11 or 3.12), use:
uv venv --seed .venv --python 3.11
source .venv/bin/activate

# 20250609 uv.lock file was checked in corrupted
rm uv.lock
uv lock

# Install the AIQ toolkit library with all optional dependencies (developer tools, profiling, plugins)
uv sync --all-groups --all-extras

# Alternatively, install just the core AIQ toolkit without plugins
#uv sync

# To install individual plugins, use:
# uv pip install -e '.[<plugin_name>]'
# Example for langchain plugin:
# uv pip install -e '.[langchain]'

# To install optional profiling dependencies:
# uv pip install -e '.[profiling]'

# ============================
# Verify Installation
# ============================
aiq --version

# ============================
# Hello World Example Usage
# ============================

# Set your NVIDIA API key environment variable
# export NVIDIA_API_KEY=<your_api_key>

# Create a workflow configuration file named workflow.yaml with the following content:
# functions:
#    wikipedia_search:
#       _type: wiki_search
#       max_results: 2
#
# llms:
#    nim_llm:
#       _type: nim
#       model_name: meta/llama-3.1-70b-instruct
#       temperature: 0.0
#
# workflow:
#    _type: react_agent
#    tool_names: [wikipedia_search]
#    llm_name: nim_llm
#    verbose: true
#    retry_parsing_errors: true
#    max_retries: 3

# Run the example workflow:
# aiq run --config_file workflow.yaml --input "List five subspecies of Aardvarks"

# ============================
# End of Script
# ============================