# CrewAI API Usage Guide for Creating a ReAct Agent with Tool Calling

This document provides an exhaustive and detailed guide on how to use the CrewAI API to create a ReAct (Reasoning and Acting) agent that supports tool calling. It covers the key classes, components, and workflows involved in building and executing such an agent.

---

## Table of Contents

- [Overview](#overview)
- [Key Concepts and Components](#key-concepts-and-components)
  - [BaseAgent](#baseagent)
  - [CrewAgentExecutorMixin](#crewagentexecutormixin)
  - [Tools and Tool Calling](#tools-and-tool-calling)
  - [ToolsHandler](#toolshandler)
- [How to Create a ReAct Agent with Tool Calling](#how-to-create-a-react-agent-with-tool-calling)
  - [Step 1: Define Your Agent](#step-1-define-your-agent)
  - [Step 2: Define and Register Tools](#step-2-define-and-register-tools)
  - [Step 3: Create Agent Executor](#step-3-create-agent-executor)
  - [Step 4: Execute Tasks with Tool Calling](#step-4-execute-tasks-with-tool-calling)
- [Example Workflow](#example-workflow)
- [Additional Features](#additional-features)
- [References to Source Files](#references-to-source-files)

---

## Overview

CrewAI provides a flexible framework to build intelligent agents that can reason and act by calling external tools. The API supports:

- Defining agents with roles, goals, and backstories.
- Associating tools with agents for task execution.
- Managing tool calls and caching results.
- Handling memory (short-term, long-term, external).
- Supporting human-in-the-loop feedback.
- Enforcing security and rate limits.

---

## Key Concepts and Components

### BaseAgent

- **Location:** `src/crewai/agents/agent_builder/base_agent.py`
- **Description:** Abstract base class for all agents compatible with CrewAI.
- **Key Attributes:**
  - `role`, `goal`, `backstory`: Define the agent's persona and objectives.
  - `tools`: List of tools available to the agent.
  - `agent_executor`: Instance responsible for executing tasks.
  - `llm`: Language model used by the agent.
  - `cache_handler`: Optional cache for tool usage.
  - `max_rpm`: Rate limit for requests.
  - `allow_delegation`: Enable delegation among agents.
- **Key Methods:**
  - `execute_task(task, context=None, tools=None)`: Abstract method to execute a task.
  - `create_agent_executor(tools=None)`: Abstract method to create the executor.
  - `get_delegation_tools(agents)`: Abstract method to get delegation tools.
  - `interpolate_inputs(inputs)`: Interpolate dynamic inputs into agent descriptions.
  - `set_cache_handler(cache_handler)`: Set cache handler and recreate executor.
  - `set_rpm_controller(rpm_controller)`: Set rate limit controller and recreate executor.
  - `copy()`: Create a deep copy of the agent.

**Usage Notes:**

- Tools must be instances of `BaseTool` or have `name`, `func`, and `description` attributes.
- The agent supports verbose logging and internationalization (i18n).
- Security configuration and knowledge sources can be attached.

---

### CrewAgentExecutorMixin

- **Location:** `src/crewai/agents/agent_builder/base_agent_executor_mixin.py`
- **Description:** Mixin class providing execution logic for agents.
- **Responsibilities:**
  - Manage memory creation (short-term, external, long-term).
  - Evaluate task results and save to long-term memory.
  - Prompt human input for feedback in training or human-in-the-loop modes.
- **Key Methods:**
  - `_create_short_term_memory(output)`: Save short-term memory if applicable.
  - `_create_external_memory(output)`: Save external memory if applicable.
  - `_create_long_term_memory(output)`: Evaluate and save long-term and entity memory.
  - `_ask_human_input(final_answer)`: Prompt human for feedback with appropriate messaging.

---

### Tools and Tool Calling

- **ToolCalling Class:**
  - **Location:** `src/crewai/tools/tool_calling.py`
  - Represents a tool call with:
    - `tool_name`: Name of the tool.
    - `arguments`: Dictionary of arguments for the tool.

- **InstructorToolCalling Class:**
  - Similar to `ToolCalling` but used for instructor or specialized tool calls.

---

### ToolsHandler

- **Location:** `src/crewai/agents/tools_handler.py`
- **Description:** Handles callbacks related to tool usage.
- **Key Attributes:**
  - `last_used_tool`: Stores the last tool called.
  - `cache`: Optional cache handler to store tool call results.
- **Key Method:**
  - `on_tool_use(calling, output, should_cache=True)`: Called when a tool finishes execution. It updates the last used tool and optionally caches the result.

---

## How to Create a ReAct Agent with Tool Calling

### Step 1: Define Your Agent

Create a subclass of `BaseAgent` or use an existing agent class. Define the agent's role, goal, backstory, and tools.

```python
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.tools.base_tool import BaseTool

class MyReactAgent(BaseAgent):
    def execute_task(self, task, context=None, tools=None):
        # Implement task execution logic, including tool calling
        pass

    def create_agent_executor(self, tools=None):
        # Create and assign the agent executor instance
        pass

    def get_delegation_tools(self, agents):
        # Return tools for delegation if applicable
        pass
```

### Step 2: Define and Register Tools

Define tools as subclasses of `BaseTool` or compatible objects with `name`, `func`, and `description`.

Example tool:

```python
from crewai.tools.base_tool import BaseTool

class DummyTool(BaseTool):
    name = "dummy_tool"
    description = "Useful for dummy queries"

    def func(self, query: str) -> str:
        return f"Dummy result for: {query}"
```

Add tools to your agent:

```python
agent.tools = [DummyTool()]
```

### Step 3: Create Agent Executor

Use `create_agent_executor()` to instantiate the executor that will run the agent's logic, including tool calling and reasoning.

This executor typically uses the language model (`llm`) and tools to process tasks.

### Step 4: Execute Tasks with Tool Calling

Call `execute_task()` on the agent with a task object. The agent will:

- Use the language model to reason about the task.
- Decide which tool to call and with what arguments.
- Call the tool and receive observations.
- Continue reasoning until a final answer is reached.

The tool calling format expected by the agent is:

```
Thought: ...
Action: <tool_name>
Action Input: <JSON arguments>
Observation: <tool output>
```

Once the agent has gathered enough information, it returns:

```
Thought: I now know the final answer
Final Answer: <answer>
```

---

## Example Workflow

The test cassette `test_agent_execute_task_with_tool.yaml` demonstrates a typical interaction:

- The agent is given a task to use a tool named `dummy_tool`.
- The agent reasons and decides to call `dummy_tool` with a query argument.
- The tool returns a result.
- The agent returns the final answer based on the tool's output.

This interaction follows the ReAct pattern of reasoning and acting with tool calls.

---

## Additional Features

- **Caching:** Tool results can be cached via `CacheHandler` to avoid redundant calls.
- **Memory:** The agent supports short-term, external, and long-term memory to store observations and evaluations.
- **Human Feedback:** The agent can prompt for human feedback during or after task execution.
- **Security:** Security configurations and fingerprinting are supported.
- **Rate Limiting:** The agent respects max requests per minute (RPM) limits.

---

## References to Source Files

- Agent base class and core logic:  
  `src/crewai/agents/agent_builder/base_agent.py`  
  `src/crewai/agents/agent_builder/base_agent_executor_mixin.py`

- Tool calling data models:  
  `src/crewai/tools/tool_calling.py`

- Tool usage callback handler:  
  `src/crewai/agents/tools_handler.py`

- Example test cassette demonstrating tool calling:  
  `tests/cassettes/test_agent_execute_task_with_tool.yaml`

---

# Summary

To create a ReAct agent with tool calling using the CrewAI API:

1. Define an agent subclassing `BaseAgent`.
2. Define and register tools compatible with the agent.
3. Create an agent executor to handle reasoning and tool calls.
4. Execute tasks where the agent reasons, calls tools, and returns final answers.

The API provides rich support for caching, memory, human feedback, and security to build robust intelligent agents.

---

If you need further code examples or details on specific components, please ask!