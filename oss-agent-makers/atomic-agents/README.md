# Atomic Agents API Usage Guide: Creating a ReAct Agent with Tool Calling

This document provides an exhaustive and detailed guide on how to use the Atomic Agents package API to create a ReAct (Reasoning and Acting) agent that can call tools dynamically. The guide covers the core components, their relationships, and step-by-step instructions to build and run such an agent.

---

## Table of Contents

- [Overview](#overview)
- [Core Concepts and Components](#core-concepts-and-components)
  - [BaseAgent](#baseagent)
  - [BaseTool](#basetool)
  - [AgentMemory](#agentmemory)
  - [SystemPromptGenerator](#systempromptgenerator)
  - [MCPToolFactory and MCP Tools](#mcptoolfactory-and-mcp-tools)
- [How to Create a ReAct Agent with Tool Calling](#how-to-create-a-react-agent-with-tool-calling)
  - [Step 1: Setup the Language Model Client](#step-1-setup-the-language-model-client)
  - [Step 2: Fetch or Define Tools](#step-2-fetch-or-define-tools)
  - [Step 3: Create or Extend an Agent](#step-3-create-or-extend-an-agent)
  - [Step 4: Configure System Prompts](#step-4-configure-system-prompts)
  - [Step 5: Run the Agent](#step-5-run-the-agent)
- [Example Code Snippet](#example-code-snippet)
- [Additional Notes](#additional-notes)
- [References to Source Files](#references-to-source-files)

---

## Overview

The Atomic Agents package provides a modular framework to build AI agents that interact with language models and external tools. The ReAct paradigm involves the agent reasoning about the problem and acting by calling tools to gather information or perform tasks.

This package supports:

- Defining agents with memory and system prompts.
- Dynamically generating tool classes from MCP (Multi-Channel Protocol) endpoints.
- Running agents synchronously or asynchronously with streaming support.
- Managing chat history and context.

---

## Core Concepts and Components

### BaseAgent

- **Location:** `atomic_agents/atomic_agents/agents/base_agent.py`
- **Description:** The foundational class for chat agents. It manages memory, system prompts, and interaction with the language model client.
- **Key Features:**
  - Input and output schemas for structured data.
  - Memory management via `AgentMemory`.
  - System prompt generation via `SystemPromptGenerator`.
  - Synchronous and asynchronous methods to run the agent (`run`, `run_async`).
  - Supports streaming partial responses.
  - Allows registering/unregistering context providers for system prompts.

**Usage Highlights:**

- Initialize with a `BaseAgentConfig` that includes the language model client, model name, memory, and system prompt generator.
- Use `run(user_input)` for synchronous calls or `run_async(user_input)` for async streaming.
- Memory stores conversation history and can be reset.

---

### BaseTool

- **Location:** `atomic_agents/atomic_agents/lib/base/base_tool.py`
- **Description:** Abstract base class for tools that the agent can call.
- **Key Features:**
  - Defines input and output schemas.
  - Requires subclasses to implement the `run(params)` method.

---

### AgentMemory

- **Location:** `atomic_agents/atomic_agents/lib/components/agent_memory.py`
- **Description:** Manages chat history and conversation turns.
- **Key Features:**
  - Stores messages with roles (`user`, `assistant`, `tool`).
  - Supports multimodal content (e.g., images).
  - Can serialize/deserialize memory state.
  - Manages message overflow with a max message limit.
  - Supports turn-based message grouping.

---

### SystemPromptGenerator

- **Location:** `atomic_agents/atomic_agents/lib/components/system_prompt_generator.py`
- **Description:** Generates system prompts that guide the agent's behavior.
- **Key Features:**
  - Supports background info, step instructions, output instructions.
  - Supports additional context providers for dynamic context injection.
  - Produces a markdown-formatted prompt string.

---

### MCPToolFactory and MCP Tools

- **Location:** `atomic_agents/atomic_agents/lib/factories/mcp_tool_factory.py`
- **Description:** Factory to dynamically generate tool classes from MCP server endpoints.
- **Key Features:**
  - Connects to MCP servers via SSE or STDIO.
  - Fetches tool definitions and input schemas.
  - Dynamically creates synchronous `BaseTool` subclasses with `run` methods that call MCP tools.
  - Supports persistent client sessions or per-call connections.
  - Provides utility functions:
    - `fetch_mcp_tools(...)` to get tool classes.
    - `create_mcp_orchestrator_schema(tools)` to create a union schema for orchestrator agents.
    - `fetch_mcp_tools_with_schema(...)` to get both tools and orchestrator schema.

---

## How to Create a ReAct Agent with Tool Calling

### Step 1: Setup the Language Model Client

You need a client to interact with a language model (e.g., OpenAI). The package uses the `instructor` client abstraction.

```python
import instructor
from openai import OpenAI

client = instructor.from_openai(OpenAI())
```

### Step 2: Fetch or Define Tools

If you have an MCP server exposing tools, use `MCPToolFactory` or the helper function `fetch_mcp_tools` to dynamically generate tool classes.

```python
from atomic_agents.lib.factories.mcp_tool_factory import fetch_mcp_tools

mcp_endpoint = "http://localhost:8000"  # Your MCP server URL
tools = fetch_mcp_tools(mcp_endpoint=mcp_endpoint)
```

Each tool class will have a `run` method accepting input parameters according to the tool's schema.

### Step 3: Create or Extend an Agent

You can use the `BaseAgent` class directly or extend it to implement custom ReAct logic.

- Initialize `BaseAgent` with a config including the client, model, memory, and system prompt generator.
- Optionally, include the tools in the system prompt or memory to enable tool calling.

```python
from atomic_agents.atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.agent_memory import AgentMemory
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator

memory = AgentMemory()
system_prompt_generator = SystemPromptGenerator(
    background=["You are a ReAct agent that can call tools."],
    steps=[
        "Analyze the user's input.",
        "Decide if a tool call is needed.",
        "Call the appropriate tool with parameters.",
        "Use the tool's output to formulate a response."
    ],
    output_instructions=["Respond in JSON format using the defined schema."]
)

config = BaseAgentConfig(
    client=client,
    model="gpt-4o-mini",
    memory=memory,
    system_prompt_generator=system_prompt_generator,
)

agent = BaseAgent(config)
```

### Step 4: Configure System Prompts

Use the `SystemPromptGenerator` to add instructions that guide the agent to reason and call tools. You can also register context providers if needed.

### Step 5: Run the Agent

Run the agent synchronously or asynchronously with user input.

```python
from atomic_agents.atomic_agents.agents.base_agent import BaseAgentInputSchema

user_input = BaseAgentInputSchema(chat_message="What is the weather in New York?")

# Synchronous call
response = agent.run(user_input)
print(response.chat_message)

# Asynchronous streaming call
import asyncio

async def async_chat():
    async for partial_response in agent.run_async(user_input):
        print(partial_response.chat_message)

asyncio.run(async_chat())
```

---

## Example Code Snippet

```python
import instructor
from openai import OpenAI
from atomic_agents.atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseAgentInputSchema
from atomic_agents.lib.factories.mcp_tool_factory import fetch_mcp_tools
from atomic_agents.lib.components.agent_memory import AgentMemory
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator

# Setup client
client = instructor.from_openai(OpenAI())

# Fetch tools from MCP server
mcp_endpoint = "http://localhost:8000"
tools = fetch_mcp_tools(mcp_endpoint=mcp_endpoint)

# Setup memory and system prompt
memory = AgentMemory()
system_prompt_generator = SystemPromptGenerator(
    background=["You are a ReAct agent that can call tools."],
    steps=[
        "Analyze the user's input.",
        "Decide if a tool call is needed.",
        "Call the appropriate tool with parameters.",
        "Use the tool's output to formulate a response."
    ],
    output_instructions=["Respond in JSON format using the defined schema."]
)

# Configure agent
config = BaseAgentConfig(
    client=client,
    model="gpt-4o-mini",
    memory=memory,
    system_prompt_generator=system_prompt_generator,
)

agent = BaseAgent(config)

# Example user input
user_input = BaseAgentInputSchema(chat_message="Calculate 5 + 7")

# Run agent synchronously
response = agent.run(user_input)
print("Agent response:", response.chat_message)

# To call a tool explicitly (example for first tool)
if tools:
    tool = tools[0]()
    tool_input = tool.input_schema(tool_name=tool.tool_name, param1=5, param2=7)  # Adjust params as per schema
    tool_output = tool.run(tool_input)
    print("Tool output:", tool_output.result)
```

---

## Additional Notes

- The `BaseAgent` class supports streaming partial responses asynchronously via `run_async`.
- Tools generated by `MCPToolFactory` are synchronous and open a connection per call unless a persistent session is provided.
- The system prompt generator can be extended with context providers to inject dynamic context.
- The agent memory supports multimodal content and can be serialized/deserialized.
- The package includes example agents and tools in the `atomic-examples` directory for reference.

---

## References to Source Files

- Agent base class and config: `atomic_agents/atomic_agents/agents/base_agent.py`
- Tool base class: `atomic_agents/atomic_agents/lib/base/base_tool.py`
- Agent memory management: `atomic_agents/atomic_agents/lib/components/agent_memory.py`
- System prompt generation: `atomic_agents/atomic_agents/lib/components/system_prompt_generator.py`
- MCP tool factory and helpers: `atomic_agents/atomic_agents/lib/factories/mcp_tool_factory.py`
- MCP tool definition service: `atomic_agents/atomic_agents/lib/factories/tool_definition_service.py`

---

This guide should enable you to understand and use the Atomic Agents API to create a ReAct agent capable of calling external tools dynamically, leveraging the MCP protocol and structured interaction with language models.