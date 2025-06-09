#!/bin/bash

# Installation script for Ax LLM Typescript package

# Client and Server are the same here since this is a Typescript package used as a library

# ---------------------------
# Client Installation
# ---------------------------

# Install the Ax package from npm using npm (preferred single package manager)
npm install @ax-llm/ax

# Alternatively, you can use yarn (uncomment if preferred)
# yarn add @ax-llm/ax

# ---------------------------
# Server / Running Local Server
# ---------------------------

# This package does not require running a separate server.
# It is a Typescript library to be used in your Node.js environment.

# ---------------------------
# Node.js Version Check
# ---------------------------

# Check if node is installed and version is supported (assumed >=14)
if ! command -v node &> /dev/null
then
    echo "Node.js is not installed. Please install Node.js version 14 or higher."
    exit 1
fi

NODE_VERSION=$(node -v | sed 's/v//g' | cut -d. -f1)
if [ "$NODE_VERSION" -lt 14 ]; then
    echo "Node.js version 14 or higher is required. Current version: $(node -v)"
    exit 1
fi

echo "Ax package installed. You can now import and use '@ax-llm/ax' in your Typescript or Javascript project."