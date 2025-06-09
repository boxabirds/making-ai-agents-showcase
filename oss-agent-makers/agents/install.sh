#!/bin/bash

# Installation script for Cloudflare Agents package

# Client and Server installation instructions for the 'agents' package

# ---------------------------
# Client Installation Section
# ---------------------------

# This project is primarily a Node.js/TypeScript package.
# The recommended installation method is via npm.

echo "Installing the 'agents' package via npm..."
npm install agents

# ---------------------------
# Server Setup Section
# ---------------------------

# To create a new project using the Cloudflare Agents starter template:
echo "Creating a new Cloudflare Agents project using npm create..."
npm create cloudflare@latest -- --template cloudflare/agents-starter

# Note:
# - This will scaffold a new project with the agents framework.
# - You can then build and run your agent using standard Node.js tools.
# - The package supports real-time WebSocket communication, HTTP endpoints, and React integration.

# ---------------------------
# Additional Notes
# ---------------------------

# - Ensure you have a supported Node.js version installed.
# - No Python or other language package instructions were found.
# - No Docker or local server run instructions were specified in the installation docs.

echo "Installation complete. Refer to the documentation for usage and development details."