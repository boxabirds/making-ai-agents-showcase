# Comprehensive Guide to Using the Google ADK Python Package to Create and Run Agents with Tool Calling (ReAct Style)

This document provides an exhaustive, detailed guide on how to use the Google ADK Python package to create an agent that can be run directly in Python (e.g., `python agent.py`). It also answers the question: "How can I use this API to create a Python ReAct agent with tool calling?" The guide includes references to source code files and explanations of key components, highlighting specialist tools and scaffolding utilities provided by the package.

---

## Table of Contents

1. [Overview of the Package and Agent Concept](#overview)
2. [Creating a Basic Agent](#basic-agent)
3. [Using Tools with Agents](#tools-with-agents)
4. [Creating a Python ReAct Agent with Tool Calling](#react-agent)
5. [Running the Agent Directly in Python](#running-agent)
6. [References to Source Code and Documentation](#references)

---

## 1. Overview of the Package and Agent Concept <a name="overview"></a>

The Google ADK Python package provides a framework to build AI agents that can interact with language models and tools. The core abstraction is the `Agent` class, which represents an AI assistant capable of processing instructions, using tools, and generating responses.

- The main agent class is `LlmAgent` (alias `Agent`), defined in:
  - `src/google/adk/agents/llm_agent.py`
- Tools are modular components that the agent can call to perform specific functions.
- The package supports advanced features like toolsets, function tools, and integration with Langchain tools.

---

## 2. Creating a Basic Agent <a name="basic-agent"></a>

A minimal agent can be created by instantiating the `Agent` class with a model, name, description, instructions, and optionally tools.

Example from `contributing/samples/quickstart/agent.py`:

```python
from google.adk.agents import Agent

def get_weather(city: str) -> dict:
    """Returns weather info for a city."""
    if city.lower() == "new york":
        return {
            "status": "success",
            "report": "The weather in New York is sunny with a temperature of 25 degrees Celsius."
        }
    else:
        return {"status": "error", "error_message": f"Weather info for '{city}' not available."}

def get_current_time(city: str) -> dict:
    """Returns current time in a city."""
    import datetime
    from zoneinfo import ZoneInfo

    if city.lower() == "new york":
        tz_identifier = "America/New_York"
    else:
        return {"status": "error", "error_message": f"Timezone info for {city} not available."}

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    report = f"The current time in {city} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"
    return {"status": "success", "report": report}

root_agent = Agent(
    name="weather_time_agent",
    model="gemini-2.0-flash",
    description="Agent to answer questions about the time and weather in a city.",
    instruction="I can answer your questions about the time and weather in a city.",
    tools=[get_weather, get_current_time],
)
```

- The `tools` parameter accepts Python functions directly, which are wrapped internally as tools.
- The `Agent` class automatically converts these functions into callable tools.

---

## 3. Using Tools with Agents <a name="tools-with-agents"></a>

### FunctionTool: Wrapping Python Functions as Tools

The package provides a `FunctionTool` class to wrap Python functions as tools with metadata and automatic function calling support.

- Defined in `src/google/adk/tools/function_tool.py`
- Automatically extracts function signature and docstring.
- Supports async functions and streaming.
- Validates mandatory arguments before invocation.

Example usage (internal, but you can pass functions directly to `Agent` which wraps them):

```python
from google.adk.tools.function_tool import FunctionTool

def add(x: int, y: int) -> int:
    return x + y

add_tool = FunctionTool(add)
```

### LangchainTool: Using Langchain Structured Tools

The package supports integration with Langchain's `StructuredTool` for advanced tool definitions.

Example from `contributing/samples/langchain_structured_tool_agent/agent.py`:

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

- This example shows how to create a ReAct-style agent with tool calling using Langchain's structured tools wrapped by `LangchainTool`.
- The `StructuredTool.from_function` method creates a tool with argument schema validation.
- The agent is instantiated with the tool wrapped in `LangchainTool`.

---

## 4. Creating a Python ReAct Agent with Tool Calling <a name="react-agent"></a>

To create a ReAct agent with tool calling:

1. Define your tool functions or use Langchain structured tools.
2. Wrap them using `FunctionTool` or `LangchainTool`.
3. Instantiate an `Agent` with the model, instructions, and tools.
4. Use the agent's API to run it interactively or programmatically.

Example (combining above concepts):

```python
from google.adk.agents import Agent
from google.adk.tools.langchain_tool import LangchainTool
from langchain_core.tools.structured import StructuredTool
from pydantic import BaseModel

# Define a tool function
def add(x, y) -> int:
    return x + y

# Define argument schema
class AddSchema(BaseModel):
    x: int
    y: int

# Create a Langchain structured tool
add_tool = StructuredTool.from_function(
    add,
    name="add",
    description="Adds two numbers",
    args_schema=AddSchema,
)

# Wrap the Langchain tool for ADK
wrapped_tool = LangchainTool(tool=add_tool)

# Create the agent
agent = Agent(
    model="gemini-2.0-flash-001",
    name="react_agent",
    description="A ReAct agent with tool calling.",
    instruction="You are a helpful assistant that can call tools to add numbers.",
    tools=[wrapped_tool],
)

# Now you can run the agent in your Python script
```

---

## 5. Running the Agent Directly in Python <a name="running-agent"></a>

To run the agent directly, create a Python script (e.g., `agent.py`) with the agent definition and add a main entry point to interact with it.

Example `agent.py`:

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

add_tool = StructuredTool.from_function(
    add,
    name="add",
    description="Adds two numbers",
    args_schema=AddSchema,
)

agent = Agent(
    model="gemini-2.0-flash-001",
    name="react_agent",
    description="A ReAct agent with tool calling.",
    instruction="You are a helpful assistant that can call tools to add numbers.",
    tools=[LangchainTool(tool=add_tool)],
)

def main():
    # Example interaction loop
    while True:
        user_input = input("User: ")
        if user_input.lower() in ("exit", "quit"):
            break
        # Here you would call the agent's run method or equivalent
        # For example (pseudo-code):
        # response = agent.run(user_input)
        # print("Agent:", response)
        print("Agent would process:", user_input)

if __name__ == "__main__":
    main()
```

- Replace the pseudo-code with actual agent invocation methods as per your integration.
- This script can be run with `python agent.py`.

---

## 6. References to Source Code and Documentation <a name="references"></a>

- **Agent class and core logic:**
  - `src/google/adk/agents/llm_agent.py` (implements `LlmAgent` which is aliased as `Agent`)
- **FunctionTool for wrapping Python functions:**
  - `src/google/adk/tools/function_tool.py`
- **LangchainTool integration:**
  - `contributing/samples/langchain_structured_tool_agent/agent.py`
- **Basic agent example with function tools:**
  - `contributing/samples/quickstart/agent.py`
- **ToolboxToolset example (toolset usage):**
  - `contributing/samples/toolbox_agent/agent.py`
- **Langchain StructuredTool usage:**
  - `langchain_core.tools.structured.StructuredTool` (external Langchain library)
- **Agent instantiation and usage pattern:**
  - See multiple sample agents in `contributing/samples/`

---

# Summary

- The Google ADK Python package provides a flexible `Agent` class to create AI agents.
- Tools can be simple Python functions wrapped automatically or explicitly wrapped using `FunctionTool`.
- For ReAct-style agents with tool calling, Langchain's `StructuredTool` can be wrapped with `LangchainTool`.
- Sample agents in the `contributing/samples/langchain_structured_tool_agent` directory demonstrate this pattern.
- Running the agent directly in Python involves defining the agent and adding a main loop or script entry point.
- The package includes advanced features like callbacks, code execution, and planning, but the basic usage is straightforward.

This guide should enable you to create, customize, and run agents with tool calling using the Google ADK Python package efficiently.