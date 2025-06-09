#!/bin/bash

# BaseAI Installation and Usage Script
# This script installs BaseAI as a package and provides instructions to run client and server components.

# 1. Install BaseAI package (TypeScript/JavaScript)
# Using npm as the package manager (preferred bun instructions not found)
npm install @baseai/core

# 2. Initialize a new BaseAI project
npx baseai@latest init

# 3. Add API keys
# Create a .env file in your project root and add your API keys as below:
cat <<EOL > .env
# !! SERVER SIDE ONLY !!
# Keep all your API keys secret — use only on the server side.

# Langbase API key for your User or Org account.
LANGBASE_API_KEY=

# Local only keys for providers you use
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
COHERE_API_KEY=
FIREWORKS_API_KEY=
GOOGLE_API_KEY=
GROQ_API_KEY=
MISTRAL_API_KEY=
PERPLEXITY_API_KEY=
TOGETHER_API_KEY=
XAI_API_KEY=
EOL

# 4. Create a new AI agent pipe
npx baseai@latest pipe

# 5. Run the BaseAI server (server instructions)
echo "Starting BaseAI server..."
npx baseai@latest dev

# 6. Run your AI agent client code
# Example: run index.ts that uses the pipe
echo "Run your client code with:"
echo "npx tsx index.ts"

# Notes:
# - Make sure to import 'dotenv/config' in your Node.js client code to load environment variables.
# - The BaseAI framework is TypeScript-first.
# - For streaming output, listen to events as shown in the README example.

# End of script