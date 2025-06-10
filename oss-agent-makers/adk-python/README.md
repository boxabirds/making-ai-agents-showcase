# How to Use the Google ADK Python API to Create a ReAct Agent with Tool Calling

This document provides an exhaustive guide on how to use the Google ADK Python package to create a ReAct (Reasoning and Acting) agent that can call tools. The guide is based on the analysis of the package's source code and sample agents.

---

## Overview

The Google ADK Python package provides a framework to build AI agents that can reason, act, and interact with external tools. The core class for creating an LLM-based agent is `LlmAgent` (aliased as `Agent`), which supports:

- Specifying an LLM model
- Providing instructions to guide the agent's behavior
- Registering tools (functions, toolsets, or tool wrappers)
- Handling agent transfer and multi-agent coordination
- Executing code blocks via code executors
- Using callbacks before/after model calls and tool calls

---

## Key Concepts

### Agent

- The main class to instantiate is `Agent` (which is an alias for `LlmAgent`).
- You specify the model, instructions, and tools when creating an agent.
- Tools can be simple Python functions, `BaseTool` instances, or `BaseToolset` instances.
- The agent can call these tools as part of its reasoning and acting process.

### Tools

- Tools are callable entities that the agent can invoke.
- They can be raw Python functions wrapped automatically by the framework.
- The package provides various tool wrappers, e.g., `LangchainTool`, `ToolboxToolset`.
- Tools can be grouped into toolsets for better organization.

### Instructions

- Instructions guide the agent's behavior.
- They can be static strings or async callables that return strings.
- There is support for both local instructions and global instructions (for root agents).

### Callbacks

- Callbacks can be registered to hook into the lifecycle of model calls and tool calls.
- These include before/after model callbacks and before/after tool callbacks.

---

## How to Create a ReAct Agent with Tool Calling

### Step 1: Import the Agent Class

```python
from google.adk.agents import Agent
```

The `Agent` class is the main entry point for creating an LLM-based agent.

### Step 2: Define or Import Tools

You can define simple Python functions as tools or use existing tool wrappers.

Example of a simple function tool:

```python
def get_weather(city: str) -> dict:
    if city.lower() == "new york":
        return {
            "status": "success",
            "report": "The weather in New York is sunny with a temperature of 25 degrees Celsius.",
        }
    else:
        return {
            "status": "error",
            "error_message": f"Weather information for '{city}' is not available.",
        }
```

Example of a function tool wrapped automatically by the agent:

```python
tools=[get_weather]
```

Alternatively, you can use more complex tool wrappers like `LangchainTool` or `ToolboxToolset`:

```python
from google.adk.tools.langchain_tool import LangchainTool
from langchain_core.tools.structured import StructuredTool
from pydantic import BaseModel

def add(x, y) -> int:
    return x + y

class AddSchema(BaseModel):
    x: int
    y: int

test_langchain_tool = StructuredTool.from_function(
    add,
    name="add",
    description="Adds two numbers",
    args_schema=AddSchema,
)

tools=[LangchainTool(tool=test_langchain_tool)]
```

Or using a toolbox toolset:

```python
from google.adk.tools.toolbox_toolset import ToolboxToolset

tools=[
    ToolboxToolset(
        server_url="http://127.0.0.1:5000",
        toolset_name="my-toolset"
    )
]
```

### Step 3: Create the Agent Instance

Create an agent by specifying the model, name, instructions, and tools:

```python
root_agent = Agent(
    model="gemini-2.0-flash",
    name="root_agent",
    instruction="You are a helpful assistant",
    tools=[
        # List your tools or toolsets here
    ],
)
```

Example with tools:

```python
root_agent = Agent(
    model="gemini-2.0-flash",
    name="weather_time_agent",
    description="Agent to answer questions about the time and weather in a city.",
    instruction="I can answer your questions about the time and weather in a city.",
    tools=[get_weather, get_current_time],
)
```

### Step 4: Use the Agent

Once created, the agent can be invoked to process inputs, reason, and call tools as needed. The exact invocation method depends on your application context (e.g., synchronous or asynchronous calls, streaming, etc.).

---

## Additional Features

### Code Execution

You can enable code execution within the agent by providing a `code_executor`:

```python
from google.adk.code_executors.built_in_code_executor import BuiltInCodeExecutor

agent = Agent(
    model="gemini-2.0-flash",
    code_executor=BuiltInCodeExecutor(),
    # other params...
)
```

### Callbacks

You can register callbacks to hook into the model and tool call lifecycle:

```python
def before_model_callback(ctx, request):
    # Modify request or short-circuit response
    return None

def after_tool_callback(tool, args, ctx, response):
    # Process tool response
    return None

agent = Agent(
    model="gemini-2.0-flash",
    before_model_callback=before_model_callback,
    after_tool_callback=after_tool_callback,
    # other params...
)
```

---

## Summary of Example Agents from the Package

### Quickstart Agent Example

- Defines two simple function tools: `get_weather` and `get_current_time`.
- Creates an agent with these tools and a simple instruction.
- Shows how to register plain Python functions as tools.

### Langchain Structured Tool Agent Example

- Defines a function `add` with a Pydantic schema for arguments.
- Wraps it as a Langchain `StructuredTool`.
- Uses `LangchainTool` wrapper to add it to the agent.
- Demonstrates integration with Langchain structured tools.

### Toolbox Toolset Agent Example

- Uses `ToolboxToolset` to add a set of tools served from a remote server.
- Shows how to add a toolset to the agent's tools list.

---

## Code Snippets from Examples

### Quickstart Agent (from `contributing/samples/quickstart/agent.py`)

```python
from google.adk.agents import Agent

def get_weather(city: str) -> dict:
    if city.lower() == "new york":
        return {
            "status": "success",
            "report": "The weather in New York is sunny with a temperature of 25 degrees Celsius.",
        }
    else:
        return {
            "status": "error",
            "error_message": f"Weather information for '{city}' is not available.",
        }

def get_current_time(city: str) -> dict:
    import datetime
    from zoneinfo import ZoneInfo

    if city.lower() == "new york":
        tz_identifier = "America/New_York"
    else:
        return {
            "status": "error",
            "error_message": f"Sorry, I don't have timezone information for {city}.",
        }

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    report = f'The current time in {city} is {now.strftime("%Y-%m-%d %H:%M:%S %Z%z")}'
    return {"status": "success", "report": report}

root_agent = Agent(
    name="weather_time_agent",
    model="gemini-2.0-flash",
    description="Agent to answer questions about the time and weather in a city.",
    instruction="I can answer your questions about the time and weather in a city.",
    tools=[get_weather, get_current_time],
)
```

### Langchain Structured Tool Agent (from `contributing/samples/langchain_structured_tool_agent/agent.py`)

```python
from google.adk.agents import Agent
from google.adk.tools.langchain_tool import LangchainTool
from langchain_core.tools.structured import StructuredTool
from pydantic import BaseModel

def add(x, y) -> int:
    return x + y

class AddSchema(BaseModel):
    x: int
    y: int

test_langchain_tool = StructuredTool.from_function(
    add,
    name="add",
    description="Adds two numbers",
    args_schema=AddSchema,
)

root_agent = Agent(
    model="gemini-2.0-flash-001",
    name="test_app",
    description="A helpful assistant for user questions.",
    instruction=(
        "You are a helpful assistant for user questions, you have access to a"
        " tool that adds two numbers."
    ),
    tools=[LangchainTool(tool=test_langchain_tool)],
)
```

### Toolbox Toolset Agent (from `contributing/samples/toolbox_agent/agent.py`)

```python
from google.adk.agents import Agent
from google.adk.tools.toolbox_toolset import ToolboxToolset

root_agent = Agent(
    model="gemini-2.0-flash",
    name="root_agent",
    instruction="You are a helpful assistant",
    tools=[
        ToolboxToolset(
            server_url="http://127.0.0.1:5000",
            toolset_name="my-toolset"
        )
    ],
)
```

---

## Summary

To create a ReAct agent with tool calling using the Google ADK Python package:

1. Import the `Agent` class.
2. Define or import tools (functions, tool wrappers, or toolsets).
3. Instantiate the `Agent` with a model, instructions, and the tools.
4. Optionally configure advanced features like code execution and callbacks.
5. Use the agent instance to process inputs and perform reasoning with tool calls.

The package provides flexible ways to integrate tools, including simple Python functions, Langchain structured tools, and remote toolsets, enabling powerful ReAct agent capabilities.

---

This concludes the detailed guide on using the Google ADK Python package to create a ReAct agent with tool calling.