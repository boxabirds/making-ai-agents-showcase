```markdown
# CAMEL AI Package: How to Use the API to Create and Run a Python Agent with ReAct and Tool Calling

This document provides an exhaustive guide on how to use the CAMEL AI package API to create an agent that can be run directly in Python (e.g., `python agent.py`), specifically focusing on creating a Python ReAct agent with tool calling capabilities. It includes detailed references to source code files and examples within the package.

---

## 1. Creating and Running a Basic Agent in Python

### Key File Reference: `examples/agents/single_agent.py`

This example demonstrates the simplest way to create and run a CAMEL AI agent in Python.

```python
from camel.agents import ChatAgent
from camel.prompts import PromptTemplateGenerator
from camel.types import TaskType

def main(key: str = 'generate_users', num_roles: int = 50, model=None):
    prompt_template = PromptTemplateGenerator().get_prompt_from_key(
        TaskType.AI_SOCIETY, key
    )
    prompt = prompt_template.format(num_roles=num_roles)
    print(prompt)
    agent = ChatAgent("You are a helpful assistant.", model=model)
    agent.reset()

    assistant_response = agent.step(prompt)
    print(assistant_response.msg.content)

if __name__ == "__main__":
    main()
```

- **How it works:**
  - Uses `ChatAgent` from `camel.agents` as the core agent class.
  - Uses a prompt template from `PromptTemplateGenerator` keyed by a task type.
  - Calls `agent.step()` to send the prompt and get a response.
  - Prints the response content.

- **To run:** Save as `agent.py` and run `python agent.py`.

---

## 2. Creating a Python ReAct Agent with Tool Calling

### Core Agent Class: `camel.agents.chat_agent.ChatAgent`

- The `ChatAgent` class is the main agent implementation supporting conversation, tool calling, memory, and model management.
- Located at: `camel/camel/agents/chat_agent.py`

### Key Features for ReAct and Tool Calling:

- **Tools Support:**
  - Internal tools: Python callables wrapped as `FunctionTool` instances.
  - External tools: Tools represented by schemas that the agent can request but not execute internally.
  - Tools are passed as a list to the `ChatAgent` constructor via the `tools` parameter.
  
- **Tool Calling Flow:**
  - When the agent generates a response, it may include tool call requests.
  - The agent executes internal tools automatically and records the results.
  - External tool calls are returned as requests for external handling.
  
- **Memory and Context:**
  - Uses `AgentMemory` (default `ChatHistoryMemory`) to store conversation history.
  - Supports token limits and message windowing.

- **Model Management:**
  - Supports single or multiple models via `ModelManager`.
  - Models are created via `ModelFactory` with platform and type specifications.

### Example Usage to Create a ReAct Agent with Tool Calling

```python
from camel.agents import ChatAgent
from camel.models import ModelFactory
from camel.toolkits import MCPToolkit  # Example toolkit with tools
from camel.types import ModelPlatformType, ModelType

def main():
    # Create a language model backend
    model = ModelFactory.create(
        model_platform=ModelPlatformType.DEFAULT,
        model_type=ModelType.DEFAULT,
    )

    # Initialize toolkit with tools (e.g., MCPToolkit for file system operations)
    mcp_toolkit = MCPToolkit(config_path="path/to/mcp_servers_config.json")
    tools = list(mcp_toolkit.get_tools())

    # Create the ChatAgent with system message, model, and tools
    agent = ChatAgent(
        system_message="You are a helpful assistant with tool calling capabilities.",
        model=model,
        tools=tools,
    )

    # Reset agent state
    agent.reset()

    # Example user input that may trigger tool calls
    user_input = "List 5 files in the current project directory."

    # Run a single step (sync or async)
    response = agent.step(user_input)

    # Print the agent's response content
    print(response.msgs[0].content)

if __name__ == "__main__":
    main()
```

- This example uses the `MCPToolkit` (see `examples/toolkits/mcp/mcp_toolkit.py`) which provides tools for file system operations.
- The agent automatically handles tool calls internally for tools it owns.
- External tool calls (if any) are returned for external processing.

---

## 3. Using MCPToolkit for Tool Calling (Example Toolkit)

### File Reference: `examples/toolkits/mcp/mcp_toolkit.py`

- Demonstrates how to connect to MCP servers and expose their tools to the agent.
- Shows both async and sync usage examples.
- Example snippet from the file:

```python
from camel.agents import ChatAgent
from camel.models import ModelFactory
from camel.toolkits import MCPToolkit
from camel.types import ModelPlatformType, ModelType

async def mcp_toolkit_example():
    async with MCPToolkit(config_path="mcp_servers_config.json") as mcp_toolkit:
        sys_msg = "You are a helpful assistant"
        model = ModelFactory.create(
            model_platform=ModelPlatformType.DEFAULT,
            model_type=ModelType.DEFAULT,
        )
        camel_agent = ChatAgent(
            system_message=sys_msg,
            model=model,
            tools=[*mcp_toolkit.get_tools()],
        )
        user_msg = "List 5 files in the project, using relative paths"
        response = await camel_agent.astep(user_msg)
        print(response.msgs[0].content)
        print(response.info['tool_calls'])
```

- This example shows how to instantiate the agent with tools from MCPToolkit and run an async step.
- The agent will call the appropriate tools based on the model's function call requests.

---

## 4. Grounding and References

- **Agent Core:** `camel/camel/agents/chat_agent.py`
  - Implements `ChatAgent` with tool calling, memory, model management, and response formatting.
  - Supports sync (`step()`) and async (`astep()`) interaction.
  - Tool execution methods: `_execute_tool()`, `_aexecute_tool()`.
  - Tool management: `add_tool()`, `remove_tool()`, `add_external_tool()`.
  - MCP server exposure via `to_mcp()` method.

- **Function Tool Abstraction:** `camel/camel/toolkits/function_tool.py`
  - `FunctionTool` wraps Python functions for OpenAI-compatible function calling.
  - Generates OpenAI JSON schemas from Python function signatures and docstrings.
  - Supports synchronous and asynchronous function calls.
  - Supports schema synthesis and output synthesis using LLMs.

- **Model Factory and Manager:**
  - `camel/camel/models/model_factory.py` (not fully shown here) creates model backends.
  - `ModelManager` manages multiple models and scheduling strategies.

- **Example Agents:**
  - `examples/agents/single_agent.py` - Basic agent usage.
  - `examples/agents/agent_step_with_reasoning.py` - Shows advanced reasoning with multiple choices.
  - `examples/toolkits/mcp/mcp_toolkit.py` - Shows toolkits integration and tool calling.

- **Documentation:**
  - The package includes docstrings with detailed explanations.
  - OpenAI function calling schema references: https://platform.openai.com/docs/api-reference/chat/create

---

## 5. Summary: How to Create and Run a Python ReAct Agent with Tool Calling

1. **Install CAMEL AI package and dependencies.**

2. **Create or import a language model backend:**

```python
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType

model = ModelFactory.create(
    model_platform=ModelPlatformType.DEFAULT,
    model_type=ModelType.DEFAULT,
)
```

3. **Prepare tools for the agent:**

- Use existing toolkits like `MCPToolkit` or create your own tools wrapped as `FunctionTool`.
- Example:

```python
from camel.toolkits import MCPToolkit

mcp_toolkit = MCPToolkit(config_path="path/to/mcp_servers_config.json")
tools = list(mcp_toolkit.get_tools())
```

4. **Create the ChatAgent with system message, model, and tools:**

```python
from camel.agents import ChatAgent

agent = ChatAgent(
    system_message="You are a helpful assistant with tool calling.",
    model=model,
    tools=tools,
)
agent.reset()
```

5. **Run the agent synchronously or asynchronously:**

```python
# Sync
response = agent.step("Your question or command here")
print(response.msgs[0].content)

# Async
response = await agent.astep("Your question or command here")
print(response.msgs[0].content)
```

6. **Handle external tool calls if any are returned in the response.**

---

## 6. Additional Notes

- The `ChatAgent` class supports advanced features like memory management, output language setting, response terminators, and model scheduling strategies.
- The `FunctionTool` class in `camel.toolkits.function_tool` is the recommended way to wrap Python functions for tool calling with OpenAI-compatible schemas.
- The package supports exposing agents as MCP servers for remote interaction (`ChatAgent.to_mcp()`).
- Extensive examples are provided in the `examples/` directory for various use cases.

---

# References to Source Code and Examples

| Topic | File Path | Description |
|-------|-----------|-------------|
| Basic agent example | `examples/agents/single_agent.py` | Minimal example to create and run a ChatAgent |
| ChatAgent implementation | `camel/camel/agents/chat_agent.py` | Core agent class with tool calling and memory |
| FunctionTool abstraction | `camel/camel/toolkits/function_tool.py` | Wrap Python functions for OpenAI function calling |
| MCPToolkit example | `examples/toolkits/mcp/mcp_toolkit.py` | Example toolkit and agent usage with MCP tools |
| Agent with reasoning example | `examples/agents/agent_step_with_reasoning.py` | Shows advanced agent reasoning with multiple choices |

---

This guide should enable you to create, run, and extend CAMEL AI agents in Python with ReAct-style tool calling, leveraging the package's built-in tools and models efficiently.

If you want me to generate a ready-to-run example script file (`agent.py`) based on this, please let me know.
```
