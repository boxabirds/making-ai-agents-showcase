#!/bin/bash
uv init
uv venv -p 3.10
source .venv/bin/activate
uv add dspy pydantic
