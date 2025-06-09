#!/bin/bash

# Installation script for Magma framework package usage

# Client and Server are the same here since this is a library package for Node.js/TypeScript usage

# Install Magma package using npm
echo "Installing Magma package..."
npm install @pompeii-labs/magma

# Example usage comment:
# To create and run your first agent, you can use the following TypeScript code:
# 
# import { MagmaAgent } from "@pompeii-labs/magma";
# 
# class MyAgent extends MagmaAgent {
#     getSystemPrompts() {
#         return [{
#             role: "system",
#             content: "You are a friendly assistant who loves dad jokes"
#         }];
#     }
# }
# 
# const myAgent = new MyAgent();
# const reply = await myAgent.main();
# console.log(reply.content);

# Note: Ensure you have a supported Node.js version installed before running this script.