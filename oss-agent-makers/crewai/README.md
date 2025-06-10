# Comprehensive Guide to Using the CrewAI Package to Create a Python ReAct Agent with Tool Calling

This document provides an exhaustive, detailed guide on how to use the CrewAI package to create an agent that can be run directly in Python (e.g., `python agent.py`). It specifically addresses how to create a Python ReAct agent with tool calling, leveraging the package's API and scaffold tools. The guide includes references to source code files and relevant code snippets to ground the explanation.

---

## Table of Contents

1. [Overview of CrewAI Agent Architecture](#overview-of-crewai-agent-architecture)
2. [Key Components for Creating an Agent](#key-components-for-creating-an-agent)
3. [Step-by-Step Guide to Creating a Python ReAct Agent](#step-by-step-guide-to-creating-a-python-react-agent)
4. [Using Scaffold Tools and Templates](#using-scaffold-tools-and-templates)
5. [Running the Agent Directly in Python](#running-the-agent-directly-in-python)
6. [References to Source Code and Documentation](#references-to-source-code-and-documentation)

---

## Overview of CrewAI Agent Architecture

CrewAI provides a modular and extensible framework for building AI agents that can interact with tools and perform complex tasks. The core concepts include:

- **Agent**: Represents an AI entity with a role, goal, backstory, and access to tools.
- **Tools**: Functional units that the agent can call to perform specific actions.
- **Agent Executor**: The runtime component that manages the agent's thought process, tool usage, and interaction with the language model (LLM).
- **Crew**: A collection of agents and tasks orchestrated together.
- **Memory**: Short-term, long-term, and external memory systems to store and recall information.

The package supports advanced features like tool calling, human-in-the-loop feedback, training modes, and delegation among agents.

---

## Key Components for Creating an Agent

### 1. BaseAgent (Abstract Base Class)

- **Location:** `src/crewai/agents/agent_builder/base_agent.py`
- **Description:** Abstract base class defining the interface and core attributes for all agents.
- **Key Methods:**
  - `execute_task`: Abstract method to execute a task.
  - `create_agent_executor`: Abstract method to create the agent executor.
  - `get_delegation_tools`: Abstract method to get tools for delegation among agents.
- **Attributes:** Role, goal, backstory, tools, LLM, crew, cache, security config, etc.

### 2. CrewAgentExecutor

- **Location:** `src/crewai/agents/crew_agent_executor.py`
- **Description:** Implements the agent execution loop, handling LLM responses, tool calls, memory updates, and human feedback.
- **Key Features:**
  - Manages the interaction loop with the LLM.
  - Executes tools via `execute_tool_and_check_finality`.
  - Supports function calling LLMs.
  - Handles human feedback and training data saving.
- **Usage:** Instantiated with LLM, agent, tools, prompt, and other configurations.

### 3. CrewStructuredTool

- **Location:** `src/crewai/tools/structured_tool.py`
- **Description:** Defines structured tools with argument schemas and callable functions.
- **Key Features:**
  - Can be created from Python functions with automatic argument schema inference.
  - Supports synchronous and asynchronous invocation.
  - Validates input arguments against Pydantic schemas.
- **Example:**
  ```python
  def add(a: int, b: int) -> int:
      """Add two numbers"""
      return a + b

  add_tool = CrewStructuredTool.from_function(add)
  ```

### 4. ToolsHandler

- **Location:** `src/crewai/agents/tools_handler.py`
- **Description:** Manages tool usage callbacks and caching.
- **Key Feature:** Tracks last used tool and optionally caches tool outputs.

### 5. AgentTools (Agent-related Tools Manager)

- **Location:** `src/crewai/tools/agent_tools/agent_tools.py`
- **Description:** Provides common tools for agent collaboration like delegation and question asking.
- **Example Tools:** `DelegateWorkTool`, `AskQuestionTool`.

---

## Step-by-Step Guide to Creating a Python ReAct Agent

### Step 1: Define Your Agent Class

Create a class inheriting from `BaseAgent`. Implement the abstract methods:

- `execute_task`: Define how the agent executes a task.
- `create_agent_executor`: Instantiate `CrewAgentExecutor` with the LLM, tools, and prompt.
- `get_delegation_tools`: Return tools for delegation if needed.

Example skeleton (based on `BaseAgent` interface):

```python
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.agents.crew_agent_executor import CrewAgentExecutor
from crewai.tools.structured_tool import CrewStructuredTool

class MyReactAgent(BaseAgent):
    def execute_task(self, task, context=None, tools=None) -> str:
        # Prepare inputs and run the agent executor
        self.create_agent_executor(tools)
        result = self.agent_executor.invoke({"input": task.input_text, "tool_names": ..., "tools": ...})
        return result["output"]

    def create_agent_executor(self, tools=None):
        tools = tools or self.tools
        prompt = {
            "system": "You are a helpful assistant.",
            "user": "{input}"
        }
        self.agent_executor = CrewAgentExecutor(
            llm=self.llm,
            task=None,
            crew=self.crew,
            agent=self,
            prompt=prompt,
            max_iter=self.max_iter,
            tools=tools,
            tools_names=", ".join([t.name for t in tools]),
            stop_words=["\n"],
            tools_description="Available tools: " + ", ".join([t.name for t in tools]),
            tools_handler=self.tools_handler,
        )
```

### Step 2: Define Tools Using `CrewStructuredTool`

Create tools by wrapping Python functions:

```python
from crewai.tools.structured_tool import CrewStructuredTool

def search_web(query: str) -> str:
    """Search the web for a query."""
    # Implement search logic here
    return "Search results for " + query

search_tool = CrewStructuredTool.from_function(search_web, description="Search the web for information.")
```

Add these tools to your agent's `tools` list.

### Step 3: Instantiate and Run the Agent

Create an instance of your agent, configure the LLM, tools, and optionally the crew. Then call `execute_task` with the input.

Example:

```python
agent = MyReactAgent(
    role="Researcher",
    goal="Answer questions using web search",
    backstory="An AI agent that can search the web.",
    llm=my_llm_instance,
    tools=[search_tool],
    max_iter=10,
)

output = agent.execute_task(task=SomeTask(input_text="What is AI?"))
print(output)
```

---

## Using Scaffold Tools and Templates

CrewAI provides CLI commands and templates to scaffold new crews and agents quickly.

### Creating a New Crew (with Agents and Tasks)

- **CLI Command:** `crewai create-crew <name>`
- **Location of CLI code:** `src/crewai/cli/create_crew.py`
- **Template files:** `src/crewai/cli/templates/crew/`

The template `crew.py` shows how to define a crew with agents and tasks using decorators:

```python
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

@CrewBase
class MyCrew():
    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def researcher(self) -> Agent:
        return Agent(config=self.agents_config['researcher'], verbose=True)

    @task
    def research_task(self) -> Task:
        return Task(config=self.tasks_config['research_task'])

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
```

The `main.py` template provides a runnable entry point:

```python
from datetime import datetime
from mycrew.crew import MyCrew

def run():
    inputs = {
        'topic': 'AI LLMs',
        'current_year': str(datetime.now().year)
    }
    MyCrew().crew().kickoff(inputs=inputs)

if __name__ == "__main__":
    run()
```

This structure allows running the crew with `python main.py`.

---

## Running the Agent Directly in Python

To run an agent directly:

1. Use the scaffolded `main.py` as an entry point.
2. Instantiate your crew and call `kickoff()` with inputs.
3. The crew manages agent execution, task orchestration, and tool calling.

Example command:

```bash
python main.py
```

This will run the crew and agents as defined in the scaffolded project.

---

## References to Source Code and Documentation

- **Agent Executor:** `src/crewai/agents/crew_agent_executor.py` (lines 1-300)
- **Base Agent:** `src/crewai/agents/agent_builder/base_agent.py` (lines 1-400)
- **Structured Tool:** `src/crewai/tools/structured_tool.py` (lines 1-200)
- **Tools Handler:** `src/crewai/agents/tools_handler.py`
- **Agent Tools Manager:** `src/crewai/tools/agent_tools/agent_tools.py`
- **CLI Create Crew:** `src/crewai/cli/create_crew.py`
- **Crew Template:** `src/crewai/cli/templates/crew/crew.py`
- **Main Template:** `src/crewai/cli/templates/crew/main.py`

---

## Summary

- Use `BaseAgent` to define your agent class.
- Use `CrewStructuredTool` to define tools with argument schemas.
- Use `CrewAgentExecutor` to run the agent's thought and tool-calling loop.
- Use CLI scaffolding (`crewai create-crew`) to generate a runnable crew project.
- Run the crew with a simple Python script (`main.py`) that calls `kickoff()`.

This approach leverages CrewAI's built-in scaffolding and runtime components to create powerful ReAct agents with tool calling capabilities efficiently.

---

If you want, I can help generate a minimal example `agent.py` script based on this package to demonstrate a runnable ReAct agent. Just ask!