#!/bin/bash

# LangGraph Multi-Agent Swarm Python Package Installation Script

# This script installs the langgraph-swarm package using the Python package manager "uv".
# It assumes you have Python installed and uv available.
# If uv is not installed, you can install it via pip: pip install uv

# Initialize a new uv environment with the required Python version (adjust version as needed)
# uv init
# uv venv -p python3.10
# source .venv/bin/activate

# Install the langgraph-swarm package and its dependencies using uv pip
uv venv -p 3.11
uv pip install langgraph-swarm langchain-openai

# Export your OpenAI API key (replace <your_api_key> with your actual key)
# export OPENAI_API_KEY=<your_api_key>

# Usage example (commented out, run in your Python environment)
# python -c "
# from langchain_openai import ChatOpenAI
# from langgraph.checkpoint.memory import InMemorySaver
# from langgraph.prebuilt import create_react_agent
# from langgraph_swarm import create_handoff_tool, create_swarm
#
# model = ChatOpenAI(model='gpt-4o')
#
# def add(a: int, b: int) -> int:
#     return a + b
#
# alice = create_react_agent(
#     model,
#     [add, create_handoff_tool(agent_name='Bob')],
#     prompt='You are Alice, an addition expert.',
#     name='Alice',
# )
#
# bob = create_react_agent(
#     model,
#     [create_handoff_tool(agent_name='Alice', description='Transfer to Alice, she can help with math')],
#     prompt='You are Bob, you speak like a pirate.',
#     name='Bob',
# )
#
# checkpointer = InMemorySaver()
# workflow = create_swarm(
#     [alice, bob],
#     default_active_agent='Alice'
# )
# app = workflow.compile(checkpointer=checkpointer)
#
# config = {'configurable': {'thread_id': '1'}}
# turn_1 = app.invoke(
#     {'messages': [{'role': 'user', 'content': \"i'd like to speak to Bob\"}]},
#     config,
# )
# print(turn_1)
# turn_2 = app.invoke(
#     {'messages': [{'role': 'user', 'content': \"what's 5 + 7?\"}]},
#     config,
# )
# print(turn_2)
# "