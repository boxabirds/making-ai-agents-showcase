#!/bin/bash

# SpinAI Installation Script
# This script installs the SpinAI package and provides instructions to run the agent.
# SpinAI is a TypeScript framework for building AI agents.
# Node.js version 18 or higher is required.

# Install SpinAI package globally using npm
npm install -g spinai

# Alternatively, to use SpinAI in a new project, create a new project using the CLI:
# npx create-spinai

# Instructions for running the agent locally after project creation:
# 1. Choose a template and configure your .env file with your LLM API key, e.g.:
#    OPENAI_API_KEY=your_api_key_here
# 2. Start your agent with:
#    npm run dev

# Client and Server instructions (if applicable) would be part of the project templates,
# so refer to the README of the chosen template for environment variables and setup.

# Note: This project requires Node.js >= 18 and npm (version 10.8.2 recommended).

# End of script