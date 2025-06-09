#!/bin/bash

# VoltAgent Installation Script
# This script installs VoltAgent using npm as per the official package instructions.
# Node.js version >= 20 and pnpm >= 8 are required.

# Check Node.js version
if ! command -v node &> /dev/null
then
    echo "Node.js is not installed. Please install Node.js version 20 or higher."
    exit 1
fi

NODE_VERSION=$(node -v | sed 's/v//g' | cut -d. -f1)
if [ "$NODE_VERSION" -lt 20 ]; then
    echo "Node.js version 20 or higher is required. Current version: $(node -v)"
    exit 1
fi

# Check pnpm version
if ! command -v pnpm &> /dev/null
then
    echo "pnpm is not installed. Installing pnpm..."
    npm install -g pnpm
fi

PNPM_VERSION=$(pnpm -v | cut -d. -f1)
if [ "$PNPM_VERSION" -lt 8 ]; then
    echo "pnpm version 8 or higher is required. Current version: $(pnpm -v)"
    exit 1
fi

# Install create-voltagent-app globally
echo "Installing create-voltagent-app CLI tool globally..."
npm install -g create-voltagent-app

# Create a new VoltAgent project
echo "Creating a new VoltAgent project..."
create-voltagent-app@latest

# Navigate to the new project directory (user should do this manually)
echo "Navigate to your new project directory and run the development server:"
echo "cd <your-project-directory>"
echo "npm run dev"

# Client and Server instructions
echo ""
echo "# Client and Server Instructions"
echo "# The VoltAgent framework runs a local development server."
echo "# After running 'npm run dev', you should see the server start message:"
echo "# VOLTAGENT SERVER STARTED SUCCESSFULLY"
echo "# HTTP Server: http://localhost:3141"
echo "# You can interact with your agent via the VoltOps LLM Observability Platform at https://console.voltagent.dev"
echo "# Open the platform, find your agent, and start chatting."

exit 0