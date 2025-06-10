# Comprehensive Guide to Using the AG2 API to Create a Python ReAct Agent with Tool Calling

This document provides an exhaustive, detailed guide on how to use the AG2 API (from the package located at `output/cache/ag2ai/ag2`) to create an agent that can be run directly in Python (e.g., `python agent.py`). It specifically addresses how to create a Python ReAct agent with tool calling capabilities, leveraging the provided scaffold tools and APIs.

---

## Table of Contents

1. [Overview of the AG2 API and Key Components](#overview)
2. [Creating an Agent That Can Run Directly in Python](#create-agent)
3. [Creating a Python ReAct Agent with Tool Calling](#react-agent-tool-calling)
4. [Using Scaffold Tools: AgentBuilder and CaptainAgent](#scaffold-tools)
5. [Code Examples and Usage Patterns](#code-examples)
6. [References to Source Code and Documentation](#references)

---

<a name="overview"></a>
## 1. Overview of the AG2 API and Key Components

The AG2 API provides a modular framework for building conversational AI agents, including multi-agent systems, user proxy agents, and tools integration. The key components relevant to building a ReAct agent with tool calling are:

- **ConversableAgent**: Base class for agents that can converse.
- **AssistantAgent**: A typical AI assistant agent.
- **UserProxyAgent**: Acts as a proxy for user input or code execution.
- **AgentBuilder**: A scaffold tool to automatically build multi-agent systems based on a task.
- **CaptainAgent**: A high-level agent that manages a group of experts (agents) and can orchestrate tool usage.
- **ToolBuilder**: Helps retrieve and bind tools to agents, enabling tool calling.
- **CodeExecutor**: Executes code blocks, supporting tool integration.

---

<a name="create-agent"></a>
## 2. Creating an Agent That Can Run Directly in Python

To create an agent that can be run directly in Python (e.g., `python agent.py`), you typically:

1. Import the necessary classes from the AG2 package.
2. Configure the LLM (language model) settings.
3. Instantiate an agent (e.g., `AssistantAgent` or `CaptainAgent`).
4. Optionally add tools or user proxy agents.
5. Run the agent's chat or task loop.

### Minimal Example (from `test_agent_usage.py`):

```python
from autogen import AssistantAgent, UserProxyAgent

# Configure your LLM credentials/config (example placeholder)
llm_config = {
    "config_list": [
        # Your LLM config here
    ]
}

# Create an assistant agent
assistant = AssistantAgent(
    "assistant",
    system_message="You are a helpful assistant.",
    llm_config=llm_config,
)

# Create a user proxy agent (e.g., for code execution)
user_proxy = UserProxyAgent(
    name="ai_user",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=1,
    code_execution_config=False,
    llm_config=llm_config,
    system_message="You ask a user for help. You check the answer from the user and provide feedback.",
)

# Example interaction
math_problem = "$x^3=125$. What is x?"
response = user_proxy.initiate_chat(
    assistant,
    message=math_problem,
    summary_method="reflection_with_llm",
)
print("Result summary:", response.summary)
```

Run this script with `python agent.py` after saving it.

---

<a name="react-agent-tool-calling"></a>
## 3. Creating a Python ReAct Agent with Tool Calling

ReAct (Reasoning + Acting) agents combine reasoning with the ability to call external tools or functions during their operation.

### Key Steps:

- Use **CaptainAgent** as the orchestrator agent that can manage multiple expert agents.
- Use **ToolBuilder** to retrieve and bind tools to agents, enabling tool calling.
- Use **UserProxyAgent** with a code executor that supports tool execution.
- Configure the nested chat system where the CaptainAgent manages a group chat of agents.

### CaptainAgent Highlights (from `captainagent.py`):

- `CaptainAgent` is a subclass of `ConversableAgent` designed to solve tasks by building and managing a group of expert agents.
- It has a built-in tool called `"seek_experts_help"` which builds a group of experts and lets them chat to solve a task.
- It supports tool libraries and retrieval to bind relevant tools to agents.
- It uses nested chats and group chat managers to coordinate multi-agent conversations.

### ToolBuilder Highlights (from `tool_retriever.py`):

- `ToolBuilder` loads tool descriptions and uses semantic search (via Sentence Transformers) to retrieve relevant tools based on skills or task descriptions.
- It can bind tool function signatures to agents' system messages, enabling the agent to call these tools.
- It supports binding tools to `UserProxyAgent` with a specialized code executor (`LocalExecutorWithTools`) that injects tools into the execution environment.

### Code Executor with Tools:

- `LocalExecutorWithTools` executes Python code blocks with injected tools, allowing direct function calls to tools without explicit imports.
- This is essential for ReAct style tool calling.

---

<a name="scaffold-tools"></a>
## 4. Using Scaffold Tools: AgentBuilder and CaptainAgent

### AgentBuilder (`agent_builder.py`)

- Helps automatically build a multi-agent system based on a task description.
- Uses a builder LLM model to generate expert agent names, system messages, and descriptions.
- Supports building agents from a library or from scratch.
- Manages agent lifecycle, including creation, clearing, saving, and loading configurations.
- Supports adding a user proxy agent for code execution automatically if coding is required.

**Usage:**

```python
from autogen.agentchat.contrib.captainagent import AgentBuilder

builder = AgentBuilder(
    config_file_or_env="OAI_CONFIG_LIST",
    builder_model="gpt-4o",
    agent_model="gpt-4o",
    max_agents=3,
)

agents, cached_configs = builder.build(
    building_task="Solve a math problem using Python and reasoning.",
    default_llm_config={"temperature": 0.7, "max_tokens": 1024},
    coding=True,
)
```

### CaptainAgent (`captainagent.py`)

- High-level agent that manages a group of experts and tool usage.
- Automatically builds nested chats and manages conversation flow.
- Supports loading tool libraries and binding tools to agents.
- Provides a proxy agent (`CaptainUserProxyAgent`) that executes code and provides feedback.
- Designed for ReAct style multi-agent collaboration with tool calling.

**Usage:**

```python
from autogen.agentchat.contrib.captainagent import CaptainAgent

captain = CaptainAgent(
    name="CaptainAgent",
    llm_config={"config_list": [...]},
    agent_lib="path/to/agent_library.json",
    tool_lib="path/to/tool_library",
)

# Use the seek_experts_help tool to build and run a group chat solving a task
response = captain.call_function(
    "seek_experts_help",
    group_name="expert_group_1",
    building_task="Build a group of experts for math and coding.",
    execution_task="Solve the integral of x^2.",
)
print(response)
```

---

<a name="code-examples"></a>
## 5. Code Examples and Usage Patterns

### Example: Creating a Python ReAct Agent with Tool Calling

```python
from autogen.agentchat.contrib.captainagent import CaptainAgent

def main():
    # Initialize the CaptainAgent with default or custom LLM config
    captain = CaptainAgent(
        name="CaptainAgent",
        llm_config={
            "config_list": [
                # Your LLM config here
            ],
            "temperature": 0.7,
            "max_tokens": 2048,
        },
        agent_lib="path/to/agent_library.json",  # Optional: agent library JSON or path
        tool_lib="path/to/tool_library",         # Optional: tool library directory or list
    )

    # Define the building task and execution task
    building_task = """
    - Math_Expert: Expert in advanced mathematics and symbolic computation.
    - Python_Expert: Skilled in Python programming and code execution.
    - Verifier: Expert in verifying correctness of solutions.
    """

    execution_task = "Calculate the derivative of sin(x^2) and provide Python code to verify."

    # Call the tool to build experts and solve the task
    response = captain.call_function(
        "seek_experts_help",
        group_name="math_coding_group",
        building_task=building_task,
        execution_task=execution_task,
    )

    print("Response from CaptainAgent:")
    print(response)

if __name__ == "__main__":
    main()
```

### Running the Agent

Save the above code as `agent.py` and run:

```bash
python agent.py
```

This will instantiate the CaptainAgent, build a group of expert agents, bind relevant tools, and run the multi-agent conversation to solve the task with tool calling.

---

<a name="references"></a>
## 6. References to Source Code and Documentation

- **AgentBuilder**: `autogen/agentchat/contrib/captainagent/agent_builder.py`  
  - Core class to build multi-agent systems automatically.  
  - Methods: `build()`, `build_from_library()`, `_create_agent()`, `clear_agent()`, `load()`, `save()`.  
  - See lines ~20-400 for full implementation.

- **CaptainAgent**: `autogen/agentchat/contrib/captainagent/captainagent.py`  
  - High-level orchestrator agent with tool calling.  
  - Implements `seek_experts_help` tool for multi-agent collaboration.  
  - See lines ~20-400 for full implementation.

- **ToolBuilder**: `autogen/agentchat/contrib/captainagent/tool_retriever.py`  
  - Retrieves and binds tools to agents.  
  - Supports semantic search with Sentence Transformers.  
  - Implements `bind()`, `bind_user_proxy()`, and `LocalExecutorWithTools` for tool-enabled code execution.

- **Test Example**: `test/agentchat/test_agent_usage.py`  
  - Shows usage of `AssistantAgent` and `UserProxyAgent`.  
  - Demonstrates how to initiate chat and print usage summaries.

- **Documentation URLs**:  
  - [OpenAIWrapper.create API](https://docs.ag2.ai/latest/docs/api-reference/autogen/OpenAIWrapper/#autogen.OpenAIWrapper.create) (referenced in code comments)  
  - [CaptainAgent User Guide](https://docs.ag2.ai/latest/docs/user-guide/reference-agents/captainagent) (mentioned in code comments)

---

# Summary

- To create a Python ReAct agent with tool calling using this package, the recommended approach is to use the **CaptainAgent** class combined with the **AgentBuilder** and **ToolBuilder** scaffold tools.
- The CaptainAgent manages a group of expert agents and can dynamically build and bind tools for execution.
- The UserProxyAgent with a specialized code executor enables running code blocks that call tools directly.
- The package provides extensive support for multi-agent collaboration, tool retrieval, and code execution, making it straightforward to build complex ReAct agents.
- The provided test files and source code offer practical examples and detailed implementations to guide usage.

---

If you want, I can help generate a ready-to-run example script (`agent.py`) based on this analysis. Would you like me to do that?