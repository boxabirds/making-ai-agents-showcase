# Langflow API Usage for Creating a ReAct Agent with Tool Calling

This document provides an exhaustive guide on how to use the Langflow API to create a ReAct agent with tool calling capabilities. The Langflow package integrates with LangChain and provides components to build agents that can utilize tools dynamically during their operation.

---

## Overview

The key class for creating a ReAct agent with tool calling in Langflow is the `ToolCallingAgentComponent`, which extends `LCToolsAgentComponent`. The `AgentComponent` class further extends `ToolCallingAgentComponent` to provide a more complete agent implementation with memory, model provider selection, and tool management.

---

## Key Classes and Their Roles

### 1. `ToolCallingAgentComponent`

- **Location:** `src/backend/base/langflow/components/langchain_utilities/tool_calling.py`
- **Description:** This component is designed to create an agent that can seamlessly utilize various tools within workflows.
- **Inheritance:** Extends `LCToolsAgentComponent`.
- **Key Features:**
  - Accepts a language model (`llm`) input.
  - Accepts a system prompt to guide agent behavior.
  - Supports chat history input for memory.
  - Uses LangChain's `create_tool_calling_agent` to create the underlying agent runnable.
- **Important Methods:**
  - `create_agent_runnable()`: Constructs the LangChain agent runnable using a chat prompt template and the provided tools and language model.
  - `get_chat_history_data()`: Returns the chat history data for the agent.

**Code snippet:**

```python
class ToolCallingAgentComponent(LCToolsAgentComponent):
    display_name: str = "Tool Calling Agent"
    description: str = "An agent designed to utilize various tools seamlessly within workflows."
    icon = "LangChain"
    name = "ToolCallingAgent"

    inputs = [
        *LCToolsAgentComponent._base_inputs,
        HandleInput(
            name="llm",
            display_name="Language Model",
            input_types=["LanguageModel"],
            required=True,
            info="Language model that the agent utilizes to perform tasks effectively.",
        ),
        MessageTextInput(
            name="system_prompt",
            display_name="System Prompt",
            info="System prompt to guide the agent's behavior.",
            value="You are a helpful assistant that can use tools to answer questions and perform tasks.",
        ),
        DataInput(
            name="chat_history",
            display_name="Chat Memory",
            is_list=True,
            advanced=True,
            info="This input stores the chat history, allowing the agent to remember previous conversations.",
        ),
    ]

    def get_chat_history_data(self) -> list[Data] | None:
        return self.chat_history

    def create_agent_runnable(self):
        messages = [
            ("system", "{system_prompt}"),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
        prompt = ChatPromptTemplate.from_messages(messages)
        self.validate_tool_names()
        try:
            return create_tool_calling_agent(self.llm, self.tools or [], prompt)
        except NotImplementedError as e:
            message = f"{self.display_name} does not support tool calling. Please try using a compatible model."
            raise NotImplementedError(message) from e
```

---

### 2. `LCToolsAgentComponent`

- **Location:** `src/backend/base/langflow/base/agents/agent.py`
- **Description:** Base class for agents that use tools. Provides inputs for tools and language model, and methods to build and run the agent.
- **Key Methods:**
  - `build_agent()`: Validates tool names and creates an `AgentExecutor` from the agent runnable and tools.
  - `create_agent_runnable()`: Abstract method to be implemented by subclasses to create the actual agent runnable.
  - `run_agent()`: Runs the agent with the given input and returns the response message.
  - `validate_tool_names()`: Ensures tool names conform to allowed patterns.

---

### 3. `AgentComponent`

- **Location:** `src/backend/base/langflow/components/agents/agent.py`
- **Description:** A concrete implementation of `ToolCallingAgentComponent` that adds:
  - Model provider selection (e.g., OpenAI, Custom).
  - Memory integration for chat history.
  - Option to add a current date tool.
  - Tool validation and setup.
- **Inputs:**
  - Model provider dropdown.
  - System prompt for agent instructions.
  - Tools list.
  - Memory inputs.
  - Boolean to add current date tool.
- **Outputs:**
  - Response message from the agent.
- **Key Methods:**
  - `message_response()`: Main async method to run the agent and get the response.
  - `get_memory_data()`: Retrieves chat history from memory component.
  - `get_llm()`: Builds the language model based on selected provider.
  - `_get_tools()`: Retrieves the list of tools available to the agent.
  - `update_build_config()`: Updates the build configuration dynamically based on model provider changes.

**Usage flow in `message_response`:**

1. Get and validate the language model.
2. Retrieve chat history from memory.
3. Optionally add a current date tool.
4. Validate that tools are present.
5. Set internal state with LLM, tools, chat history, input, and system prompt.
6. Create the agent runnable.
7. Run the agent and return the response.

---

## How to Use the API to Create a ReAct Agent with Tool Calling

### Step 1: Instantiate the `AgentComponent`

This component is the recommended entry point for creating a ReAct agent with tool calling.

```python
agent_component = AgentComponent()
```

### Step 2: Configure Inputs

- **Select a language model provider** (e.g., "OpenAI").
- **Set the system prompt** to guide the agent's behavior.
- **Add tools** that the agent can use (must be instances of `Tool`).
- **Optionally configure memory** inputs for chat history.
- **Optionally enable the current date tool**.

Example:

```python
agent_component.agent_llm = "OpenAI"
agent_component.system_prompt = "You are a helpful assistant that can use tools to answer questions and perform tasks."
agent_component.tools = [tool1, tool2]  # List of Tool instances
agent_component.add_current_date_tool = True
```

### Step 3: Provide User Input

Set the input value that the agent will process:

```python
agent_component.input_value = "What is the weather like today?"
```

### Step 4: Run the Agent

Call the async method `message_response()` to run the agent and get the response message:

```python
import asyncio

response_message = asyncio.run(agent_component.message_response())
print(response_message.content)
```

---

## Important Notes

- The agent uses LangChain's `create_tool_calling_agent` internally to support tool calling.
- Tools must have valid names (alphanumeric, underscores, dashes, no spaces).
- The system prompt and chat history are used to build the chat prompt template for the agent.
- The agent supports asynchronous execution and event streaming.
- The `AgentComponent` supports dynamic model provider configuration and memory integration.
- If the selected language model does not support tool calling, a `NotImplementedError` is raised with a helpful message.

---

## Summary

| Step | Action | Class/Method |
|-------|--------|--------------|
| 1 | Instantiate agent | `AgentComponent()` |
| 2 | Configure language model, tools, system prompt, memory | Set properties on `AgentComponent` |
| 3 | Provide user input | Set `input_value` on `AgentComponent` |
| 4 | Run agent and get response | `await AgentComponent.message_response()` |
| 5 | Internally creates runnable agent | `ToolCallingAgentComponent.create_agent_runnable()` |
| 6 | Uses LangChain's tool calling agent | `create_tool_calling_agent()` |

---

This detailed guide should enable you to effectively use the Langflow API to create and run a ReAct agent with tool calling capabilities. The `AgentComponent` class is the main interface, leveraging the underlying LangChain integration and Langflow's component system for tools, memory, and language models.