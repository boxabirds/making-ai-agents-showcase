#!/bin/bash

# Installation script for BeeAI Framework

# ============================
# Python Package Installation
# ============================
# Prerequisites: Python >= 3.11

# Using uv package manager (preferred)
uv init
uv venv -p 3.11
source .venv/bin/activate
uv pip install beeai-framework

# To run Python projects, use:
# python [project_name].py

# ============================
# TypeScript Package Installation
# ============================

# Using npm (preferred package manager)
#npm install beeai-framework

# To run TypeScript projects, use:
# npm run start [project_name].ts

# Alternatively, using yarn:
# yarn add beeai-framework
# yarn start [project_name].ts

# ============================
# Notes
# ============================
# - For Python, ensure you have Python 3.11 or higher installed.
# - For TypeScript, ensure you have Node.js installed.
# - For Python examples, see python/examples directory.
# - For TypeScript examples, see typescript/examples directory.
# - Some examples require additional setup like installing Ollama or Groq models.
# - Refer to the official documentation for more details and advanced usage.