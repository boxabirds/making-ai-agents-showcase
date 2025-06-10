# Comprehensive Guide to Using the `pydantic-ai` Package to Create and Run Agents in Python

This document provides an exhaustive explanation of how to use the `pydantic-ai` package API to create an agent that can be run directly in Python (e.g., `python agent.py`). It also explains how to create a Python ReAct agent with tool calling, referencing source code and examples from the package.

---

## Table of Contents

- [1. Overview of the `pydantic-ai` Agent API](#1-overview-of-the-pydantic-ai-agent-api)
- [2. Creating and Running a Basic Agent](#2-creating-and-running-a-basic-agent)
- [3. Creating a Python ReAct Agent with Tool Calling](#3-creating-a-python-react-agent-with-tool-calling)
- [4. Using Decorators to Register Tools and Validators](#4-using-decorators-to-register-tools-and-validators)
- [5. Running the Agent: Async, Sync, Streaming, and CLI](#5-running-the-agent-async-sync-streaming-and-cli)
- [6. Advanced Features: Instrumentation, MCP Servers, and Overrides](#6-advanced-features-instrumentation-mcp-servers-and-overrides)
- [7. Example: Weather Agent with Multiple Tools](#7-example-weather-agent-with-multiple-tools)
- [8. References and Further Reading](#8-references-and-further-reading)

---

## 1. Overview of the `pydantic-ai` Agent API

The core class for creating agents is `Agent`, defined in `pydantic_ai_slim/pydantic_ai/agent.py`. An `Agent` represents a conversational entity that interacts with a language model (LLM) and optionally calls tools during the conversation.

### Key Features of `Agent`:

- Generic over dependency injection type (`AgentDepsT`) and output data type (`OutputDataT`).
- Supports specifying the underlying LLM model (e.g., `"openai:gpt-4o"`).
- Supports registering tools (functions) that the agent can call during conversation.
- Supports system prompts and instructions to guide the agent's behavior.
- Supports output validation and retries.
- Supports synchronous, asynchronous, and streaming execution.
- Supports instrumentation with OpenTelemetry.
- Supports converting the agent to a CLI or ASGI app.

---

## 2. Creating and Running a Basic Agent

### Creating an Agent

You create an agent by instantiating the `Agent` class with parameters such as the model name, instructions, tools, and dependency types.

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-4o')
```

### Running the Agent

You can run the agent asynchronously or synchronously:

- **Async run:**

```python
result = await agent.run('What is the capital of France?')
print(result.output)  # Output: Paris
```

- **Sync run:**

```python
result_sync = agent.run_sync('What is the capital of France?')
print(result_sync.output)  # Output: Paris
```

### Streaming run (async):

```python
async with agent.run_stream('What is the capital of France?') as streamed_result:
    print(await streamed_result.get_output())
```

---

## 3. Creating a Python ReAct Agent with Tool Calling

ReAct (Reasoning + Acting) agents use tools to augment their reasoning capabilities. The `pydantic-ai` package supports this pattern by allowing you to register tools that the agent can call during conversation.

### Steps to Create a ReAct Agent:

1. **Define your dependencies (optional):**

```python
from dataclasses import dataclass

@dataclass
class Deps:
    # Define any dependencies your tools need, e.g., API clients, keys
    api_key: str
```

2. **Create the agent with instructions and dependency type:**

```python
agent = Agent(
    'openai:gpt-4o',
    instructions='Use the tools to answer the user queries.',
    deps_type=Deps,
    retries=2,
)
```

3. **Register tools using the `@agent.tool` decorator:**

```python
from pydantic_ai import RunContext

@agent.tool
async def get_lat_lng(ctx: RunContext[Deps], location: str) -> dict[str, float]:
    # Tool implementation to get latitude and longitude
    return {'lat': 51.1, 'lng': -0.1}

@agent.tool
async def get_weather(ctx: RunContext[Deps], lat: float, lng: float) -> dict[str, str]:
    # Tool implementation to get weather
    return {'temperature': '21 °C', 'description': 'Sunny'}
```

4. **Run the agent with dependencies:**

```python
deps = Deps(api_key='your_api_key_here')
result = await agent.run('What is the weather in London?', deps=deps)
print(result.output)
```

### How Tool Calling Works Internally

- The agent builds an internal graph of nodes representing user prompts, model requests, and tool calls (`UserPromptNode`, `ModelRequestNode`, `CallToolsNode`).
- When the model response includes a tool call, the agent executes the corresponding tool function.
- The agent supports retries and validation of tool outputs.
- Tool calls can be processed in parallel asynchronously.

---

## 4. Using Decorators to Register Tools and Validators

The `Agent` class provides decorators to register tools and output validators easily:

- `@agent.tool`: Register a tool function that takes a `RunContext` as the first argument.
- `@agent.tool_plain`: Register a tool function that does **not** take a `RunContext`.
- `@agent.output_validator`: Register a function to validate the output of the agent.

Example:

```python
@agent.tool
async def example_tool(ctx: RunContext[Deps], param: int) -> int:
    return param + 1

@agent.output_validator
def validate_output(output: str) -> str:
    if 'error' in output:
        raise ModelRetry('Invalid output')
    return output
```

---

## 5. Running the Agent: Async, Sync, Streaming, and CLI

### Async Run

```python
result = await agent.run('Hello')
print(result.output)
```

### Sync Run

```python
result = agent.run_sync('Hello')
print(result.output)
```

### Streaming Run (Async)

```python
async with agent.run_stream('Hello') as stream:
    async for chunk in stream:
        print(chunk)
```

### CLI Interface

You can run the agent in a CLI chat interface:

```python
await agent.to_cli(deps=deps)
```

Or synchronously:

```python
agent.to_cli_sync(deps=deps)
```

This launches an interactive CLI chat session.

---

## 6. Advanced Features: Instrumentation, MCP Servers, and Overrides

- **Instrumentation:** Enable OpenTelemetry instrumentation for monitoring.

```python
agent = Agent('openai:gpt-4o', instrument=True)
```

- **MCP Servers:** Register MCP servers to provide additional tools remotely.

- **Override Context Manager:** Temporarily override dependencies or model for testing.

```python
with agent.override(deps=my_deps, model='openai:gpt-4o'):
    result = agent.run_sync('Hello')
```

- **System Prompts and Instructions:** Use decorators to register dynamic or static system prompts and instructions.

```python
@agent.instructions
def my_instructions(ctx: RunContext[Deps]) -> str:
    return "You are a helpful assistant."

@agent.system_prompt(dynamic=True)
async def dynamic_prompt(ctx: RunContext[Deps]) -> str:
    return f"Current time is {ctx.deps.now}"
```

---

## 7. Example: Weather Agent with Multiple Tools

The package includes an example agent that demonstrates a ReAct agent with multiple tools:

- **File:** `examples/pydantic_ai_examples/weather_agent.py`

### Summary:

- Defines a `Deps` dataclass with HTTP client and API keys.
- Creates an `Agent` with instructions to use two tools: `get_lat_lng` and `get_weather`.
- Registers two async tools using `@weather_agent.tool`.
- Runs the agent asynchronously with dependencies.

### Example snippet from `weather_agent.py`:

```python
from pydantic_ai import Agent, RunContext
from httpx import AsyncClient
from dataclasses import dataclass

@dataclass
class Deps:
    client: AsyncClient
    weather_api_key: str | None
    geo_api_key: str | None

weather_agent = Agent(
    'openai:gpt-4o',
    instructions=(
        'Be concise, reply with one sentence.'
        'Use the `get_lat_lng` tool to get the latitude and longitude of the locations, '
        'then use the `get_weather` tool to get the weather.'
    ),
    deps_type=Deps,
    retries=2,
)

@weather_agent.tool
async def get_lat_lng(ctx: RunContext[Deps], location_description: str) -> dict[str, float]:
    # Implementation...

@weather_agent.tool
async def get_weather(ctx: RunContext[Deps], lat: float, lng: float) -> dict[str, Any]:
    # Implementation...

async def main():
    async with AsyncClient() as client:
        deps = Deps(client=client, weather_api_key='...', geo_api_key='...')
        result = await weather_agent.run('What is the weather like in London?', deps=deps)
        print(result.output)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
```

This example can be run directly with Python and demonstrates how to create a ReAct agent with tool calling.

---

## 8. References and Further Reading

- **Source Code:**

  - `pydantic_ai_slim/pydantic_ai/agent.py` — Core `Agent` class and API.
  - `pydantic_ai_slim/pydantic_ai/_agent_graph.py` — Internal graph nodes and execution logic.
  - `examples/pydantic_ai_examples/weather_agent.py` — Example ReAct agent with tools.
  - `examples/pydantic_ai_examples/weather_agent_gradio.py` — Example integrating the agent with Gradio UI.

- **Online Documentation:**

  - [Pydantic AI Documentation](https://ai.pydantic.dev/)
  - [Debugging and Monitoring Guide](https://ai.pydantic.dev/logfire/)
  - [Tools Documentation](../tools.md#function-tools-and-schema) (referenced in code comments)

- **Usage Patterns:**

  - Use `Agent` to create agents with optional dependency injection.
  - Register tools with `@agent.tool` or `@agent.tool_plain`.
  - Use `agent.run()`, `agent.run_sync()`, or `agent.run_stream()` to execute.
  - Use `agent.to_cli()` or `agent.to_cli_sync()` for CLI interaction.
  - Use `agent.override()` context manager for testing with different deps or models.

---

# Summary

The `pydantic-ai` package provides a powerful, flexible API to create conversational agents backed by LLMs with integrated tool calling capabilities. The `Agent` class is the main entry point, supporting rich features like dependency injection, output validation, retries, instrumentation, and multiple execution modes.

To create a Python ReAct agent with tool calling:

- Instantiate `Agent` with your model and instructions.
- Define your dependencies as a dataclass.
- Register tools using `@agent.tool` decorators.
- Run the agent asynchronously or synchronously with dependencies.
- Optionally use streaming or CLI interfaces.

The package includes scaffold tools and examples (e.g., the weather agent) that make it straightforward to build complex agents without hand-coding all the internals.

---

If you want, I can also generate a minimal runnable example script (`agent.py`) based on this API to run directly with `python agent.py`. Just ask!