# AgentStack API Usage Guide: Creating a ReAct Agent with Tool Calling

This document provides an exhaustive guide on how to use the AgentStack API to create a ReAct agent with tool calling capabilities. It explains the core concepts, key classes, and methods, and provides a step-by-step example based on the provided codebase.

---

## Table of Contents

- [Overview](#overview)
- [Core Concepts](#core-concepts)
  - [Agent](#agent)
  - [Task](#task)
  - [Tools](#tools)
  - [Frameworks](#frameworks)
- [Key API Components](#key-api-components)
  - [`agentstack` Package](#agentstack-package)
  - `AgentConfig` Class (Agent Configuration)
  - Framework Interface and Entrypoint
  - ToolLoader and Tool Callables
- [How to Create a ReAct Agent with Tool Calling](#how-to-create-a-react-agent-with-tool-calling)
  - Step 1: Define Agent Configuration
  - Step 2: Define Tasks
  - Step 3: Use Tools
  - Step 4: Create Agent and Crew Classes
  - Step 5: Run the Agent
- [Example: Research Assistant Crew](#example-research-assistant-crew)
- [Additional Utilities](#additional-utilities)
- [Summary](#summary)

---

## Overview

AgentStack is a Python package designed to facilitate the creation and management of AI agents, tasks, and tools within a project. It supports multiple frameworks and provides utilities to define agents, tasks, and tools declaratively and programmatically.

The API supports the ReAct (Reasoning + Acting) agent pattern, allowing agents to call tools as part of their reasoning process.

---

## Core Concepts

### Agent

An **Agent** represents an autonomous AI entity with a defined role, goal, and backstory. Agents can use tools to perform actions and complete tasks.

- Agents are configured via YAML files (`src/config/agents.yaml`).
- The `AgentConfig` class provides an interface to read, write, and manage agent configurations.
- Agents are implemented as methods decorated with `@agentstack.agent` or framework-specific decorators.

### Task

A **Task** represents a unit of work or action that an agent can perform.

- Tasks are also configured via YAML files (`src/config/tasks.yaml`).
- Tasks are implemented as methods decorated with `@agentstack.task`.

### Tools

**Tools** are callable functions or modules that agents can invoke to perform specific actions (e.g., web scraping, querying databases).

- Tools are accessed via the `agentstack.tools` interface.
- Tools are wrapped with framework-specific decorators and optionally with `agentops` event recording.
- Tools can be added or removed from agents programmatically.

### Frameworks

AgentStack supports multiple frameworks (e.g., `crewai`, `langgraph`, `openai_swarm`, `llamaindex`).

- Frameworks define how agents, tasks, and tools are integrated into the user's project.
- The framework module handles code generation, validation, and wrapping of tools.
- The active framework is determined by the project configuration.

---

## Key API Components

### `agentstack` Package

The `agentstack` package exposes the public API for interacting with agents, tasks, tools, and frameworks.

- Decorators: `@agent` and `@task` mark methods as agents or tasks.
- Functions to get agents, tasks, and their names.
- `tools` object to access tool callables by name.

**Example from `agentstack/__init__.py`:**

```python
from agentstack.agents import get_agent, get_all_agents, get_all_agent_names
from agentstack.tasks import get_task, get_all_tasks, get_all_task_names
from agentstack.utils import get_framework
from agentstack import conf, frameworks

def agent(func):
    def wrap(*args, **kwargs):
        return func(*args, **kwargs)
    return wrap

def task(func):
    def wrap(*args, **kwargs):
        return func(*args, **kwargs)
    return wrap

class ToolLoader:
    def __getitem__(self, tool_name: str) -> list[Callable]:
        return frameworks.get_tool_callables(tool_name)

tools = ToolLoader()
```

### `AgentConfig` Class (Agent Configuration)

Located in `agentstack/agents.py`, this class manages agent configurations stored in YAML.

- Load agent config by name.
- Properties: `provider`, `model`, `prompt`.
- Context manager support for editing and saving.
- Example usage:

```python
with AgentConfig('researcher') as config:
    config.llm = "openai/gpt-4o"
```

### Framework Interface and Entrypoint

Located in `agentstack/frameworks/__init__.py`, this module defines the interface for framework modules.

- Framework modules implement methods to add agents, tasks, tools.
- They provide entrypoint file handling, validation, and tool wrapping.
- Tools are wrapped with `agentops` event recording and framework-specific decorators.

### ToolLoader and Tool Callables

- Tools are accessed via `agentstack.tools[tool_name]`.
- Returns a list of callable functions wrapped for the active framework.
- Example:

```python
tool_funcs = agentstack.tools["firecrawl"]
for func in tool_funcs:
    result = func(...)
```

---

## How to Create a ReAct Agent with Tool Calling

### Step 1: Define Agent Configuration

Create or update an agent configuration in `src/config/agents.yaml` with fields:

- `name`: Agent name (e.g., "researcher")
- `role`: Agent role description
- `goal`: Agent goal
- `backstory`: Agent backstory
- `llm`: Language model identifier (e.g., "openai/gpt-4o")

Use `AgentConfig` to programmatically manage this config.

### Step 2: Define Tasks

Define tasks similarly in `src/config/tasks.yaml` and manage via `TaskConfig` (not shown in detail here but analogous to `AgentConfig`).

### Step 3: Use Tools

Add tools to your agent by referencing them via `agentstack.tools[tool_name]`.

Tools are callable functions that the agent can invoke during execution.

### Step 4: Create Agent and Crew Classes

Define your agent and tasks as methods decorated with `@agent` and `@task` inside a class decorated with `@CrewBase` (from the framework, e.g., `crewai`).

Example from `examples/research_assistant/src/crew.py`:

```python
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
import agentstack

@CrewBase
class ResearchassistantCrew:

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["researcher"],
            tools=[
                *agentstack.tools["firecrawl"],
            ],
            verbose=True,
        )

    @agent
    def web_scraper(self) -> Agent:
        return Agent(
            config=self.agents_config["web_scraper"],
            tools=[
                *agentstack.tools["agentql"],
            ],
            verbose=True,
        )

    @task
    def research(self) -> Task:
        return Task(
            config=self.tasks_config["research"],
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
```

### Step 5: Run the Agent

Use the entrypoint script to initialize and run the crew.

Example from `examples/research_assistant/src/main.py`:

```python
import agentstack
import agentops
from crew import ResearchassistantCrew

agentops.init(default_tags=agentstack.get_tags())

instance = ResearchassistantCrew().crew()

def run():
    instance.kickoff(inputs=agentstack.get_inputs())

if __name__ == '__main__':
    run()
```

---

## Example: Research Assistant Crew

- Defines three agents: `researcher`, `web_scraper`, and `analyst`.
- Each agent is configured with specific tools (e.g., `"firecrawl"`, `"agentql"`).
- Defines tasks: `research`, `scrape_site`, `analyze`.
- Creates a crew that runs agents and tasks sequentially.

This example demonstrates how to combine agents, tasks, and tools into a working ReAct agent system.

---

## Additional Utilities

- `agentstack.get_tags()`: Returns tags relevant to the project and framework.
- `agentstack.get_agent(name)`: Load an agent configuration by name.
- `agentstack.get_all_agents()`: List all agent configurations.
- `agentstack.add_tool(tool, agent_name)`: Add a tool to an agent programmatically.
- `agentstack.remove_tool(tool, agent_name)`: Remove a tool from an agent.
- `agentstack.validate_project()`: Validate the project setup for the active framework.

---

## Summary

To create a ReAct agent with tool calling using AgentStack:

1. Define your agents and tasks in YAML config files or programmatically using `AgentConfig` and `TaskConfig`.
2. Use the `@agent` and `@task` decorators to define agent and task methods inside a `@CrewBase` class.
3. Assign tools to agents by accessing them via `agentstack.tools[tool_name]`.
4. Create a crew that orchestrates agents and tasks.
5. Run the crew using the provided entrypoint script, initializing `agentops` and passing inputs.

This approach leverages AgentStack's framework abstraction, tool wrapping, and configuration management to build powerful ReAct agents capable of tool calling.

---

If you need further details on any specific part of the API or example code, please ask!