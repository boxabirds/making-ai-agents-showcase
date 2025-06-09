#!/bin/bash

# Installation script for Eko JavaScript framework package

# Client and Server are the same here since Eko is a JavaScript framework usable in both browser and Node.js environments

# Install Eko package using pnpm (preferred package manager as per README)
echo "Installing Eko package..."
pnpm install @eko-ai/eko

# Note: Ensure you have a supported Node.js version installed before running this script

# Example usage snippet (to be run in your JavaScript/TypeScript environment):
# 
# const llms = {
#   default: {
#     provider: "anthropic",
#     model: "claude-sonnet-4-20250514",
#     apiKey: "your-api-key"
#   },
#   openai: {
#     provider: "openai",
#     model: "gpt-4.1",
#     apiKey: "your-api-key"
#   }
# };
# 
# let agents = [new BrowserAgent(), new FileAgent()];
# let eko = new Eko({ llms, agents });
# let result = await eko.run("Search for the latest news about Musk, summarize and save to the desktop as Musk.md");

echo "Eko installation complete. Please refer to https://eko.fellou.ai/docs/getting-started/quickstart/ for usage instructions."