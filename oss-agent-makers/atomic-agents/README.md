# Comprehensive Guide to Using the Atomic Agents API to Create and Run Python Agents with ReAct and Tool Calling

This document provides an exhaustive, detailed explanation of how to use the Atomic Agents package API to create an agent that can be run directly in Python (e.g., `python agent.py`). It also explains how to create a Python ReAct agent with tool calling capabilities, referencing relevant source code and example scripts from the package.

---

## Table of Contents

1. [Overview of the Atomic Agents API](#overview-of-the-atomic-agents-api)
2. [Creating and Running a Basic Agent in Python](#creating-and-running-a-basic-agent-in-python)
3. [Creating a Python ReAct Agent with Tool Calling](#creating-a-python-react-agent-with-tool-calling)
4. [Using MCP Tool Factory for Tool Integration](#using-mcp-tool-factory-for-tool-integration)
5. [Example: MCP Agent with STDIO Transport](#example-mcp-agent-with-stdio-transport)
6. [References to Source Code and Documentation](#references-to-source-code-and-documentation)

---

## Overview of the Atomic Agents API

The Atomic Agents package provides a modular and extensible framework for building AI agents that interact with language models and tools. The core components include:

- **BaseAgent**: The foundational class for creating chat agents.
- **AgentMemory**: Manages conversation history.
- **SystemPromptGenerator**: Generates system prompts to guide the agent's behavior.
- **BaseIOSchema**: Pydantic-based schemas for input/output validation.
- **MCPToolFactory**: Factory to dynamically create tool classes from MCP (Multi-Channel Protocol) tool definitions, enabling tool calling.
- **Instructor**: A client abstraction layer for various LLM providers (OpenAI, Anthropic, etc.).

---

## Creating and Running a Basic Agent in Python

### Key Class: `BaseAgent`

- Located in: `atomic-agents/atomic-agents/atomic_agents/agents/base_agent.py`
- The `BaseAgent` class encapsulates the logic for interacting with a language model, managing memory, and generating responses.
- It supports synchronous and asynchronous operation.
- Uses `BaseAgentConfig` for configuration, including the LLM client, model name, memory, system prompt generator, and schemas.

### Basic Usage Pattern

1. **Setup the LLM client** (e.g., OpenAI via `instructor`).
2. **Create memory and system prompt generator** instances.
3. **Define input/output schemas** if customization is needed.
4. **Instantiate `BaseAgent` with a `BaseAgentConfig`.**
5. **Run the agent synchronously or asynchronously.**

### Example from `3_basic_custom_chatbot_with_custom_schema.py`

```python
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseAgentInputSchema
from atomic_agents.lib.components.agent_memory import AgentMemory
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
import instructor
import openai
import os

API_KEY = os.getenv("OPENAI_API_KEY")
client = instructor.from_openai(openai.OpenAI(api_key=API_KEY))

memory = AgentMemory()
system_prompt_generator = SystemPromptGenerator(
    background=["This assistant is knowledgeable and friendly."],
    steps=["Analyze input.", "Formulate response.", "Suggest follow-up questions."],
    output_instructions=["Provide clear, concise answers.", "Maintain friendly tone."]
)

agent = BaseAgent(
    BaseAgentConfig(
        client=client,
        model="gpt-4o-mini",
        memory=memory,
        system_prompt_generator=system_prompt_generator,
        output_schema=CustomOutputSchema,  # Optional custom output schema
    )
)

user_input = BaseAgentInputSchema(chat_message="Hello, how are you?")
response = agent.run(user_input)
print(response.chat_message)
```

- This example shows how to create a simple chat agent that can be run directly in Python.
- The agent maintains memory and uses a system prompt to guide responses.
- The `run` method is synchronous and returns a validated output schema instance.

### Running the Agent

You can wrap the above code in a script (e.g., `agent.py`) and run it with:

```bash
python agent.py
```

---

## Creating a Python ReAct Agent with Tool Calling

ReAct (Reasoning and Acting) agents combine reasoning with the ability to call external tools dynamically. The Atomic Agents package supports this pattern via:

- **MCPToolFactory**: Dynamically generates tool classes from MCP tool definitions.
- **Orchestrator Agent**: An agent that reasons about which tool to call and when.
- **Union Schemas**: Used to represent the input schemas of all available tools, enabling the orchestrator to select among them.

### Steps to Create a ReAct Agent with Tool Calling

1. **Fetch or define tools** using `MCPToolFactory` or manually.
2. **Create an orchestrator input schema** that includes the user query.
3. **Create an orchestrator output schema** that includes reasoning and the chosen action (tool input or final response).
4. **Instantiate a `BaseAgent` as the orchestrator** with the above schemas.
5. **Implement a loop where the orchestrator decides which tool to call, calls it, and updates memory.**

---

## Using MCP Tool Factory for Tool Integration

### Location

- `atomic-agents/atomic-agents/atomic_agents/lib/factories/mcp_tool_factory.py`

### Purpose

- Connects to an MCP server (via SSE or STDIO).
- Discovers tool definitions dynamically.
- Generates synchronous `BaseTool` subclasses for each tool.
- Supports persistent sessions for efficient tool calling.

### Key Functions

- `fetch_mcp_tools(...)`: Connects to MCP server and returns a list of tool classes.
- `create_mcp_orchestrator_schema(tools)`: Creates a Pydantic schema that unions all tool input schemas for orchestrator use.
- `fetch_mcp_tools_with_schema(...)`: Returns both tools and orchestrator schema.

### Example Usage

```python
from atomic_agents.lib.factories.mcp_tool_factory import fetch_mcp_tools, create_mcp_orchestrator_schema

tools = fetch_mcp_tools(mcp_endpoint="http://localhost:8000", use_stdio=False)
orchestrator_schema = create_mcp_orchestrator_schema(tools)
```

---

## Example: MCP Agent with STDIO Transport

A complete example demonstrating a ReAct agent with tool calling is provided in:

- `atomic-examples/mcp-agent/example-client/example_client/main_stdio.py`

### Highlights

- Uses `fetch_mcp_tools` with a persistent STDIO session.
- Dynamically loads tools from an MCP server.
- Defines an orchestrator agent with custom input/output schemas.
- Runs an interactive chat loop where the orchestrator reasons about tool usage.
- Calls tools synchronously and updates memory with results.
- Provides detailed reasoning and final responses to the user.

### Key Code Snippets

**Setup persistent STDIO session and fetch tools:**

```python
import asyncio
import shlex
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from atomic_agents.lib.factories.mcp_tool_factory import fetch_mcp_tools

async def _bootstrap_stdio():
    exit_stack = AsyncExitStack()
    command_parts = shlex.split("poetry run example-mcp-server --mode stdio")
    server_params = StdioServerParameters(command=command_parts[0], args=command_parts[1:], env=None)
    read_stream, write_stream = await exit_stack.enter_async_context(stdio_client(server_params))
    session = await exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
    await session.initialize()
    return session

stdio_loop = asyncio.new_event_loop()
stdio_session = stdio_loop.run_until_complete(_bootstrap_stdio())

tools = fetch_mcp_tools(
    mcp_endpoint=None,
    use_stdio=True,
    client_session=stdio_session,
    event_loop=stdio_loop,
)
```

**Define orchestrator schemas:**

```python
from pydantic import Field
from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from typing import Union, Type

class MCPOrchestratorInputSchema(BaseIOSchema):
    query: str = Field(..., description="The user's query to analyze.")

class OrchestratorOutputSchema(BaseIOSchema):
    reasoning: str = Field(..., description="Explanation of chosen action.")
    action: Union[tuple(tool.input_schema for tool in tools) + (FinalResponseSchema,)] = Field(...)
```

**Create and run orchestrator agent:**

```python
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from atomic_agents.lib.components.agent_memory import AgentMemory

memory = AgentMemory()
orchestrator_agent = BaseAgent(
    BaseAgentConfig(
        client=client,
        model="gpt-4o",
        memory=memory,
        system_prompt_generator=SystemPromptGenerator(
            background=["You are an MCP Orchestrator Agent..."],
            steps=[
                "Use reasoning to select tools.",
                "Call tools sequentially.",
                "Provide final response."
            ],
            output_instructions=[
                "Explain reasoning.",
                "Choose one action.",
                "Validate parameters."
            ],
        ),
        input_schema=MCPOrchestratorInputSchema,
        output_schema=OrchestratorOutputSchema,
    )
)

# Interactive loop omitted for brevity
```

---

## References to Source Code and Documentation

- **BaseAgent and Config**:  
  `atomic-agents/atomic-agents/atomic_agents/agents/base_agent.py` (lines 1-300)  
  This file contains the core agent class with detailed docstrings and an example interactive chat loop in the `__main__` block.

- **MCP Tool Factory**:  
  `atomic-agents/atomic-agents/atomic_agents/lib/factories/mcp_tool_factory.py`  
  Contains the factory class to dynamically create tool classes from MCP tool definitions, including methods to fetch tools and create orchestrator schemas.

- **Basic Chatbot Example**:  
  `atomic-examples/quickstart/quickstart/3_basic_custom_chatbot_with_custom_schema.py`  
  Shows how to create a simple agent with custom input/output schemas and run it interactively.

- **Provider Selection Example**:  
  `atomic-examples/quickstart/quickstart/4_basic_chatbot_different_providers.py`  
  Demonstrates how to configure the agent with different LLM providers.

- **MCP Agent STDIO Example**:  
  `atomic-examples/mcp-agent/example-client/example_client/main_stdio.py`  
  A full example of a ReAct agent with tool calling using MCP tools over STDIO transport.

- **MCP Agent Main Entrypoint**:  
  `atomic-examples/mcp-agent/example-client/example_client/main.py`  
  Shows how to launch the MCP agent with different transports (stdio or sse).

---

# Summary

- To **create a basic agent**, instantiate `BaseAgent` with a configured `BaseAgentConfig` including an LLM client, memory, and system prompt generator. Use `agent.run()` to get responses.
- To **create a ReAct agent with tool calling**, use `MCPToolFactory` to fetch tools dynamically, create an orchestrator agent with union schemas of tool inputs, and implement a loop where the orchestrator reasons and calls tools.
- The package provides **example scripts** that can be run directly (e.g., `main_stdio.py`) demonstrating full ReAct agent workflows with tool integration.
- The **MCP tool factory** is a specialist tool that simplifies creating tool classes and orchestrator schemas, strongly recommended for building tool-enabled agents.

This guide, combined with the referenced source files and examples, should enable you to effectively use the Atomic Agents API to build and run Python agents with advanced ReAct and tool-calling capabilities.