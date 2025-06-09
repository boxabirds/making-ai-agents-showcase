#!/bin/bash

# TypedAI Installation Script
# This script installs the TypedAI package and provides instructions for running the CLI locally or in Docker.

# Check Node.js version (TypedAI requires Node.js >= 20.6.0)
NODE_VERSION=$(node -v | sed 's/v//')
REQUIRED_VERSION="20.6.0"

version_greater_equal() {
  # Compare two semantic versions, returns 0 if $1 >= $2
  [ "$(printf '%s\n' "$2" "$1" | sort -V | head -n1)" = "$2" ]
}

if ! version_greater_equal "$NODE_VERSION" "$REQUIRED_VERSION"; then
  echo "Node.js version $REQUIRED_VERSION or higher is required. Current version: $NODE_VERSION"
  echo "Please install or upgrade Node.js."
  exit 1
fi

# Install dependencies using npm (assuming package.json is present)
echo "Installing dependencies..."
npm install

# Client and Server instructions

# Client: CLI usage
echo ""
echo "To use the TypedAI CLI locally, you can run commands like:"
echo "  ./ai query \"What test frameworks does this repository use?\""
echo "  ./ai code \"Add error handling to the user authentication function\""
echo "  ./ai research \"Latest developments in large language models\""
echo ""
echo "The 'ai' script runs locally and provides access to all CLI agents including the specialized 'codeAgent' for autonomous code editing tasks."

# Server: Docker usage
echo ""
echo "To run TypedAI in Docker for isolation, use the 'aid' script inside the Docker container."
echo "You can build and run the Docker container using the provided Dockerfile in the repository root."
echo "Example Docker commands:"
echo "  docker build -t typedai ."
echo "  docker run -it --env-file variables/local.env typedai aid <command>"
echo ""
echo "For more detailed CLI documentation, visit: https://typedai.dev/cli-usage/"

# End of script