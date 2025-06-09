#!/bin/bash

# Installation script for Flowise project using package form (npm global install)

# Check Node.js version (must be >= 18.15.0)
if ! command -v node &> /dev/null
then
    echo "Node.js is not installed. Please install Node.js >= 18.15.0 from https://nodejs.org/en/download"
    exit 1
fi

NODE_VERSION=$(node -v | sed 's/v//')
REQUIRED_VERSION="18.15.0"

version_greater_equal() {
  # Compare two version strings $1 and $2, returns 0 if $1 >= $2
  [ "$(printf '%s\n' "$2" "$1" | sort -V | head -n1)" = "$2" ]
}

if ! version_greater_equal "$NODE_VERSION" "$REQUIRED_VERSION"; then
  echo "Node.js version $NODE_VERSION is less than required $REQUIRED_VERSION. Please upgrade Node.js."
  exit 1
fi

# Install Flowise globally using npm
echo "Installing Flowise globally via npm..."
npm install -g flowise

# Start Flowise server
echo "Starting Flowise server..."
npx flowise start &

# Wait a few seconds for server to start
sleep 5

echo "Flowise should now be running. Open your browser at http://localhost:3000"

# End of script