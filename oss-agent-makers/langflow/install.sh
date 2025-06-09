#!/bin/bash

# Langflow Installation Script

# ---------------------------
# Python Package Installation
# ---------------------------

# Recommended installation using uv package manager
uv venv -p 3.11
uv pip install langflow

# Alternative installation using pip (commented out)
# pip install langflow

# ---------------------------
# Deployment Instructions
# ---------------------------

# Self-managed deployment using Docker
# Follow the guide at https://docs.langflow.org/deployment-docker for Docker deployment instructions

# Fully-managed deployment by DataStax
# Sign up for a free account at https://astra.datastax.com/signup?type=langflow to use the fully-managed environment

# End of script