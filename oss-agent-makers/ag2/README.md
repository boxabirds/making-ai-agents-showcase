# API Usage Guide for Creating a ReAct Agent with Tool Calling Using the `ag2` Package

This document provides an exhaustive and detailed guide on how to use the API provided by the `ag2` package to create a ReAct (Reasoning and Acting) agent capable of tool calling. The guide is based on the analysis of the core agent implementation in the package, particularly focusing on the `ConversableAgent` class, which is the main class for creating agents that can converse, reason, and call tools or functions.

---

## Table of Contents

- [Overview](#overview)
- [Key Classes and Concepts](#key-classes-and-concepts)
  - [Agent Protocol](#agent-protocol)
  - [LLMAgent Protocol](#llmagent-protocol)
  - [ConversableAgent Class](#conversableagent-class)
- [Creating a ReAct Agent](#creating-a-react-agent)
  - [Initialization](#initialization)
  - [Registering Tools and Functions](#registering-tools-and-functions)
  - [Sending and Receiving Messages](#sending-and-receiving-messages)
  - [Generating Replies with Tool Calling](#generating-replies-with-tool-calling)
- [Advanced Features](#advanced-features)
  - [Code Execution](#code-execution)
  - [Human Input Modes](#human-input-modes)
  - [Nested Chats and Group Chats](#nested-chats-and-group-chats)
  - [Hooks and Agent State Updates](#hooks-and-agent-state-updates)
- [Example Usage](#example-usage)
- [Summary](#summary)

---

## Overview

The `ag2` package provides a flexible and extensible framework for building conversational agents that can reason, act, and interact with tools or functions. The core abstraction is the `Agent` protocol, with the `ConversableAgent` class implementing a powerful LLM-based agent that supports:

- Conversational interaction with other agents.
- Tool and function calling integrated with LLM responses.
- Code execution capabilities.
- Human-in-the-loop interaction modes.
- Nested and group chat management.
- Extensible hooks for custom behaviors.

---

## Key Classes and Concepts

### Agent Protocol

Defined in `autogen/agentchat/agent.py`, the `Agent` protocol specifies the interface for any agent:

- Properties:
  - `name`: The agent's name.
  - `description`: A description used for introductions or group chat context.
- Methods:
  - `send(message, recipient, request_reply)`: Send a message to another agent.
  - `receive(message, sender, request_reply)`: Receive a message from another agent.
  - `generate_reply(messages, sender)`: Generate a reply based on conversation history.
- Async variants of send, receive, and generate_reply are also defined.

### LLMAgent Protocol

Extends `Agent` with LLM-specific features:

- Property:
  - `system_message`: The system prompt/message for the agent.
- Method:
  - `update_system_message(system_message)`: Update the system message.

### ConversableAgent Class

Located in `autogen/agentchat/conversable_agent.py`, this is the main class to create a ReAct agent with tool calling capabilities.

- Implements `LLMAgent` protocol.
- Supports:
  - Registering functions and tools for LLM use and execution.
  - Sending and receiving messages with automatic reply generation.
  - Handling function calls and tool calls embedded in LLM messages.
  - Code execution with optional Docker support.
  - Human input modes (`ALWAYS`, `NEVER`, `TERMINATE`).
  - Nested chats and group chat support.
  - Hooks for extending agent behavior.
- Manages conversation history and usage summaries.
- Supports both synchronous and asynchronous operation.

---

## Creating a ReAct Agent

### Initialization

To create a ReAct agent, instantiate `ConversableAgent` with appropriate parameters:

```python
from autogen.agentchat.conversable_agent import ConversableAgent

agent = ConversableAgent(
    name="MyAgent",
    system_message="You are a helpful AI assistant.",
    llm_config={  # LLM configuration dict or LLMConfig instance
        "model": "gpt-4o-mini",
        "temperature": 0.7,
    },
    function_map=None,  # Optional dict mapping function names to callables
    code_execution_config=False,  # or dict to enable code execution
    human_input_mode="NEVER",  # or "ALWAYS", "TERMINATE"
)
```

- `name`: Unique name for the agent (no whitespace allowed).
- `system_message`: System prompt for the LLM.
- `llm_config`: Configuration for the LLM client (OpenAIWrapper).
- `function_map`: Optional mapping of function names to Python callables for execution.
- `code_execution_config`: Enable or disable code execution.
- `human_input_mode`: Controls when human input is requested.

### Registering Tools and Functions

Tools and functions can be registered for two purposes:

- **LLM Tool Registration**: To expose functions/tools to the LLM for function/tool calling.
- **Execution Registration**: To enable the agent to execute the functions/tools when called.

Use the decorators provided by `ConversableAgent`:

```python
@agent.register_for_llm(description="Calculate the sum of two numbers")
@agent.register_for_execution()
def add_numbers(a: int, b: int) -> int:
    return a + b
```

Or register functions programmatically:

```python
agent.register_function({"add_numbers": add_numbers})
```

- `register_for_llm`: Decorator to register a function/tool for LLM function calling.
- `register_for_execution`: Decorator to register a function/tool for execution by the agent.
- Functions must have valid names (letters, numbers, `_`, `-` only).

### Sending and Receiving Messages

Agents communicate by sending and receiving messages:

```python
agent.send(message={"content": "Hello, how can I help you?"}, recipient=other_agent)
```

- Messages can be strings or dicts following OpenAI ChatCompletion schema.
- The agent automatically appends messages to conversation history.
- Receiving a message triggers reply generation unless suppressed.

Async variants are available:

```python
await agent.a_send(message, recipient)
await agent.a_receive(message, sender)
```

### Generating Replies with Tool Calling

The agent generates replies by checking registered reply functions in order:

1. Check termination and human reply conditions.
2. Generate function call reply (deprecated, replaced by tool calls).
3. Generate tool calls reply.
4. Generate code execution reply.
5. Generate LLM-based reply.

Example of generating a reply explicitly:

```python
reply = agent.generate_reply(messages=agent.chat_messages[sender], sender=sender)
```

- Tool calls embedded in the LLM response are executed automatically.
- Tool call results are returned as part of the reply message.
- Async variants are supported.

---

## Advanced Features

### Code Execution

- Enable code execution by passing a config dict to `code_execution_config` during initialization.
- Supports Docker-based execution or local execution.
- The agent scans recent messages for code blocks and executes them.
- Execution results are included in replies.

### Human Input Modes

- `ALWAYS`: Prompt human input every message.
- `NEVER`: Never prompt human input; auto-reply only.
- `TERMINATE`: Prompt human input only on termination messages or max auto-replies.

Human input can be customized by overriding `get_human_input` and `a_get_human_input`.

### Nested Chats and Group Chats

- Supports initiating nested chats with multiple agents.
- Can register nested chat reply functions.
- Supports carryover of context and summaries between nested chats.

### Hooks and Agent State Updates

- Hooks can be registered to extend agent behavior at various points:
  - `update_agent_state`
  - `process_last_received_message`
  - `process_all_messages_before_reply`
  - `process_message_before_send`
- Useful for custom context updates, message processing, or logging.

---

## Example Usage

```python
from autogen.agentchat.conversable_agent import ConversableAgent

# Create the agent
agent = ConversableAgent(
    name="ReActAgent",
    system_message="You are a helpful assistant that can call tools.",
    llm_config={"model": "gpt-4o-mini"},
    human_input_mode="NEVER",
)

# Define a tool function
@agent.register_for_llm(description="Add two numbers")
@agent.register_for_execution()
def add(a: int, b: int) -> int:
    return a + b

# Start a conversation with another agent or self
response = agent.initiate_chat(
    recipient=agent,
    message="What is the sum of 5 and 7?",
    max_turns=3,
)

print("Chat summary:", response.summary)
print("Chat history:", response.chat_history)
```

---

## Summary

- Use `ConversableAgent` to create a ReAct agent with tool calling.
- Register functions/tools with `register_for_llm` and `register_for_execution`.
- Send and receive messages using `send` and `receive` methods.
- Replies are generated automatically, supporting tool calls and code execution.
- Supports synchronous and asynchronous usage.
- Human input modes and hooks provide customization.
- Nested chats and group chat features enable complex multi-agent interactions.

This API provides a comprehensive framework to build intelligent agents that can reason, act, and interact with external tools seamlessly.

---

# References

- `autogen/agentchat/agent.py` — Defines the `Agent` and `LLMAgent` protocols.
- `autogen/agentchat/conversable_agent.py` — Implements the `ConversableAgent` class with detailed methods for tool calling, message handling, and chat management.

If you need further examples or specific usage scenarios, please ask!