# Griptape API Usage Guide: Creating a ReAct Agent with Tool Calling

This document provides an exhaustive and detailed guide on how to use the Griptape API to create a ReAct (Reasoning and Acting) agent that can call tools. It explains the core components, their relationships, and step-by-step instructions to build and run such an agent.

---

## Table of Contents

- [Overview](#overview)
- [Core Concepts](#core-concepts)
  - [Agent](#agent)
  - [PromptTask](#prompttask)
  - [BaseTool and Tool Activities](#basetool-and-tool-activities)
  - [RagTool (Example Tool)](#ragtool-example-tool)
- [Creating a ReAct Agent with Tool Calling](#creating-a-react-agent-with-tool-calling)
  - [Step 1: Define Tools](#step-1-define-tools)
  - [Step 2: Create an Agent](#step-2-create-an-agent)
  - [Step 3: Configure the Agent's PromptTask](#step-3-configure-the-agents-prompttask)
  - [Step 4: Run the Agent](#step-4-run-the-agent)
- [Detailed Code Examples](#detailed-code-examples)
- [Additional Notes](#additional-notes)

---

## Overview

Griptape provides a flexible framework to build AI agents that can reason and act by calling external tools. The core abstraction is the `Agent` structure, which internally manages a `PromptTask` that interacts with a language model (via a prompt driver) and a set of tools. Tools encapsulate external capabilities or APIs that the agent can invoke during its reasoning process.

---

## Core Concepts

### Agent

- Defined in `griptape.structures.agent.Agent` (see `structures/agent.py`).
- Represents a high-level AI agent structure.
- Holds a single `PromptTask` internally (only one task allowed).
- Accepts:
  - `input`: The initial input to the agent (string, artifact, or callable).
  - `tools`: A list of tools the agent can call.
  - `prompt_driver`: The driver that interfaces with the language model.
  - `output_schema`: Optional schema to validate output.
  - `stream`: Whether to stream output.
- The agent runs by invoking its internal `PromptTask`.

Key methods and properties:
- `add_task(task)`: Adds the single task (usually a `PromptTask`).
- `try_run()`: Runs the agent's task.
- `task`: Property to access the internal task.

Example snippet from `Agent` class:
```python
task = PromptTask(
    self.input,
    prompt_driver=prompt_driver,
    tools=self.tools,
    output_schema=self.output_schema,
    max_meta_memory_entries=self.max_meta_memory_entries,
)
self.add_task(task)
```

---

### PromptTask

- Defined in `griptape.tasks.prompt_task.PromptTask` (see `tasks/prompt_task.py`).
- Represents the core task that manages prompt construction, tool calling, and response handling.
- Uses a `prompt_driver` to interact with the language model.
- Maintains a list of `tools` that it can invoke.
- Supports subtasks representing individual tool calls or output schema validations.
- Supports streaming and conversation memory integration.
- Has customizable templates for system, user, and assistant messages.
- Runs by building a prompt stack, sending it to the LLM, and processing the output including tool calls.

Key features:
- `tools`: List of tools available for the task.
- `prompt_stack`: Builds the prompt including system, user, assistant messages, and memory.
- `try_run()`: Runs the prompt driver and processes subtasks (tool calls).
- `default_run_actions_subtasks()`: Runs subtasks that represent tool calls.
- `default_run_output_schema_validation_subtasks()`: Validates output against schema if provided.

---

### BaseTool and Tool Activities

- Defined in `griptape.tools.base_tool.BaseTool` (see `tools/base_tool.py`).
- Abstract base class for all tools.
- Tools define activities (methods decorated with `@activity`) that can be called by the agent.
- Supports input and output memory for stateful interactions.
- Supports automatic dependency installation from `requirements.txt`.
- Provides schema for tool activities to enable structured tool calling.
- Handles running activities and converting results to artifacts.

Key methods:
- `run(activity, subtask, action)`: Runs a specific activity.
- `try_run(activity, subtask, action, value)`: Executes the activity and returns an artifact.
- `activity_schemas()`: Returns schemas for all activities for integration with LLM.

---

### RagTool (Example Tool)

- Defined in `griptape.tools.rag.tool.RagTool` (see `tools/rag/tool.py`).
- A concrete tool example that queries a Retrieval-Augmented Generation (RAG) engine.
- Has a single activity `search` that accepts a query and returns a list of artifacts or an error artifact.
- Demonstrates how to define a tool with an activity and schema for tool calling.

Example activity definition:
```python
@activity(
    config={
        "description": "{{ _self.description }}",
        "schema": Schema({Literal("query", description="A natural language search query"): str}),
    },
)
def search(self, params: dict) -> ListArtifact | ErrorArtifact:
    query = params["values"]["query"]
    try:
        artifacts = self.rag_engine.process_query(query).outputs
        # Process and return artifacts...
    except Exception as e:
        return ErrorArtifact(f"error querying: {e}")
```

---

## Creating a ReAct Agent with Tool Calling

### Step 1: Define Tools

- Create or use existing tools inheriting from `BaseTool`.
- Define activities decorated with `@activity` that the agent can call.
- Example: Use `RagTool` or other official tools like `CalculatorTool`, `WebSearchTool`, etc.

### Step 2: Create an Agent

- Instantiate an `Agent` object.
- Provide the initial input (string or artifact).
- Provide a list of tools the agent can use.
- Optionally specify a `prompt_driver` or use the default.

Example:
```python
from griptape.structures import Agent
from griptape.tools.rag.tool import RagTool

rag_tool = RagTool(description="RAG search tool", rag_engine=my_rag_engine)

agent = Agent(
    input="What is the capital of France?",
    tools=[rag_tool],
)
```

### Step 3: Configure the Agent's PromptTask

- The agent internally creates a `PromptTask` with the tools and prompt driver.
- You can customize the prompt driver or output schema if needed.
- The `PromptTask` manages the prompt stack, tool calling, and subtasks.

### Step 4: Run the Agent

- Call `agent.try_run()` to execute the agent.
- The agent will process the input, call tools as needed, and produce output.
- The output is an artifact (e.g., `TextArtifact`) representing the final response.

Example:
```python
result = agent.try_run()
print(result.output.to_text())
```

---

## Detailed Code Examples

### Example: Creating a ReAct Agent with a RAG Tool

```python
from griptape.structures import Agent
from griptape.tools.rag.tool import RagTool
from griptape.engines.rag import RagEngine  # hypothetical import

# Initialize your RAG engine (implementation specific)
my_rag_engine = RagEngine(...)

# Create the RAG tool
rag_tool = RagTool(description="RAG search tool", rag_engine=my_rag_engine)

# Create the agent with input and tools
agent = Agent(
    input="Find information about the Eiffel Tower.",
    tools=[rag_tool],
)

# Run the agent
result = agent.try_run()

# Output the result text
print(result.output.to_text())
```

---

## Additional Notes

- The `Agent` class only supports a single task internally, which is typically a `PromptTask`.
- Tools must have unique names within the agent.
- The `PromptTask` supports subtasks for tool calls and output validation.
- The prompt driver can be customized or defaulted from configuration.
- The framework supports streaming output and conversation memory for context.
- Tools can automatically install dependencies if a `requirements.txt` is present.
- The `@activity` decorator on tool methods defines callable activities with schemas for LLM integration.

---

This guide should enable you to understand and use the Griptape API to create a ReAct agent capable of calling tools effectively. For more advanced usage, explore the `PromptTask` customization, tool development, and memory management features in the codebase.