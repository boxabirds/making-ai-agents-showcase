#!/bin/bash

# Griptape Python Package Installation Script

# Initialize a uv virtual environment with the required Python version (example: 3.10)
uv init
uv venv -p 3.10
source .venv/bin/activate

# Install Griptape package using uv pip
uv pip install griptape

# Note: Griptape is a Python framework and does not require separate client/server setup.
# You can use it directly in your Python projects after installation.

# Example usage (uncomment to run):
# python -c "
# from griptape.drivers.prompt.openai import OpenAiChatPromptDriver
# from griptape.rules import Rule
# from griptape.tasks import PromptTask
#
# task = PromptTask(
#     prompt_driver=OpenAiChatPromptDriver(model='gpt-4.1'),
#     rules=[Rule('Keep your answer to a few sentences.')]
# )
#
# result = task.run('How do I do a kickflip?')
# print(result.value)
# "