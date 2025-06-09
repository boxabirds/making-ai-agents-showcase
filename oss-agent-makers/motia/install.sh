#!/bin/bash

# Motia Installation Script

# This script installs the Motia package and provides instructions for running the client and server.

# ---------------------------
# Installation (JavaScript/TypeScript)
# ---------------------------
npm install motia
# or
# yarn add motia
# or
# pnpm add motia

# ---------------------------
# Running the Server (Development)
# ---------------------------
# To start the Motia development server and Workbench (visual interface):
# This will launch the Workbench at http://localhost:3000
npx motia dev

# ---------------------------
# Running the Client
# ---------------------------
# The client usage depends on your application code.
# For example, you can trigger API steps using curl:
# curl -X POST http://localhost:3000/default -H "Content-Type: application/json" -d '{}'

# Or emit events using the Motia CLI:
# npx motia emit --topic test-state --message '{}'

# ---------------------------
# Notes
# ---------------------------
# - The Motia CLI provides commands like `motia init`, `motia install`, `motia build`, and `motia dev`.
# - For full documentation, visit https://motia.dev/docs
# - This script assumes Node.js is installed and available in your environment.