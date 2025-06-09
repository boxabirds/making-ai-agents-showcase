#!/bin/bash

# Installation instructions for smolagents Python package using uv package manager

# Initialize uv environment with Python 3.10 (example version, adjust if needed)
uv init
uv venv -p 3.10
source .venv/bin/activate

# Install smolagents package with toolkit extras
uv pip install smolagents[toolkit]

# Usage example (commented out, for user reference)
# python -c "
# from smolagents import CodeAgent, WebSearchTool, InferenceClientModel
# model = InferenceClientModel()
# agent = CodeAgent(tools=[WebSearchTool()], model=model, stream_outputs=True)
# agent.run('How many seconds would it take for a leopard at full speed to run through Pont des Arts?')
# "

# CLI usage examples (commented out, for user reference)
# smolagent \"Plan a trip to Tokyo, Kyoto and Osaka between Mar 28 and Apr 7.\" --model-type \"InferenceClientModel\" --model-id \"Qwen/Qwen2.5-Coder-32B-Instruct\" --imports \"pandas numpy\" --tools \"web_search\"
# webagent \"go to xyz.com/men, get to sale section, click the first clothing item you see. Get the product details, and the price, return them. note that I'm shopping from France\" --model-type \"LiteLLMModel\" --model-id \"gpt-4o\"