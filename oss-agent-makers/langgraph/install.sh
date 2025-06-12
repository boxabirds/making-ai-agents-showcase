#!/bin/bash

uv init
uv venv -p 3.12
uv add langgraph langchain-openai langchain-google
