# LangGraph-Swarm-Py API Usage Guide for Creating a ReAct Agent with Tool Calling

This document provides an exhaustive and detailed explanation of how to use the `langgraph-swarm-py` package API to create a ReAct agent with tool calling capabilities, specifically focusing on building a multi-agent ReAct system (a "swarm") with agent handoff (tool calling) between agents.

---

## Table of Contents

- [Overview](#overview)
- [Key Concepts and Components](#key-concepts-and-components)
- [Core API Functions and Classes](#core-api-functions-and-classes)
  - [`SwarmState`](#swarmstate)
  - [`create_handoff_tool`](#create_handoff_tool)
  - [`add_active_agent_router`](#add_active_agent_router)
  - [`create_swarm`](#create_swarm)
- [Step-by-Step Guide to Create a ReAct Agent with Tool Calling](#step-by-step-guide-to-create-a-react-agent-with-tool-calling)
- [Example Usage](#example-usage)
- [Additional Notes](#additional-notes)

---

## Overview

The `langgraph-swarm-py` package enables the creation of multi-agent systems ("swarms") where multiple ReAct agents can interact and hand off control to each other via tool calls. This is useful for complex workflows where different agents specialize in different tasks and can transfer control dynamically.

The package builds on top of LangGraph's `StateGraph` and `Pregel` abstractions and provides utilities to:

- Define a shared state schema for the swarm (`SwarmState`).
- Create handoff tools that allow agents to transfer control to other agents.
- Add routing logic to track the currently active agent.
- Compose multiple agents into a swarm with automatic routing and handoff.

---

## Key Concepts and Components

- **ReAct Agent**: An agent built using LangGraph's `create_react_agent` function, which supports reasoning and acting with tools.
- **Tool Calling / Handoff**: Mechanism by which one agent can transfer control to another agent by invoking a special "handoff" tool.
- **Swarm**: A multi-agent system composed of multiple ReAct agents connected in a graph with routing and handoff capabilities.
- **StateGraph**: The underlying graph structure representing the multi-agent workflow.
- **Active Agent**: The agent currently handling the conversation or task, tracked in the shared state.

---

## Core API Functions and Classes

### `SwarmState`

Defined in `langgraph_swarm/swarm.py` (lines 7-15):

```python
class SwarmState(MessagesState):
    """State schema for the multi-agent swarm."""

    # Optional field to track the currently active agent by name.
    active_agent: Optional[str]
```

- Extends `MessagesState` (from LangGraph).
- Contains an optional `active_agent` field to track which agent is currently active.
- The package dynamically updates this field's type to a `Literal` of agent names for type safety.

---

### `create_handoff_tool`

Defined in `langgraph_swarm/handoff.py` (lines 15-56):

```python
def create_handoff_tool(
    *, agent_name: str, name: str | None = None, description: str | None = None
) -> BaseTool:
    """Create a tool that can handoff control to the requested agent."""
    ...
```

- Creates a special tool that, when called, transfers control to another agent in the swarm.
- The tool name defaults to `transfer_to_<agent_name>`.
- The tool returns a `Command` that updates the state to set the `active_agent` to the target agent and appends a tool message indicating the transfer.
- This tool is used inside agents to enable handoff.

---

### `add_active_agent_router`

Defined in `langgraph_swarm/swarm.py` (lines 38-92):

```python
def add_active_agent_router(
    builder: StateGraph,
    *,
    route_to: list[str],
    default_active_agent: str,
) -> StateGraph:
    """Add a router to the currently active agent to the StateGraph."""
    ...
```

- Adds routing logic to the `StateGraph` to route execution based on the `active_agent` field in the state.
- Routes to one of the agents in `route_to` list.
- Uses `default_active_agent` if no active agent is set.
- This router is essential to keep track of which agent should handle the next step.

---

### `create_swarm`

Defined in `langgraph_swarm/swarm.py` (lines 94-153):

```python
def create_swarm(
    agents: list[Pregel],
    *,
    default_active_agent: str,
    state_schema: StateSchemaType = SwarmState,
    config_schema: Type[Any] | None = None,
) -> StateGraph:
    """Create a multi-agent swarm."""
    ...
```

- Takes a list of agents (which can be compiled LangGraph graphs or ReAct agents).
- Sets up the swarm with routing and handoff capabilities.
- Automatically updates the `SwarmState` schema to restrict `active_agent` to the agent names.
- Adds the active agent router.
- Adds each agent as a node in the graph with destinations derived from their handoff tools.
- Returns a `StateGraph` representing the multi-agent swarm.

---

## Step-by-Step Guide to Create a ReAct Agent with Tool Calling

1. **Create individual ReAct agents** using LangGraph's `create_react_agent` function. Each agent should have:
   - A unique `name`.
   - A prompt describing its role.
   - A list of tools it can use, including handoff tools to other agents.

2. **Create handoff tools** for each agent to enable transferring control to other agents:
   ```python
   from langgraph_swarm import create_handoff_tool

   handoff_to_agent_b = create_handoff_tool(agent_name="agent_b")
   handoff_to_agent_a = create_handoff_tool(agent_name="agent_a")
   ```

3. **Add handoff tools to agents' tool lists** so they can call each other:
   ```python
   agent_a = create_react_agent(
       model,
       prompt="You are Agent A",
       tools=[some_tool, handoff_to_agent_b],
       name="agent_a",
   )

   agent_b = create_react_agent(
       model,
       prompt="You are Agent B",
       tools=[some_other_tool, handoff_to_agent_a],
       name="agent_b",
   )
   ```

4. **Create the swarm** by passing the list of agents and specifying the default active agent:
   ```python
   from langgraph_swarm import create_swarm

   swarm = create_swarm([agent_a, agent_b], default_active_agent="agent_a")
   ```

5. **Compile the swarm** to get an executable application:
   ```python
   app = swarm.compile(checkpointer=some_checkpointer)
   ```

6. **Invoke the swarm app** with user messages and configuration:
   ```python
   config = {"configurable": {"thread_id": "1"}}
   response = app.invoke(
       {"messages": [{"role": "user", "content": "Hello, I want to talk to Agent B"}]},
       config,
   )
   ```

7. The swarm will route the request to the active agent, and agents can hand off control to each other by calling the handoff tools.

---

## Example Usage

The following example is adapted from the docstrings and example files:

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent
from langgraph_swarm import create_handoff_tool, create_swarm

def add(a: int, b: int) -> int:
    return a + b

# Create handoff tools
handoff_to_bob = create_handoff_tool(agent_name="Bob")
handoff_to_alice = create_handoff_tool(agent_name="Alice", description="Transfer to Alice, she can help with math")

# Create agents
alice = create_react_agent(
    "openai:gpt-4o",
    [add, handoff_to_bob],
    prompt="You are Alice, an addition expert.",
    name="Alice",
)

bob = create_react_agent(
    "openai:gpt-4o",
    [handoff_to_alice],
    prompt="You are Bob, you speak like a pirate.",
    name="Bob",
)

# Create swarm
checkpointer = InMemorySaver()
swarm = create_swarm([alice, bob], default_active_agent="Alice")

# Compile swarm
app = swarm.compile(checkpointer=checkpointer)

# Invoke swarm
config = {"configurable": {"thread_id": "1"}}
turn_1 = app.invoke(
    {"messages": [{"role": "user", "content": "I'd like to speak to Bob"}]},
    config,
)
turn_2 = app.invoke(
    {"messages": [{"role": "user", "content": "What's 5 + 7?"}]},
    config,
)
```

---

## Additional Notes

- The `active_agent` field in the shared state is critical for routing and is automatically managed by the swarm.
- The handoff tools use metadata to indicate the destination agent, which is used to build the routing graph.
- The package supports optional configuration schemas to expose configurable parameters.
- The example in `examples/research/src/agent/agent.py` demonstrates a more complex use case with a planner and researcher agent using handoff tools.

---

# Summary

To create a ReAct agent with tool calling using `langgraph-swarm-py`:

- Define your agents with `create_react_agent`.
- Create handoff tools with `create_handoff_tool` to enable agent-to-agent transfer.
- Compose agents into a swarm with `create_swarm`.
- Use `add_active_agent_router` internally to route based on the active agent.
- Compile and invoke the swarm app to handle multi-agent conversations with dynamic handoff.

This API design enables flexible multi-agent workflows with clear routing and tool-based handoff, leveraging LangGraph's graph-based state management.

---

If you need further details or code snippets from specific files, please ask!