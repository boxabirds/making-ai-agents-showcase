#!/bin/bash

# Installation script for Dify Python SDK using uv package manager

# Initialize uv environment with required Python version (assuming Python 3.10 as example)
uv init
uv venv -p 3.10
source .venv/bin/activate

# Install dify-client package using uv pip
uv pip install dify-client

# Usage instructions for client (commented for user reference)
: '
# Example usage for CompletionClient (blocking response_mode)
from dify_client import CompletionClient

api_key = "your_api_key"
completion_client = CompletionClient(api_key)
completion_response = completion_client.create_completion_message(inputs={"query": "What\'s the weather like today?"}, response_mode="blocking", user="user_id")
completion_response.raise_for_status()
result = completion_response.json()
print(result.get("answer"))

# Example usage for ChatClient (streaming response_mode)
import json
from dify_client import ChatClient

api_key = "your_api_key"
chat_client = ChatClient(api_key)
chat_response = chat_client.create_chat_message(inputs={}, query="Hello", user="user_id", response_mode="streaming")
chat_response.raise_for_status()

for line in chat_response.iter_lines(decode_unicode=True):
    line = line.split("data:", 1)[-1]
    if line.strip():
        line = json.loads(line.strip())
        print(line.get("answer"))
'

# Note: This project also supports running the full Dify server via Docker Compose.
# To run the server locally:
# cd output/cache/langgenius/dify/docker
# cp .env.example .env
# docker compose up -d
# Access the dashboard at http://localhost/install

# End of script