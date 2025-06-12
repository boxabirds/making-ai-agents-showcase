# LangGraph-Swarm-Py API Usage Guide for Creating a Python ReAct Agent with Tool Calling

This document provides an exhaustive guide on how to use the `langgraph-swarm-py` package API to create and run a multi-agent ReAct (Reasoning and Acting) agent system in Python. It includes detailed references to source code and usage examples, focusing on creating an agent that can be run directly (e.g., `python agent.py`) and how to implement a Python ReAct agent with tool calling.

---

## Table of Contents

1. [Overview of the Package](#overview-of-the-package)
2. [Creating a ReAct Agent](#creating-a-react-agent)
3. [Creating a Multi-Agent Swarm](#creating-a-multi-agent-swarm)
4. [Using Handoff Tools for Agent Communication](#using-handoff-tools-for-agent-communication)
5. [Example: Running a Multi-Agent ReAct System](#example-running-a-multi-agent-react-system)
6. [Summary and References](#summary-and-references)

---

## Overview of the Package

The `langgraph-swarm-py` package builds on top of LangGraph and LangChain to enable multi-agent workflows with tool calling and agent handoff capabilities. It provides:

- Facilities to create individual ReAct agents with tools.
- Utilities to create handoff tools that allow agents to transfer control to each other.
- A `SwarmState` and `StateGraph` based system to manage multi-agent state and routing.
- A `create_swarm` function to combine multiple agents into a single multi-agent system.

Key modules and files:
- `langgraph_swarm/swarm.py`: Core multi-agent swarm creation and routing logic.
- `langgraph_swarm/handoff.py`: Tools for creating handoff tools to transfer control between agents.
- `examples/research/src/agent/agent.py`: Example usage of creating and running a multi-agent system.
- `examples/research/src/agent/configuration.py`: Configuration management.
- `examples/research/src/agent/prompts.py`: Prompts used for agents.
- `examples/research/src/agent/utils.py`: Utility functions including document fetching.

---

## Creating a ReAct Agent

The package leverages LangGraph's `create_react_agent` function to create ReAct agents. This function initializes an agent with a language model, a prompt, and a set of tools it can use.

### Key points from `examples/research/src/agent/agent.py`:

```python
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent

# Initialize the language model (e.g., GPT-4o from OpenAI)
model = init_chat_model(model="gpt-4o", model_provider="openai")

# Create a ReAct agent with a prompt and tools
planner_agent = create_react_agent(
    model,
    prompt=planner_prompt_formatted,
    tools=[fetch_doc, transfer_to_researcher_agent],
    name="planner_agent",
)
```

- `model`: The language model instance.
- `prompt`: The prompt guiding the agent's behavior.
- `tools`: A list of callable tools the agent can use (e.g., `fetch_doc` to fetch documents, handoff tools).
- `name`: Unique name for the agent.

---

## Creating a Multi-Agent Swarm

The package provides a high-level API to create a multi-agent swarm that manages multiple agents and routes requests between them.

### Core function: `create_swarm` (from `langgraph_swarm/swarm.py`)

```python
def create_swarm(
    agents: list[Pregel],
    *,
    default_active_agent: str,
    state_schema: StateSchemaType = SwarmState,
    config_schema: Type[Any] | None = None,
) -> StateGraph:
    ...
```

- `agents`: List of agents (e.g., created by `create_react_agent`).
- `default_active_agent`: The agent to route to by default.
- Returns a `StateGraph` representing the multi-agent swarm.

### How it works:

- Updates the state schema to include the active agent.
- Adds a router node that routes requests to the currently active agent.
- Adds each agent as a node in the graph.
- Uses handoff destinations to define edges between agents.

---

## Using Handoff Tools for Agent Communication

Agents can transfer control to each other using handoff tools created by `create_handoff_tool`.

### Function: `create_handoff_tool` (from `langgraph_swarm/handoff.py`)

```python
def create_handoff_tool(
    *, agent_name: str, name: str | None = None, description: str | None = None
) -> BaseTool:
    ...
```

- `agent_name`: The target agent to transfer control to.
- Returns a tool that, when called, updates the state to set the active agent to the target.

### Example usage:

```python
transfer_to_planner_agent = create_handoff_tool(
    agent_name="planner_agent",
    description="Transfer the user to the planner_agent for clarifying questions."
)
```

This tool can be included in an agent's tool list to enable transferring control.

---

## Example: Running a Multi-Agent ReAct System

The example in `examples/research/src/agent/agent.py` demonstrates creating two agents (`planner_agent` and `researcher_agent`), each with their own prompts and tools, and combining them into a swarm.

### Key code snippet:

```python
from langgraph.prebuilt import create_react_agent
from langgraph_swarm import create_handoff_tool, create_swarm
from swarm_researcher.prompts import planner_prompt, researcher_prompt
from swarm_researcher.utils import fetch_doc

# Initialize model
model = init_chat_model(model="gpt-4o", model_provider="openai")

# Create handoff tools
transfer_to_planner_agent = create_handoff_tool(agent_name="planner_agent")
transfer_to_researcher_agent = create_handoff_tool(agent_name="researcher_agent")

# Format prompts
llms_txt = "LangGraph:https://langchain-ai.github.io/langgraph/llms.txt"
num_urls = 3
planner_prompt_formatted = planner_prompt.format(llms_txt=llms_txt, num_urls=num_urls)

# Create agents
planner_agent = create_react_agent(
    model,
    prompt=planner_prompt_formatted,
    tools=[fetch_doc, transfer_to_researcher_agent],
    name="planner_agent",
)

researcher_agent = create_react_agent(
    model,
    prompt=researcher_prompt,
    tools=[fetch_doc, transfer_to_planner_agent],
    name="researcher_agent",
)

# Create swarm
agent_swarm = create_swarm(
    [planner_agent, researcher_agent], default_active_agent="planner_agent"
)

# Compile the swarm into an app
app = agent_swarm.compile()

# Now `app` can be invoked with user messages to run the multi-agent system.
```

### Running the agent

You can create a Python script (e.g., `agent.py`) with the above code and run it directly:

```bash
python agent.py
```

You would then invoke the compiled app with user messages to interact with the agents.

---

## How to Create a Python ReAct Agent with Tool Calling Using This API

1. **Initialize a language model** using `init_chat_model` from `langchain.chat_models`.
2. **Create tools** your agent will use. This can include:
   - Custom tools (e.g., `fetch_doc` for fetching documents).
   - Handoff tools created with `create_handoff_tool` to enable agent switching.
3. **Create a ReAct agent** using `create_react_agent` from `langgraph.prebuilt`:
   - Pass the model, prompt, tools, and a unique name.
4. **(Optional) Create multiple agents** and combine them into a swarm using `create_swarm` from `langgraph_swarm`.
5. **Compile the swarm** to get an executable app.
6. **Invoke the app** with user messages to run the agent(s).

---

## References and Further Reading

- **Source code for swarm creation and routing:**  
  [`langgraph_swarm/swarm.py`](output/cache/langchain-ai/langgraph-swarm-py/langgraph_swarm/swarm.py)  
  Key functions: `create_swarm`, `add_active_agent_router`

- **Source code for handoff tools:**  
  [`langgraph_swarm/handoff.py`](output/cache/langchain-ai/langgraph-swarm-py/langgraph_swarm/handoff.py)  
  Key function: `create_handoff_tool`

- **Example multi-agent system:**  
  [`examples/research/src/agent/agent.py`](output/cache/langchain-ai/langgraph-swarm-py/examples/research/src/agent/agent.py)

- **Prompts used for agents:**  
  [`examples/research/src/agent/prompts.py`](output/cache/langchain-ai/langgraph-swarm-py/examples/research/src/agent/prompts.py)

- **Utility functions (e.g., document fetching):**  
  [`examples/research/src/agent/utils.py`](output/cache/langchain-ai/langgraph-swarm-py/examples/research/src/agent/utils.py)

- **LangGraph documentation:**  
  https://langchain-ai.github.io/langgraph/

---

## Summary

- Use `init_chat_model` to initialize your LLM.
- Use `create_react_agent` to create agents with prompts and tools.
- Use `create_handoff_tool` to enable agents to transfer control.
- Use `create_swarm` to combine multiple agents into a multi-agent system.
- Compile the swarm and invoke it to run your multi-agent ReAct system.
- The example in `examples/research/src/agent/agent.py` is a complete reference implementation.

This approach leverages the package's scaffold tools to simplify multi-agent ReAct agent creation with tool calling, avoiding the need to hand-code complex routing or state management.

---

# Appendix: Minimal Example to Create and Run a Single ReAct Agent

```python
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent

# Initialize model
model = init_chat_model(model="gpt-4o", model_provider="openai")

# Define a simple tool (example)
def add(a: int, b: int) -> int:
    return a + b

# Create agent
agent = create_react_agent(
    model,
    tools=[add],
    prompt="You are an addition expert.",
    name="simple_agent",
)

# Compile and run
app = agent.compile()
response = app.invoke({"messages": [{"role": "user", "content": "What is 5 + 7?"}]})
print(response)
```

---

This concludes the detailed guide on using the `langgraph-swarm-py` package to create Python ReAct agents with tool calling.