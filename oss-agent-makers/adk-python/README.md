# ADK-Python Tech Writer Agent

This directory contains a Tech Writer agent implementation using Google's Agent Development Kit (ADK) Python package. The agent analyzes codebases and creates technical documentation using a ReAct (Reasoning and Acting) pattern.

## Tech Writer Agent Features

- **ReAct Pattern**: Uses reasoning and acting steps to analyze codebases
- **Tool Calling**: Integrates file discovery and reading tools
- **Command-line Interface**: Supports analyzing local directories or GitHub repositories
- **Flexible Output**: Generates documentation in various formats

## Files in this Directory

- `tech_writer_agent.py` - The main agent implementation with tools
- `tech_writer_runner.py` - CLI runner for batch processing
- `tech_writer.sh` - Shell script wrapper for easy execution
- `test_tech_writer.py` - Test script to verify the agent works
- `agent.py` - Simple hello world agent example
- `agent.sh` - Shell script for the hello world agent

## Usage

### Interactive Mode

Run the agent in interactive mode:

```bash
python tech_writer_agent.py
```

### Command-line Mode

Use the runner for batch processing:

```bash
# Analyze a local directory
python tech_writer_runner.py -d ./my-project -p prompts/analyze.txt

# Analyze a GitHub repository
python tech_writer_runner.py -r https://github.com/user/repo -p prompts/analyze.txt

# Or use the shell script
./tech_writer.sh -d ./my-project -p prompts/analyze.txt
```

### Testing

Run the test script to verify the installation:

```bash
python test_tech_writer.py
```

---

# Google ADK Python Package - Agent Usage and ReAct Agent with Tool Calling Guide

This document provides an exhaustive guide on how to use the Google ADK Python package to create and run agents directly in Python, with a focus on creating a Python ReAct agent with tool calling capabilities. The guide is grounded exclusively in the source code and sample agents provided in the package.

---

## 1. How to Use the API to Create and Run an Agent Directly in Python

### Overview

The core class to create an agent is `Agent` (alias for `LlmAgent`) from the module `google.adk.agents`. An agent is configured with a model, instructions, tools, and optionally planners and callbacks. The agent can then be run using a runner such as `InMemoryRunner` or `Runner`.

### Key Classes and Modules

- **Agent (LlmAgent)**: `google.adk.agents.llm_agent.Agent`  
  This is the main class to instantiate an agent. It supports specifying the model, instructions, tools, planners, and callbacks.  
  - Source: `src/google/adk/agents/llm_agent.py` (lines ~100-400)
- **Runner / InMemoryRunner**: Used to run the agent asynchronously with session management.  
  - Example usage in sample: `contributing/samples/hello_world/main.py`
- **Tools**: Functions or tool classes that the agent can call during execution.

### Minimal Example to Create and Run an Agent

Refer to the sample `hello_world` agent and main runner:

- **Agent definition**: `contributing/samples/hello_world/agent.py`  
  Defines two tools: `roll_die` and `check_prime` as Python functions, then creates an `Agent` with these tools and instructions.

```python
import random
from google.adk import Agent
from google.genai import types

def roll_die(sides: int, tool_context) -> int:
    result = random.randint(1, sides)
    # Store rolls in tool_context state for later reference
    if 'rolls' not in tool_context.state:
        tool_context.state['rolls'] = []
    tool_context.state['rolls'].append(result)
    return result

async def check_prime(nums: list[int]) -> str:
    primes = set()
    for number in nums:
        if number <= 1:
            continue
        is_prime = True
        for i in range(2, int(number**0.5) + 1):
            if number % i == 0:
                is_prime = False
                break
        if is_prime:
            primes.add(number)
    return "No prime numbers found." if not primes else f"{', '.join(str(num) for num in primes)} are prime numbers."

root_agent = Agent(
    model='gemini-2.0-flash',
    name='hello_world_agent',
    description='hello world agent that can roll a dice of 8 sides and check prime numbers.',
    instruction=\"\"\"
      You roll dice and answer questions about the outcome of the dice rolls.
      You can roll dice of different sizes.
      You can use multiple tools in parallel by calling functions in parallel(in one request and in one round).
      ...
    \"\"\",
    tools=[roll_die, check_prime],
)
```

- **Running the agent**: `contributing/samples/hello_world/main.py`  
  Uses `InMemoryRunner` to run the agent asynchronously with session management.

```python
import asyncio
from google.adk.runners import InMemoryRunner
from google.adk.sessions import Session
from google.genai import types
import agent  # The above agent.py

async def main():
    runner = InMemoryRunner(agent=agent.root_agent, app_name='my_app')
    session = await runner.session_service.create_session(app_name='my_app', user_id='user1')

    async def run_prompt(session: Session, new_message: str):
        content = types.Content(role='user', parts=[types.Part.from_text(text=new_message)])
        async for event in runner.run_async(user_id='user1', session_id=session.id, new_message=content):
            if event.content.parts and event.content.parts[0].text:
                print(f'Agent says: {event.content.parts[0].text}')

    await run_prompt(session, 'Roll a die with 100 sides')
    await run_prompt(session, 'What numbers did I got?')

if __name__ == '__main__':
    asyncio.run(main())
```

### Running the Agent

Run the main script directly:

```bash
python contributing/samples/hello_world/main.py
```

This will start the agent, create a session, send user prompts, and print the agent's responses.

---

## 2. How to Create a Python ReAct Agent with Tool Calling Using This API

### What is a ReAct Agent?

A ReAct agent uses reasoning and acting steps, calling tools as needed to answer questions or perform tasks. The Google ADK supports this pattern by allowing tools (functions or classes) to be registered with the agent and called during execution.

### Using Tools with the Agent

- Tools can be simple Python functions (sync or async) or more complex tool classes.
- Tools are passed to the `Agent` constructor in the `tools` list.
- The agent's instruction should guide it on how to use the tools.

### Example: Langchain Structured Tool Agent (ReAct style with tool calling)

See `contributing/samples/langchain_structured_tool_agent/agent.py`:

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

- This example shows how to wrap a Langchain `StructuredTool` as a tool for the ADK agent.
- The agent can then call this tool during its reasoning process.

### Using the Agent with Tool Calling

- The agent automatically manages tool invocation based on the instructions and the tools provided.
- The `Agent` class internally uses an LLM flow (`AutoFlow` or `SingleFlow`) to handle reasoning and tool calling.
- Tools can be synchronous or asynchronous functions or classes implementing the tool interface.

### Advanced Features

- You can specify a `planner` in the agent to control multi-step reasoning.
- You can use callbacks (`before_model_callback`, `after_model_callback`, `before_tool_callback`, `after_tool_callback`) to hook into the agent's lifecycle.
- You can configure code execution capabilities via `code_executor`.

---

## 3. References to Source Code and Documentation

- **Agent class and core logic**:  
  `src/google/adk/agents/llm_agent.py`  
  This file defines the `LlmAgent` class (aliased as `Agent`), which is the main class for creating agents. It supports tools, instructions, planners, callbacks, and code execution.  
  Key methods: `_run_async_impl`, `canonical_tools`, `canonical_instruction`  
  (See lines ~50-400)

- **Sample agents demonstrating tool usage and ReAct style**:  
  - `contributing/samples/hello_world/agent.py` and `main.py` (basic tool calling with dice roll and prime check)  
  - `contributing/samples/langchain_structured_tool_agent/agent.py` (integration with Langchain StructuredTool)  
  - `contributing/samples/hello_world_ollama/agent.py` (another example with a different LLM model)  
  - `contributing/samples/toolbox_agent/agent.py` (using ToolboxToolset for tool integration)

- **Running agents**:  
  Use `InMemoryRunner` or `Runner` from `google.adk.runners` to run agents asynchronously with session management.  
  Example: `contributing/samples/hello_world/main.py`

- **Tool integration**:  
  Tools can be simple Python functions or wrapped tools like `LangchainTool` from `google.adk.tools.langchain_tool`.

- **Agent instructions and tool calling**:  
  The agent's `instruction` string guides the LLM on how to use the tools. The agent framework handles the tool invocation automatically.

---

## 4. Using Specialist Tools and Scaffolding

- The package provides scaffolding tools like `LangchainTool` to easily wrap Langchain tools for use in the agent.  
  - Example: `google.adk.tools.langchain_tool.LangchainTool` used in `langchain_structured_tool_agent/agent.py`

- The `Agent` class supports passing Python functions directly as tools, which are internally wrapped as `FunctionTool` instances.

- The `Runner` and `InMemoryRunner` classes provide easy ways to run agents with session and artifact management.

---

## Summary

- To create and run an agent directly in Python, define your tools as functions or tool classes, instantiate an `Agent` with a model, instructions, and tools, then run it using a `Runner` or `InMemoryRunner` with session management.  
- To create a ReAct agent with tool calling, provide tools to the `Agent` and write instructions guiding the agent to use those tools. The agent framework handles the tool invocation automatically.  
- Use provided scaffolding tools like `LangchainTool` for easier integration with Langchain tools.  
- Refer to the sample agents in `contributing/samples/` for practical examples of agent creation and running.

---

## Important Files for Reference

| File Path | Description |
|-----------|-------------|
| `src/google/adk/agents/llm_agent.py` | Core Agent class implementation with tool and callback support |
| `contributing/samples/hello_world/agent.py` | Example agent with tool calling (dice roll and prime check) |
| `contributing/samples/hello_world/main.py` | Example runner script to run the agent asynchronously |
| `contributing/samples/langchain_structured_tool_agent/agent.py` | Example of ReAct agent using Langchain StructuredTool |
| `contributing/samples/toolbox_agent/agent.py` | Example using ToolboxToolset for tool integration |
| `src/google/adk/tools/langchain_tool.py` | Langchain tool wrapper for ADK agents |

---

This guide is based 100% on the source code and samples found in the package directory `output/cache/google/adk-python`.

For further details, consult the source files mentioned above.
