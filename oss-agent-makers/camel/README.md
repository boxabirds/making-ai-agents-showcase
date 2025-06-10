# CAMEL API Usage Guide: Creating a ReAct Agent with Tool Calling

This document provides an exhaustive, detailed guide on how to use the CAMEL API to create a ReAct (Reasoning and Acting) agent with tool calling capabilities. It covers the core concepts, API usage, and practical examples to help you build an agent that can reason, call external tools, and interact effectively.

---

## Table of Contents

- [1. Overview of CAMEL Agents](#1-overview-of-camel-agents)
- [2. Creating a Chat Agent](#2-creating-a-chat-agent)
- [3. Defining and Using Tools](#3-defining-and-using-tools)
- [4. Integrating Tools with ChatAgent](#4-integrating-tools-with-chatagent)
- [5. Example: Role-Playing Agent with Tool Calling](#5-example-role-playing-agent-with-tool-calling)
- [6. Best Practices and Advanced Features](#6-best-practices-and-advanced-features)
- [7. Additional Resources](#7-additional-resources)

---

## 1. Overview of CAMEL Agents

CAMEL agents are autonomous entities designed to perform tasks by interacting with language models and other components. The primary agent class for conversational and tool-using agents is the `ChatAgent`.

### Key Features of `ChatAgent`:

- Supports system message configuration for role definition.
- Manages conversation memory.
- Supports tool/function calling.
- Supports structured output formats.
- Supports multiple model backends and async operation.

Agents inherit from a base class `BaseAgent` with core methods:

- `reset()`: Reset the agent state.
- `step()`: Perform a single interaction step.

---

## 2. Creating a Chat Agent

You can create a `ChatAgent` in multiple ways depending on how you want to specify the underlying language model.

### Example: Different Ways to Initialize a ChatAgent

```python
from camel.agents import ChatAgent
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType

# Method 1: Using a model name string (default platform OpenAI)
agent_1 = ChatAgent("You are a helpful assistant.", model="gpt-4o-mini")

# Method 2: Using ModelType enum
agent_2 = ChatAgent("You are a helpful assistant.", model=ModelType.GPT_4O_MINI)

# Method 3: Using a tuple of strings (platform, model)
agent_3 = ChatAgent("You are a helpful assistant.", model=("anthropic", "claude-3-5-sonnet-latest"))

# Method 4: Using a tuple of enums
agent_4 = ChatAgent(
    "You are a helpful assistant.",
    model=(ModelPlatformType.ANTHROPIC, ModelType.CLAUDE_3_5_SONNET),
)

# Method 5: Default model (no model specified)
agent_5 = ChatAgent("You are a helpful assistant.")

# Method 6: Using a pre-created model instance
model = ModelFactory.create(
    model_platform=ModelPlatformType.OPENAI,
    model_type=ModelType.GPT_4O_MINI,
)
agent_6 = ChatAgent("You are a helpful assistant.", model=model)
```

### Using the Agent

```python
response = agent_3.step("Which model are you?")
print(response.msgs[0].content)
# Output: I am Claude, an AI assistant created by Anthropic...
```

---

## 3. Defining and Using Tools

Tools in CAMEL are function-like entities that agents can call to perform external actions or computations. They are similar to OpenAI Functions and can be wrapped using `FunctionTool`.

### Defining a Custom Tool

```python
from camel.toolkits import FunctionTool

def add(a: int, b: int) -> int:
    """Adds two numbers."""
    return a + b

add_tool = FunctionTool(add)
```

### Inspecting Tool Properties

```python
print(add_tool.get_function_name())  # Output: add
print(add_tool.get_function_description())  # Output: Adds two numbers.
print(add_tool.get_openai_function_schema())  # Output: JSON schema for OpenAI function
print(add_tool.get_openai_tool_schema())  # Output: Tool schema compatible with OpenAI
```

### Using Built-in Toolkits

CAMEL provides many built-in toolkits, e.g., `SearchToolkit`, `MathToolkit`, etc.

```python
from camel.toolkits import SearchToolkit

search_tool = SearchToolkit().search_duckduckgo
```

---

## 4. Integrating Tools with ChatAgent

You can pass tools to the `ChatAgent` during initialization to enable tool calling.

```python
from camel.agents import ChatAgent
from camel.toolkits import FunctionTool, SearchToolkit

# Define or get tools
search_tool = SearchToolkit().search_duckduckgo
calculator_tool = FunctionTool(lambda a, b: a + b)

# Create agent with tools
agent = ChatAgent(
    model="gpt-4o-mini",
    tools=[search_tool, calculator_tool],
)

# Use the agent
response = agent.step("What is 5 + 3?")
print(response.msgs[0].content)
```

---

## 5. Example: Role-Playing Agent with Tool Calling

The following example demonstrates a ReAct style agent setup where an assistant and user role play a task involving tool calls (math and search).

```python
from camel.models import ModelFactory
from camel.societies import RolePlaying
from camel.toolkits import MathToolkit, SearchToolkit
from camel.types import ModelPlatformType, ModelType

def main():
    task_prompt = (
        "Assume now is 2024 in the Gregorian calendar, "
        "estimate the current age of University of Oxford "
        "and then add 10 more years to this age, "
        "and get the current weather of the city where "
        "the University is located. You must use tool to solve the task."
    )

    tools_list = [
        *MathToolkit().get_tools(),
        SearchToolkit().search_duckduckgo,
    ]

    role_play_session = RolePlaying(
        assistant_role_name="Searcher",
        user_role_name="Professor",
        assistant_agent_kwargs=dict(
            model=ModelFactory.create(
                model_platform=ModelPlatformType.DEFAULT,
                model_type=ModelType.DEFAULT,
            ),
            tools=tools_list,
        ),
        user_agent_kwargs=dict(
            model=ModelFactory.create(
                model_platform=ModelPlatformType.DEFAULT,
                model_type=ModelType.DEFAULT,
            ),
        ),
        task_prompt=task_prompt,
        with_task_specify=False,
    )

    input_msg = role_play_session.init_chat()
    chat_turn_limit = 10
    for _ in range(chat_turn_limit):
        assistant_response, user_response = role_play_session.step(input_msg)

        if assistant_response.terminated or user_response.terminated:
            break

        print("User:", user_response.msg.content)
        print("Assistant:", assistant_response.msg.content)

        if "CAMEL_TASK_DONE" in user_response.msg.content:
            break

        input_msg = assistant_response.msg

if __name__ == "__main__":
    main()
```

This example shows:

- Creating a role-playing session with two agents.
- Passing toolkits (math and search) to the assistant agent.
- Running a conversation loop where the assistant can call tools to solve the task.
- Terminating when the task is done or turn limit is reached.

---

## 6. Best Practices and Advanced Features

- **Memory Management:** Use conversation memory to maintain context over multiple steps.
- **Tool Integration:** Keep tools focused and handle errors gracefully.
- **Structured Output:** Use Pydantic models to enforce structured responses.
- **Model Scheduling:** CAMEL supports multiple model backends with customizable scheduling strategies.
- **Output Language Control:** You can set the language of agent responses.

Example of setting output language:

```python
agent.set_output_language("Spanish")
```

---

## 7. Additional Resources

- [CAMEL Agents Documentation](https://docs.camel-ai.org/key_modules/agents.html)
- [Tools and Toolkits Documentation](https://docs.camel-ai.org/key_modules/tools.html)
- [Tools Cookbook](https://docs.camel-ai.org/cookbooks/advanced_features/agents_with_tools.html)
- [Role Playing with Functions Example](examples/toolkits/role_playing_with_functions.py)
- [Create Chat Agent Example](examples/agents/create_chat_agent.py)

---

# Summary

To create a ReAct agent with tool calling in CAMEL:

1. Define or use existing tools wrapped as `FunctionTool` or from toolkits.
2. Create a `ChatAgent` and pass the tools list during initialization.
3. Use the `step()` method to interact with the agent, which can call tools as needed.
4. For complex scenarios, use `RolePlaying` to simulate multi-agent interactions with tool calling.
5. Leverage CAMEL's built-in toolkits and model factory for flexible model and tool management.

This approach enables building powerful agents that can reason, act, and interact with external tools seamlessly.

---

If you need further help, join the CAMEL community on [Discord](https://discord.camel-ai.org/) or consult the official documentation at [docs.camel-ai.org](https://docs.camel-ai.org).