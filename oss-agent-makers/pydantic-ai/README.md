# pydantic-ai API Usage for Creating a ReAct Agent with Tool Calling

This document provides an exhaustive guide on how to use the `pydantic-ai` package API to create a ReAct (Reasoning and Acting) agent with tool calling capabilities. It is based on the analysis of the package source code, focusing on the core `Agent` class and related tooling support.

---

## Table of Contents

- [Overview](#overview)
- [Creating an Agent](#creating-an-agent)
- [Registering Tools](#registering-tools)
- [Running the Agent](#running-the-agent)
- [Iterating Over Agent Execution (ReAct style)](#iterating-over-agent-execution-react-style)
- [Using Dependencies and Output Types](#using-dependencies-and-output-types)
- [Advanced Features](#advanced-features)
- [Example: Time Range Inference Agent](#example-time-range-inference-agent)
- [Example: Chat Application](#example-chat-application)
- [Summary](#summary)

---

## Overview

The core abstraction is the `Agent` class, which represents a conversational agent powered by an LLM model. The agent supports:

- Defining tools (functions) that the agent can call during reasoning.
- Running the agent asynchronously or synchronously.
- Streaming results or iterating over the internal execution graph nodes.
- Customizing system prompts, instructions, and output validation.
- Dependency injection for passing contextual data to tools.
- Integration with MCP servers and instrumentation for observability.

---

## Creating an Agent

The `Agent` class is generic over two type parameters:

- `AgentDepsT`: The type of dependencies passed to tools.
- `OutputDataT`: The type of the output data returned by the agent.

### Basic Initialization

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-4o')
```

- `model`: The model name or instance (e.g., `'openai:gpt-4o'`).
- `output_type`: The expected output type (default is `str`).
- `instructions`: Optional instructions for the agent.
- `system_prompt`: Static or dynamic system prompts.
- `deps_type`: Type of dependencies for tools.
- `tools`: Sequence of tools to register.
- `prepare_tools`: Optional function to customize tool definitions per step.
- `end_strategy`: Strategy for handling tool calls with final results (default `'early'`).
- `instrument`: Enable OpenTelemetry instrumentation.

---

## Registering Tools

Tools are Python functions that the agent can call during execution. There are two main decorators to register tools:

### 1. `@agent.tool`

Registers a tool function that **takes a `RunContext` as the first argument**.

Example:

```python
from pydantic_ai import Agent, RunContext

agent = Agent('test', deps_type=int)

@agent.tool
def add(ctx: RunContext[int], x: int, y: int) -> int:
    return ctx.deps + x + y
```

### 2. `@agent.tool_plain`

Registers a tool function that **does NOT take a `RunContext` argument**.

Example:

```python
@agent.tool_plain
def multiply(x: int, y: int) -> int:
    return x * y
```

### Tool Options

Both decorators accept parameters such as:

- `name`: Tool name (defaults to function name).
- `retries`: Number of retries allowed for the tool.
- `prepare`: Custom function to prepare the tool definition dynamically.
- `docstring_format`: Format of the docstring for schema extraction (`'auto'` by default).
- `require_parameter_descriptions`: Whether to enforce parameter descriptions.
- `schema_generator`: JSON schema generator class.
- `strict`: Enforce strict JSON schema compliance (OpenAI only).

---

## Running the Agent

The agent supports multiple run modes:

### 1. `run`

Asynchronously run the agent with a user prompt and return the final result.

```python
result = await agent.run("What is the capital of France?")
print(result.output)  # e.g., "Paris"
```

### 2. `run_sync`

Synchronously run the agent (blocking call).

```python
result = agent.run_sync("What is the capital of France?")
print(result.output)
```

### 3. `run_stream`

Asynchronously run the agent and get a streamed response.

```python
async with agent.run_stream("What is the capital of France?") as streamed_result:
    async for chunk in streamed_result.stream():
        print(chunk)
```

### 4. `iter`

Get an async context manager that yields an `AgentRun` instance, which can be iterated over to get each node of the internal execution graph. This is the core API for ReAct style interaction.

```python
async with agent.iter("What is the capital of France?") as agent_run:
    async for node in agent_run:
        # Inspect or modify nodes here
        print(node)
```

---

## Iterating Over Agent Execution (ReAct style)

The `AgentRun` class represents a stateful run of the agent. It supports:

- Async iteration over nodes (`UserPromptNode`, `ModelRequestNode`, `CallToolsNode`, `End`).
- Manual driving of execution via `next(node)` method.
- Access to the final result via `result` property.
- Access to usage statistics.

Example driving the run manually:

```python
from pydantic_graph import End

async with agent.iter("What is the capital of France?") as agent_run:
    next_node = agent_run.next_node
    while not isinstance(next_node, End):
        # Optionally inspect or modify next_node here
        next_node = await agent_run.next(next_node)
    print("Final result:", agent_run.result.output)
```

---

## Using Dependencies and Output Types

- You can specify a dependencies type (`deps_type`) when creating the agent. This type is passed to tools via the `RunContext`.
- You can specify a custom output type (`output_type`) for the agent's result, which will be validated.
- You can override dependencies and model temporarily using the `override` context manager.

Example with dependencies and output type:

```python
from pydantic_ai import Agent
from my_types import MyDeps, MyOutput

agent = Agent[MyDeps, MyOutput](
    'openai:gpt-4o',
    deps_type=MyDeps,
    output_type=MyOutput,
)

result = await agent.run("Some prompt", deps=MyDeps(...))
```

---

## Advanced Features

- **Instructions and System Prompts**: Use `@agent.instructions` and `@agent.system_prompt` decorators to register functions that provide dynamic instructions or system prompts.
- **Output Validators**: Use `@agent.output_validator` to register functions that validate or transform the output.
- **MCP Servers**: Register MCP servers for multi-agent communication.
- **Instrumentation**: Enable OpenTelemetry instrumentation for observability.
- **Convert to ASGI app**: Use `agent.to_a2a()` to convert the agent into a FastA2A ASGI application.
- **CLI Interface**: Use `agent.to_cli()` or `agent.to_cli_sync()` to run the agent in a CLI chat interface.

---

## Example: Time Range Inference Agent

This example shows an agent with dependencies and a tool:

```python
from dataclasses import dataclass, field
from datetime import datetime
from pydantic_ai import Agent, RunContext
from .models import TimeRangeInputs, TimeRangeResponse

@dataclass
class TimeRangeDeps:
    now: datetime = field(default_factory=lambda: datetime.now().astimezone())

time_range_agent = Agent[TimeRangeDeps, TimeRangeResponse](
    'gpt-4o',
    output_type=TimeRangeResponse,
    deps_type=TimeRangeDeps,
    system_prompt="Convert the user's request into a structured time range.",
    retries=1,
    instrument=True,
)

@time_range_agent.tool
def get_current_time(ctx: RunContext[TimeRangeDeps]) -> str:
    now_str = ctx.deps.now.strftime('%A, %B %d, %Y %H:%M:%S %Z')
    return f"The user's current time is {now_str}."

async def infer_time_range(inputs: TimeRangeInputs) -> TimeRangeResponse:
    deps = TimeRangeDeps(now=inputs['now'])
    return (await time_range_agent.run(inputs['prompt'], deps=deps)).output
```

---

## Example: Chat Application

A simple chat app using FastAPI and the agent's streaming API:

- The agent is created with a model.
- The chat history is passed as message history.
- The agent is run with `run_stream` to stream responses.
- Messages are stored in a SQLite database asynchronously.

Key snippet:

```python
from pydantic_ai import Agent
agent = Agent('openai:gpt-4o')

@app.post('/chat/')
async def post_chat(prompt: str, database: Database):
    async def stream_messages():
        yield json.dumps({'role': 'user', 'content': prompt}).encode() + b'\n'
        messages = await database.get_messages()
        async with agent.run_stream(prompt, message_history=messages) as result:
            async for text in result.stream(debounce_by=0.01):
                yield json.dumps({'role': 'model', 'content': text}).encode() + b'\n'
        await database.add_messages(result.new_messages_json())
    return StreamingResponse(stream_messages(), media_type='text/plain')
```

---

## Summary

To create a ReAct agent with tool calling using `pydantic-ai`:

1. **Create an `Agent` instance**, specifying the model, output type, and optionally dependencies.
2. **Register tools** using `@agent.tool` or `@agent.tool_plain` decorators.
3. **Run the agent** asynchronously with `run`, synchronously with `run_sync`, or stream with `run_stream`.
4. **For ReAct style interaction**, use the `iter` method to get an `AgentRun` instance and iterate over execution nodes.
5. **Use system prompts, instructions, and output validators** to customize agent behavior.
6. **Optionally integrate with MCP servers, instrumentation, or convert to ASGI or CLI apps.**

This API design provides a powerful and flexible way to build agents that reason and act by calling tools, with strong typing, validation, and observability.

---

# References

- `Agent` class: `pydantic_ai_slim/pydantic_ai/agent.py` (lines 1-1000+)
- `Tool` class and decorators: `pydantic_ai_slim/pydantic_ai/tools.py`
- Example agent with tools: `examples/pydantic_ai_examples/evals/agent.py`
- Chat app example: `examples/pydantic_ai_examples/chat_app.py`

If you want me to extract usage examples or specific API details from other files or focus on particular features, please let me know!