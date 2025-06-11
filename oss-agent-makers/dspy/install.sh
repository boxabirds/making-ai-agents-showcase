#!/bin/bash
uv init --name "tech-writer-agent"
uv venv -p 3.12
source .venv/bin/activate
uv add dspy pydantic
