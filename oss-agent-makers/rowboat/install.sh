#!/bin/bash

# Installation and usage script for Rowboat project

# ---------------------------
# Client and Server Setup
# ---------------------------

# Step 1: Set your OpenAI API key environment variable
# Replace 'your-openai-api-key' with your actual OpenAI API key
export OPENAI_API_KEY=your-openai-api-key

# Step 2: Clone the Rowboat repository and navigate into it
git clone git@github.com:rowboatlabs/rowboat.git
cd rowboat

# Step 3: Create necessary data directories for uploads, qdrant, and mongo
mkdir -p data/uploads
mkdir -p data/qdrant
mkdir -p data/mongo

# Step 4: Start the Rowboat server using docker-compose with required profiles
# This will build and start the server with RAG support and workers
USE_RAG=true
USE_RAG_UPLOADS=true
USE_RAG_SCRAPING=true

CMD="docker-compose"
CMD="$CMD --profile setup_qdrant"
CMD="$CMD --profile qdrant"
CMD="$CMD --profile rag_text_worker"
CMD="$CMD --profile rag_files_worker"

if [ "$USE_RAG_SCRAPING" = "true" ]; then
  CMD="$CMD --profile rag_urls_worker"
fi

CMD="$CMD up --build"

echo "Running: $CMD"
exec $CMD

# ---------------------------
# Python SDK Installation
# ---------------------------

# Install the Python SDK package 'rowboat' using pip
pip install rowboat

# ---------------------------
# Usage Notes
# ---------------------------

# Access the Rowboat app at http://localhost:3000 after the server is running.

# To interact with the agents, you can use either:
# 1. HTTP API (curl example):
# curl --location 'http://localhost:3000/api/v1/<PROJECT_ID>/chat' \
# --header 'Content-Type: application/json' \
# --header 'Authorization: Bearer <API_KEY>' \
# --data '{
#     "messages": [
#         {
#             "role": "user",
#             "content": "tell me the weather in london in metric units"
#         }
#     ],
#     "state": null
# }'

# 2. Python SDK example:
# from rowboat import Client, StatefulChat
# from rowboat.schema import UserMessage, SystemMessage
#
# client = Client(
#     host="http://localhost:3000",
#     project_id="<PROJECT_ID>",
#     api_key="<API_KEY>"
# )
#
# chat = StatefulChat(client)
# response = chat.run("What's the weather in London?")
# print(response)

# Replace <PROJECT_ID> and <API_KEY> with your actual project ID and API key from Rowboat settings.