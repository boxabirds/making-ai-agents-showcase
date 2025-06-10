# Comprehensive Guide to Using the `smolagents` API for Creating and Running Agents in Python

This document provides an exhaustive, detailed guide on how to use the `smolagents` package API to create agents that can be run directly in Python, including how to create a Python ReAct agent with tool calling. It includes references to source code and example scripts found in the package, as well as explanations of key classes and methods.

---

## Table of Contents

1. [Overview of the `smolagents` Package](#overview)
2. [Creating and Running an Agent in Python](#creating-running-agent)
3. [Creating a Python ReAct Agent with Tool Calling](#react-agent-tool-calling)
4. [Key Classes and Components](#key-classes)
5. [Example Scripts and Usage](#examples)
6. [Saving and Sharing Agents](#saving-sharing)
7. [References to Source Code and Documentation](#references)

---

<a name="overview"></a>
## 1. Overview of the `smolagents` Package

`smolagents` is a Python package designed to facilitate the creation of intelligent agents that interact with language models (LLMs) and tools in a ReAct (Reasoning + Acting) framework. It supports multiple agent types, including:

- **MultiStepAgent**: Base class for agents that solve tasks step-by-step.
- **ToolCallingAgent**: Agent that uses JSON-like tool calls leveraging LLM tool calling capabilities.
- **CodeAgent**: Agent that formulates tool calls as code snippets, parses, and executes them.

The package also provides utilities for tools, memory management, monitoring, and integration with various LLM backends.

---

<a name="creating-running-agent"></a>
## 2. Creating and Running an Agent in Python

### Basic Steps to Create and Run an Agent

1. **Import the necessary classes and tools** from `smolagents`.
2. **Define or import tools** that the agent can use.
3. **Instantiate a model** compatible with `smolagents` (e.g., `InferenceClientModel`, `TransformersModel`, `OpenAIServerModel`).
4. **Create an agent instance** (e.g., `CodeAgent` or `ToolCallingAgent`) with the model and tools.
5. **Run the agent** on a task using the `.run()` method.

### Example (from `examples/agent_from_any_llm.py`):

```python
from smolagents import CodeAgent, ToolCallingAgent, InferenceClientModel, tool

# Define a simple tool
@tool
def get_weather(location: str, celsius: bool | None = False) -> str:
    return "The weather is UNGODLY with torrential rains and temperatures below -10°C"

# Instantiate a model (choose your inference backend)
model = InferenceClientModel(model_id="meta-llama/Llama-3.3-70B-Instruct", provider="nebius")

# Create a ToolCallingAgent
agent = ToolCallingAgent(tools=[get_weather], model=model, verbosity_level=2)

# Run the agent on a task
print("ToolCallingAgent:", agent.run("What's the weather like in Paris?"))

# Create a CodeAgent with streaming output enabled
agent = CodeAgent(tools=[get_weather], model=model, verbosity_level=2, stream_outputs=True)

print("CodeAgent:", agent.run("What's the weather like in Paris?"))
```

- Save this script as `agent.py`.
- Run it directly with `python agent.py`.

---

<a name="react-agent-tool-calling"></a>
## 3. How to Create a Python ReAct Agent with Tool Calling

The `ToolCallingAgent` class is designed to leverage LLMs' tool calling capabilities using JSON-like calls. This is the recommended way to create a ReAct agent with tool calling.

### Key Points:

- The agent uses the model's `get_tool_call` method to parse tool calls.
- Tools are passed as a list of `Tool` instances decorated with `@tool`.
- The agent supports streaming outputs if the model supports `generate_stream`.
- The system prompt and planning prompts are loaded from a YAML template (`toolcalling_agent.yaml`).

### Minimal Example:

```python
from smolagents import ToolCallingAgent, InferenceClientModel, tool

@tool
def get_weather(location: str) -> str:
    return f"Weather at {location} is sunny."

model = InferenceClientModel(model_id="your-model-id")

agent = ToolCallingAgent(tools=[get_weather], model=model)

result = agent.run("What's the weather in New York?")
print(result)
```

### How It Works Internally (Reference: `src/smolagents/agents.py` lines ~400-600):

- The `_step_stream` method sends the conversation history to the model.
- The model returns a JSON-like tool call.
- The agent parses the tool call and executes the corresponding tool.
- Observations or final answers are yielded back to the caller.

---

<a name="key-classes"></a>
## 4. Key Classes and Components

### 4.1 `MultiStepAgent` (Base Class)

- Abstract base class for agents that solve tasks step-by-step.
- Manages tools, memory, planning, and execution steps.
- Implements `.run()` method to execute the agent on a task.
- Supports streaming and non-streaming modes.
- Reference: `src/smolagents/agents.py` lines 50-350.

### 4.2 `ToolCallingAgent`

- Subclass of `MultiStepAgent`.
- Uses LLM tool calling capabilities with JSON-like calls.
- Loads prompt templates from `toolcalling_agent.yaml`.
- Supports streaming outputs.
- Reference: `src/smolagents/agents.py` lines 400-600.

### 4.3 `CodeAgent`

- Subclass of `MultiStepAgent`.
- Tool calls are formulated as code snippets by the LLM.
- Parses and executes code using a Python executor (local, Docker, or remote).
- Supports structured outputs and streaming.
- Reference: `src/smolagents/agents.py` lines 600-900.

### 4.4 `Tool` and `@tool` Decorator

- Tools are Python functions decorated with `@tool`.
- They define the interface and logic for callable tools.
- Tools are passed to agents to enable tool usage.
- Reference: `src/smolagents/tools.py` (not fully shown here).

---

<a name="examples"></a>
## 5. Example Scripts and Usage

### 5.1 `examples/agent_from_any_llm.py`

- Demonstrates creating agents from various LLM backends.
- Shows usage of `ToolCallingAgent` and `CodeAgent`.
- Defines a simple `get_weather` tool.
- Shows how to run agents and print results.

### 5.2 `examples/multiple_tools.py`

- Shows how to define multiple tools (weather, currency conversion, news, jokes, etc.).
- Demonstrates creating a `CodeAgent` with multiple tools.
- Example usage of `.run()` with different queries.
- Shows commented-out example for `ToolCallingAgent` usage.

---

<a name="saving-sharing"></a>
## 6. Saving and Sharing Agents

The `MultiStepAgent` class supports saving and loading agents:

- `.save(output_dir)` saves the agent's code, tools, managed agents, prompts, and requirements.
- `.from_folder(folder)` loads an agent from a saved folder.
- `.push_to_hub(repo_id, ...)` uploads the agent to the Hugging Face Hub as a Space.

This enables easy sharing and deployment of agents.

Reference: `src/smolagents/agents.py` lines 300-400.

---

<a name="references"></a>
## 7. References to Source Code and Documentation

- **Agent Base and Implementations**: `src/smolagents/agents.py`
  - `MultiStepAgent` class: lines 50-350
  - `ToolCallingAgent` class: lines 400-600
  - `CodeAgent` class: lines 600-900
- **Example Usage**:
  - `examples/agent_from_any_llm.py`
  - `examples/multiple_tools.py`
- **Package Initialization**: `src/smolagents/__init__.py` (imports all key modules)
- **Prompt Templates**: Loaded from YAML files in `smolagents.prompts` (e.g., `toolcalling_agent.yaml`)
- **Tool Decorator and Tool Classes**: `src/smolagents/tools.py` (not fully shown here)
- **Model Interfaces**: `src/smolagents/models.py` (not fully shown here)
- **Memory and Monitoring**: `src/smolagents/memory.py`, `src/smolagents/monitoring.py`

---

# Summary

To create and run an agent directly in Python:

- Import `smolagents` classes and tools.
- Define your tools with `@tool`.
- Instantiate a compatible LLM model.
- Create an agent instance (`ToolCallingAgent` for JSON tool calls or `CodeAgent` for code-based tool calls).
- Call `.run()` on your task.
- Optionally, save or push your agent for reuse or deployment.

The `ToolCallingAgent` is the recommended approach for creating a Python ReAct agent with tool calling, leveraging modern LLM tool call capabilities.

---

If you want, I can help generate a minimal runnable `agent.py` script based on this package for your specific use case.