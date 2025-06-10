# Langflow Agent API Usage Guide

This document provides an exhaustive guide on how to use the Langflow package API to create and run an agent directly in Python, specifically focusing on creating a Python ReAct agent with tool calling capabilities. It includes detailed references to the source code and highlights specialized tools provided by the package to simplify agent creation.

---

## 1. Creating and Running an Agent Directly in Python

### Overview

The Langflow package provides a modular and extensible API to create agents that can interact with language models and tools. The core agent class is `AgentComponent` located in:

- `src/backend/base/langflow/components/agents/agent.py`

This class extends `ToolCallingAgentComponent` (from `tool_calling.py`), which itself extends `LCToolsAgentComponent` (LangChain Tools Agent Component).

### Key Class: `AgentComponent`

- **Location:** `src/backend/base/langflow/components/agents/agent.py`
- **Description:** Defines an agent that can be configured with a language model, tools, memory, and system prompts. It supports running asynchronously and integrates tool calling.
- **Main method to run:** `message_response()` — asynchronously runs the agent and returns a response message.

### How to Use `AgentComponent`

1. **Instantiate the Agent:**

   ```python
   from langflow.components.agents.agent import AgentComponent

   agent = AgentComponent()
   ```

2. **Configure Inputs:**

   The agent expects inputs such as:
   - `agent_llm`: Model provider (e.g., "OpenAI")
   - Model-specific parameters (API keys, model names, etc.)
   - `system_prompt`: Instructions for the agent
   - `tools`: List of tools the agent can use
   - `memory` inputs (optional)
   - `add_current_date_tool`: Boolean to add a current date tool

3. **Set Inputs:**

   You can set these inputs as attributes on the agent instance, e.g.:

   ```python
   agent.agent_llm = "OpenAI"
   agent.system_prompt = "You are a helpful assistant that can use tools."
   agent.tools = [...]  # List of tools (StructuredTool instances)
   agent.add_current_date_tool = True
   ```

4. **Run the Agent:**

   The agent runs asynchronously:

   ```python
   import asyncio

   async def run_agent():
       response = await agent.message_response()
       print(response)

   asyncio.run(run_agent())
   ```

5. **Create a Python Script to Run the Agent:**

   Example `agent.py`:

   ```python
   import asyncio
   from langflow.components.agents.agent import AgentComponent
   from langflow.components.helpers.memory import MemoryComponent
   from langchain_core.tools import StructuredTool

   async def main():
       agent = AgentComponent()
       agent.agent_llm = "OpenAI"
       agent.system_prompt = "You are a helpful assistant that can use tools."
       # Add tools here, e.g., from LangChain or Langflow toolkits
       agent.tools = [/* StructuredTool instances */]
       agent.add_current_date_tool = True
       # Optionally set memory inputs
       # agent.memory_inputs = ...
       response = await agent.message_response()
       print(response)

   if __name__ == "__main__":
       asyncio.run(main())
   ```

---

## 2. Creating a Python ReAct Agent with Tool Calling

### What is a ReAct Agent?

ReAct (Reasoning + Acting) agents combine reasoning with tool usage, allowing the agent to decide when and how to call external tools during interaction.

### Langflow Support for Tool Calling Agents

Langflow provides a specialized agent component for tool calling:

- **Class:** `ToolCallingAgentComponent`
- **Location:** `src/backend/base/langflow/components/langchain_utilities/tool_calling.py`
- **Description:** Extends `LCToolsAgentComponent` and uses LangChain's `create_tool_calling_agent` to create an agent that supports tool calling.

### How to Create a ReAct Agent with Tool Calling

1. **Use `ToolCallingAgentComponent` or `AgentComponent` (which extends it):**

   The `AgentComponent` class inherits from `ToolCallingAgentComponent`, so it already supports tool calling.

2. **Set Up Language Model and Tools:**

   - Provide a language model instance (must be compatible with tool calling).
   - Provide a list of tools (instances of `StructuredTool` or compatible).

3. **Create the Agent Runnable:**

   The `create_agent_runnable()` method in `ToolCallingAgentComponent` creates the LangChain tool calling agent:

   ```python
   from langflow.components.langchain_utilities.tool_calling import ToolCallingAgentComponent

   agent_component = ToolCallingAgentComponent()
   agent_component.llm = your_llm_instance
   agent_component.tools = your_tools_list
   agent = agent_component.create_agent_runnable()
   ```

4. **Run the Agent:**

   Use the `run_agent()` method or your own async runner to execute the agent with input.

### Example Snippet from `tool_calling.py`:

```python
from langchain.agents import create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate

class ToolCallingAgentComponent(LCToolsAgentComponent):
    # ...

    def create_agent_runnable(self):
        messages = [
            ("system", "{system_prompt}"),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
        prompt = ChatPromptTemplate.from_messages(messages)
        self.validate_tool_names()
        return create_tool_calling_agent(self.llm, self.tools or [], prompt)
```

This method creates a prompt template and uses LangChain's `create_tool_calling_agent` to instantiate the agent.

---

## 3. Grounding and References

### Source Code References

- **AgentComponent (main agent class):**  
  `src/backend/base/langflow/components/agents/agent.py`  
  - Implements agent setup, memory integration, tool addition (including current date tool), and running the agent asynchronously.  
  - Handles model provider selection and dynamic build config updates.

- **ToolCallingAgentComponent (tool calling agent base):**  
  `src/backend/base/langflow/components/langchain_utilities/tool_calling.py`  
  - Uses LangChain's `create_tool_calling_agent` to create a tool calling agent.  
  - Defines inputs for LLM, system prompt, and chat history.

- **Starter Projects (example agent graphs):**  
  `src/backend/base/langflow/initial_setup/starter_projects/complex_agent.py`  
  `src/backend/base/langflow/initial_setup/starter_projects/sequential_tasks_agent.py`  
  - These files show example complex agents built using Langflow components, including tool usage and multi-agent orchestration.

### Online Documentation

- Langflow GitHub or official docs (if available) for API references and examples.
- LangChain documentation for `create_tool_calling_agent`:  
  https://python.langchain.com/en/latest/modules/agents/tool_calling.html

---

## 4. Using Specialist Tools and Scaffold Tools

Langflow provides scaffold components and starter projects that simplify agent creation:

- **Component Toolkit:**  
  The agent uses `_get_component_toolkit()` to fetch tools and update metadata dynamically. This toolkit helps build tools from components without hand-coding each tool.

- **MemoryComponent:**  
  Provides chat memory integration for agents, allowing stateful conversations.

- **CurrentDateComponent:**  
  Adds a tool that returns the current date, useful for agents needing temporal context.

- **Starter Projects:**  
  Predefined agent graphs like `complex_agent_graph()` and `sequential_tasks_agent_graph()` demonstrate how to compose agents with tools, prompts, and tasks. These can be used as templates or starting points.

---

## Summary Example: Creating and Running a Simple Tool Calling Agent

```python
import asyncio
from langflow.components.agents.agent import AgentComponent
from langflow.components.helpers.memory import MemoryComponent
from langchain_core.tools import StructuredTool

async def main():
    agent = AgentComponent()
    agent.agent_llm = "OpenAI"  # or another supported provider
    agent.system_prompt = "You are a helpful assistant that can use tools."
    
    # Example: Add a current date tool (automatically added if add_current_date_tool=True)
    agent.add_current_date_tool = True
    
    # Add your tools here (must be StructuredTool instances)
    # For example, tools = [some_tool1, some_tool2]
    agent.tools = []  # Add actual tools
    
    # Optionally set memory inputs
    # agent.memory_inputs = ...
    
    response = await agent.message_response()
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
```

---

# Conclusion

The Langflow package provides a powerful and flexible API to create agents with tool calling capabilities in Python. The `AgentComponent` class is the primary interface for creating agents that can be run directly. It leverages the `ToolCallingAgentComponent` for tool calling support, which internally uses LangChain's `create_tool_calling_agent`.

Specialized components and starter projects provide scaffolding to build complex agents with minimal hand-coding. This guide, grounded in the source code and LangChain documentation, should enable you to create, customize, and run your own Python ReAct agents with tool calling using Langflow.

---

If you need further examples or help with specific tools or configurations, please ask!