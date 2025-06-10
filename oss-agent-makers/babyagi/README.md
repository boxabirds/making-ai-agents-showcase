# BabyAGI Package: Comprehensive Guide to Creating and Running a Python ReAct Agent with Tool Calling

This document provides an exhaustive guide on how to use the BabyAGI package API to create an autonomous agent that can be run directly in Python (e.g., `python agent.py`). It also explains how to create a Python ReAct agent with tool calling capabilities using BabyAGI's framework. The guide is grounded extensively with references to source code files and examples within the package.

---

## Table of Contents

1. [Overview of BabyAGI](#overview-of-babyagi)
2. [Setting Up and Running a Basic BabyAGI Agent](#setting-up-and-running-a-basic-babyagi-agent)
3. [Creating a Python ReAct Agent with Tool Calling](#creating-a-python-react-agent-with-tool-calling)
4. [Key Source Code References](#key-source-code-references)
5. [Summary and Best Practices](#summary-and-best-practices)

---

## Overview of BabyAGI

BabyAGI is an experimental framework designed for building autonomous agents that can self-build and self-manage functions. It uses a function framework called **functionz** to store, manage, and execute functions from a database, with dependency tracking, secret key management, and a dashboard for monitoring.

- The framework supports registering Python functions with metadata, dependencies, and key dependencies.
- It provides a dashboard accessible via a web server for managing functions and keys.
- It supports loading function packs (collections of related functions).
- It integrates with LLMs (e.g., OpenAI GPT models) for reasoning and function execution.
- It supports advanced agent patterns like ReAct (Reasoning + Acting) with tool calling.

For more background, see the [README.md](output/cache/yoheinakajima/babyagi/README.md) in the package root.

---

## Setting Up and Running a Basic BabyAGI Agent

### 1. Installation

Install BabyAGI via pip:

```bash
pip install babyagi
```

### 2. Register Functions and Add API Keys

You register functions using the `@babyagi.register_function()` decorator. Functions can depend on other functions and require secret keys.

Example from `examples/simple_example.py`:

```python
import babyagi
import os

# Add OpenAI API key for embedding and descriptions
babyagi.add_key_wrapper('openai_api_key', os.environ['OPENAI_API_KEY'])

@babyagi.register_function()
def world():
    return "world"

@babyagi.register_function(dependencies=["world"])
def hello_world():
    x = world()
    return f"Hello {x}!"

print(hello_world())
```

### 3. Create and Run the Web Dashboard

The dashboard is a Flask app created with:

```python
app = babyagi.create_app('/dashboard')
```

Run the app:

```python
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
```

This serves the dashboard at `http://localhost:8080/dashboard`.

Example from `examples/quickstart_example.py`:

```python
import babyagi
import os

app = babyagi.create_app('/dashboard')

babyagi.add_key_wrapper('openai_api_key', os.environ['OPENAI_API_KEY'])

@app.route('/')
def home():
    return 'Welcome to the main app. Visit <a href="/dashboard">/dashboard</a> for BabyAGI dashboard.'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
```

---

## Creating a Python ReAct Agent with Tool Calling

The BabyAGI package includes a draft implementation of a ReAct agent that uses tool calling with LLMs and function execution. This is found in:

- `babyagi/functionz/packs/drafts/react_agent.py`
- `babyagi/functionz/packs/default/function_calling_chat.py`

### 1. Understanding the ReAct Agent (`react_agent.py`)

The `react_agent` function is a registered function that:

- Retrieves all available functions from the BabyAGI function database.
- Converts function signatures to JSON schema for LLM tool calling.
- Uses LiteLLM (a lightweight LLM interface) to perform chain-of-thought reasoning.
- Calls functions dynamically based on LLM tool calls.
- Maintains a history of function calls to avoid repetition.
- Iterates reasoning and function execution up to a max iteration count.
- Returns a detailed reasoning path and final answer.

Key points from `react_agent.py`:

- Uses `get_all_functions_wrapper()`, `get_function_wrapper()`, and `execute_function_wrapper()` to interact with the function database.
- Maps Python types to JSON schema for tool parameter definitions.
- Uses `litellm.completion()` with `tools` parameter to enable function calling.
- Handles function call results and appends them to the chat context for further reasoning.

### 2. Using the Chat with Functions (`function_calling_chat.py`)

This function provides a chat interface that:

- Accepts chat history and a list of available function names.
- Validates and prepares the chat context.
- Fetches function metadata and prepares tools for LiteLLM.
- Calls LiteLLM to get responses and function calls.
- Executes function calls and appends results to the chat.
- Returns the final assistant response.

This is a simpler interface for tool calling chat agents.

### 3. How to Create and Run Your Own ReAct Agent

You can create a Python script `agent.py` like this:

```python
import babyagi
import os

# Add your OpenAI API key
babyagi.add_key_wrapper('openai_api_key', os.environ['OPENAI_API_KEY'])

# Load the react_agent function pack (draft)
babyagi.load_functions("functionz/packs/drafts/react_agent")

# Import the react_agent function
from babyagi.functionz.packs.drafts.react_agent import react_agent

if __name__ == "__main__":
    # Example input task
    task = "Find the current weather in New York and summarize it."

    # Run the react agent with the task
    result = react_agent(task)

    print("Agent output:")
    print(result)
```

Run it with:

```bash
python agent.py
```

This will:

- Use the registered `react_agent` function.
- Use the BabyAGI function database to find and call functions.
- Use LiteLLM to reason and call tools.
- Output detailed reasoning and final answer.

### 4. Using the Chat Interface for Tool Calling

Alternatively, you can use the `chat_with_functions` function from `function_calling_chat.py` to build a chat-based ReAct agent:

```python
import babyagi
import os
from babyagi.functionz.packs.default.function_calling_chat import chat_with_functions

babyagi.add_key_wrapper('openai_api_key', os.environ['OPENAI_API_KEY'])

# List of function names you want the agent to use
available_functions = ["function1", "function2"]

# Example chat history
chat_history = [
    {"role": "user", "message": "Please help me with task X."}
]

response = chat_with_functions(chat_history, available_functions)

print("Chat agent response:")
print(response)
```

---

## Key Source Code References

| File | Description | Relevant Lines/Functions |
|-------|-------------|-------------------------|
| `examples/simple_example.py` | Basic example of registering functions and running dashboard | Lines 1-30 |
| `examples/quickstart_example.py` | Minimal example to start dashboard and add API key | Lines 1-20 |
| `examples/custom_route_example.py` | Example of custom Flask routes with BabyAGI | Lines 1-25 |
| `babyagi/functionz/packs/drafts/react_agent.py` | Draft ReAct agent implementation with tool calling | Entire file (~150 lines) |
| `babyagi/functionz/packs/default/function_calling_chat.py` | Chat interface with tool calling and function execution | Entire file (~150 lines) |
| `README.md` | Comprehensive documentation and usage guide | Entire file |

---

## Summary and Best Practices

- **Start simple:** Use `register_function` to register your Python functions with metadata and dependencies.
- **Add your API keys:** Use `add_key_wrapper` to add keys like OpenAI API keys.
- **Run the dashboard:** Use `create_app` to create and run the Flask dashboard for function management.
- **Use draft ReAct agents:** Load and use the `react_agent` function for advanced chain-of-thought reasoning with tool calling.
- **Use chat interface:** Use `chat_with_functions` for chat-based agents that call functions dynamically.
- **Refer to examples:** The `examples/` directory contains runnable scripts demonstrating usage.
- **Explore function packs:** BabyAGI supports loading function packs for modular function management.
- **Check logs and dashboard:** Use the dashboard to monitor function executions and manage keys.

---

This guide should enable you to create and run autonomous agents using BabyAGI, including advanced ReAct agents with tool calling, leveraging the package's function database and LLM integration.

For more details, consult the source files and the README in the package root.

---

# Appendix: Minimal `agent.py` Example for ReAct Agent

```python
import babyagi
import os

# Add OpenAI API key
babyagi.add_key_wrapper('openai_api_key', os.environ['OPENAI_API_KEY'])

# Load the react_agent draft pack
babyagi.load_functions("functionz/packs/drafts/react_agent")

from babyagi.functionz.packs.drafts.react_agent import react_agent

if __name__ == "__main__":
    task = "Write a summary of the latest news about AI."
    output = react_agent(task)
    print(output)
```

Run:

```bash
python agent.py
```

---

# References

- BabyAGI GitHub repo: https://github.com/yoheinakajima/babyagi
- BabyAGI README: [README.md](output/cache/yoheinakajima/babyagi/README.md)
- Example scripts: `examples/quickstart_example.py`, `examples/simple_example.py`
- Draft ReAct agent: `babyagi/functionz/packs/drafts/react_agent.py`
- Chat with functions: `babyagi/functionz/packs/default/function_calling_chat.py`