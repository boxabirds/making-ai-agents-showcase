#!/bin/bash

# Installation script for CAMEL Python package using uv package manager

# Initialize uv environment with required Python version (assuming Python 3.8+)
uv init
uv venv -p python3
source .venv/bin/activate

# Install CAMEL package from PyPI
uv pip install camel-ai

# Optional: Install CAMEL with web tools support
uv pip install 'camel-ai[web_tools]'

# Set up environment variable for OpenAI API key (replace with your actual key)
# export OPENAI_API_KEY='your_openai_api_key'

# Instructions for running a simple ChatAgent example (Python code)
# Save the following code in a file, e.g., chat_agent_example.py, and run it with Python
: '
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType
from camel.agents import ChatAgent
from camel.toolkits import SearchToolkit

model = ModelFactory.create(
  model_platform=ModelPlatformType.OPENAI,
  model_type=ModelType.GPT_4O,
  model_config_dict={"temperature": 0.0},
)

search_tool = SearchToolkit().search_duckduckgo

agent = ChatAgent(model=model, tools=[search_tool])

response_1 = agent.step("What is CAMEL-AI?")
print(response_1.msgs[0].content)

response_2 = agent.step("What is the Github link to CAMEL framework?")
print(response_2.msgs[0].content)
'

# No separate client/server instructions found; this is a Python package installation and usage script.