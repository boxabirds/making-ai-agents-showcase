# Comprehensive Guide to Using the Autogen Core API to Create a Python ReAct Agent with Tool Calling

This document provides an exhaustive, detailed guide on how to use the Autogen Core API (from the `autogen-core` package) to create an agent that can be run directly in Python (e.g., `python agent.py`). It specifically addresses how to create a Python ReAct (Reasoning and Acting) agent with tool calling capabilities. The guide includes extensive grounding with references to source code files and relevant code snippets.

---

## Table of Contents

1. [Overview of the Autogen Core API](#overview-of-the-autogen-core-api)
2. [Key Components for Creating an Agent](#key-components-for-creating-an-agent)
3. [Creating a Tool Agent](#creating-a-tool-agent)
4. [Using the Tool Agent Caller Loop](#using-the-tool-agent-caller-loop)
5. [Creating Custom Tools with FunctionTool](#creating-custom-tools-with-functiontool)
6. [Example: Creating and Running a Tool Agent](#example-creating-and-running-a-tool-agent)
7. [How to Create a Python ReAct Agent with Tool Calling](#how-to-create-a-python-react-agent-with-tool-calling)
8. [References and Further Reading](#references-and-further-reading)

---

## Overview of the Autogen Core API

The Autogen Core API provides a framework for building intelligent agents that can handle messages, route them to appropriate handlers, and interact with tools. The core concepts include:

- **Agents**: Autonomous entities that process messages.
- **RoutedAgent**: A base class for agents that route messages to handlers based on message types.
- **Tools**: Components that encapsulate functionality callable by agents.
- **ToolAgent**: A specialized agent that executes tools based on function call messages.
- **FunctionTool**: A wrapper around Python functions to expose them as callable tools.
- **Tool Agent Caller Loop**: A helper function to run a loop where the agent and model client interact, enabling tool calling.

---

## Key Components for Creating an Agent

### 1. RoutedAgent

- **File:** `src/autogen_core/_routed_agent.py`
- **Description:** Base class for agents that route messages to handlers decorated with `@event` or `@rpc`.
- **Usage:** Subclass `RoutedAgent` to create custom agents with message handlers.
- **Key Decorators:**
  - `@event`: For event message handlers.
  - `@rpc`: For RPC message handlers (e.g., function calls).
- **Example snippet:**

```python
from autogen_core import RoutedAgent, event, rpc, MessageContext

class MyAgent(RoutedAgent):
    def __init__(self):
        super().__init__("MyAgent")

    @event
    async def handle_event(self, message: SomeEventType, ctx: MessageContext) -> None:
        # handle event
        pass

    @rpc
    async def handle_rpc(self, message: SomeRPCType, ctx: MessageContext) -> SomeResponseType:
        # handle rpc
        return SomeResponseType()
```

---

## Creating a Tool Agent

### ToolAgent Class

- **File:** `src/autogen_core/tool_agent/_tool_agent.py`
- **Description:** An agent that accepts `FunctionCall` messages, executes the requested tool with provided arguments, and returns `FunctionExecutionResult`.
- **Constructor Arguments:**
  - `description` (str): Description of the agent.
  - `tools` (List[Tool]): List of tools the agent can execute.
- **Message Handler:**
  - `handle_function_call`: Handles `FunctionCall` messages asynchronously.
- **Exception Handling:**
  - Raises `ToolNotFoundException` if tool not found.
  - Raises `InvalidToolArgumentsException` if arguments are invalid.
  - Raises `ToolExecutionException` if tool execution fails.

**Key snippet from `ToolAgent`:**

```python
@message_handler
async def handle_function_call(self, message: FunctionCall, ctx: MessageContext) -> FunctionExecutionResult:
    tool = next((tool for tool in self._tools if tool.name == message.name), None)
    if tool is None:
        raise ToolNotFoundException(...)
    try:
        arguments = json.loads(message.arguments)
        result = await tool.run_json(args=arguments, cancellation_token=ctx.cancellation_token)
        result_as_str = tool.return_value_as_string(result)
    except json.JSONDecodeError as e:
        raise InvalidToolArgumentsException(...)
    except Exception as e:
        raise ToolExecutionException(...)
    return FunctionExecutionResult(content=result_as_str, call_id=message.id, is_error=False, name=message.name)
```

---

## Using the Tool Agent Caller Loop

- **File:** `src/autogen_core/tool_agent/_caller_loop.py`
- **Function:** `tool_agent_caller_loop`
- **Purpose:** Runs a loop where the model client and tool agent interact, sending messages and executing tool calls until no more tool calls are generated.
- **Arguments:**
  - `caller`: The agent or runtime sending messages.
  - `tool_agent_id`: The ID of the tool agent.
  - `model_client`: The chat completion client (LLM interface).
  - `input_messages`: Initial input messages to the model.
  - `tool_schema`: List of tools or tool schemas available.
  - `cancellation_token`: Optional cancellation token.
- **Returns:** List of generated LLM messages.

**Key snippet:**

```python
async def tool_agent_caller_loop(
    caller, tool_agent_id, model_client, input_messages, tool_schema, cancellation_token=None, caller_source="assistant"
) -> List[LLMMessage]:
    generated_messages = []
    response = await model_client.create(input_messages, tools=tool_schema, cancellation_token=cancellation_token)
    generated_messages.append(AssistantMessage(content=response.content, source=caller_source))

    while isinstance(response.content, list) and all(isinstance(item, FunctionCall) for item in response.content):
        results = await asyncio.gather(
            *[caller.send_message(message=call, recipient=tool_agent_id, cancellation_token=cancellation_token) for call in response.content],
            return_exceptions=True,
        )
        function_results = []
        for result in results:
            if isinstance(result, FunctionExecutionResult):
                function_results.append(result)
            elif isinstance(result, ToolException):
                function_results.append(FunctionExecutionResult(content=f"Error: {result}", call_id=result.call_id, is_error=True, name=result.name))
            elif isinstance(result, BaseException):
                raise result
        generated_messages.append(FunctionExecutionResultMessage(content=function_results))
        response = await model_client.create(input_messages + generated_messages, tools=tool_schema, cancellation_token=cancellation_token)
        generated_messages.append(AssistantMessage(content=response.content, source=caller_source))

    return generated_messages
```

---

## Creating Custom Tools with FunctionTool

- **File:** `src/autogen_core/tools/_function_tool.py`
- **Class:** `FunctionTool`
- **Description:** Wraps standard Python functions as tools with type annotations for input validation and schema generation.
- **Constructor Arguments:**
  - `func`: The Python function to wrap.
  - `description`: Description of the tool.
  - `name`: Optional custom name (defaults to function name).
  - `global_imports`: Optional imports needed by the function.
  - `strict`: If True, enforces strict schema (required for structured output models).
- **Run Method:** Executes the wrapped function asynchronously or synchronously with cancellation support.
- **Example usage:**

```python
import asyncio
from autogen_core.tools import FunctionTool
from autogen_core import CancellationToken

async def get_stock_price(ticker: str, date: str) -> float:
    # Simulate fetching stock price
    return 123.45

async def main():
    stock_tool = FunctionTool(get_stock_price, description="Get stock price for a ticker")
    cancellation_token = CancellationToken()
    result = await stock_tool.run_json({"ticker": "AAPL", "date": "2023-01-01"}, cancellation_token)
    print(stock_tool.return_value_as_string(result))

asyncio.run(main())
```

---

## Example: Creating and Running a Tool Agent

The test file `test_tool_agent.py` in `packages/autogen-core/tests` provides a practical example of creating a tool agent with multiple tools and running it.

- **File:** `packages/autogen-core/tests/test_tool_agent.py`
- **Highlights:**
  - Defines simple synchronous and asynchronous functions wrapped as `FunctionTool`.
  - Registers a `ToolAgent` with these tools in a `SingleThreadedAgentRuntime`.
  - Sends `FunctionCall` messages to the agent and asserts expected results.
  - Demonstrates error handling for invalid tool names and arguments.
  - Shows cancellation of long-running tool calls.

**Excerpt from test setup:**

```python
from autogen_core.tool_agent import ToolAgent
from autogen_core.tools import FunctionTool
from autogen_core import SingleThreadedAgentRuntime, FunctionCall
import json

def _pass_function(input: str) -> str:
    return "pass"

def _raise_function(input: str) -> str:
    raise Exception("raise")

async def _async_sleep_function(input: str) -> str:
    await asyncio.sleep(10)
    return "pass"

runtime = SingleThreadedAgentRuntime()
await ToolAgent.register(
    runtime,
    "tool_agent",
    lambda: ToolAgent(
        description="Tool agent",
        tools=[
            FunctionTool(_pass_function, name="pass", description="Pass function"),
            FunctionTool(_raise_function, name="raise", description="Raise function"),
            FunctionTool(_async_sleep_function, name="sleep", description="Sleep function"),
        ],
    ),
)
agent_id = AgentId("tool_agent", "default")
runtime.start()

result = await runtime.send_message(
    FunctionCall(id="1", arguments=json.dumps({"input": "pass"}), name="pass"), agent_id
)
print(result)  # Should print FunctionExecutionResult with content "pass"
```

---

## How to Create a Python ReAct Agent with Tool Calling

To create a Python ReAct agent that uses tool calling with the Autogen Core API, follow these steps:

### Step 1: Define Your Tools

Wrap your Python functions as `FunctionTool` instances. These tools represent the actions your agent can perform.

```python
from autogen_core.tools import FunctionTool

async def search_web(query: str) -> str:
    # Implement your search logic here
    return "Search results for " + query

search_tool = FunctionTool(search_web, description="Search the web for a query")
```

### Step 2: Create a ToolAgent

Create a `ToolAgent` instance with a description and a list of your tools.

```python
from autogen_core.tool_agent import ToolAgent

tool_agent = ToolAgent(description="My ReAct Tool Agent", tools=[search_tool])
```

### Step 3: Register the ToolAgent with a Runtime

Use a runtime such as `SingleThreadedAgentRuntime` to register and run your agent.

```python
from autogen_core import SingleThreadedAgentRuntime

runtime = SingleThreadedAgentRuntime()
await ToolAgent.register(runtime, "my_tool_agent", lambda: tool_agent)
runtime.start()
```

### Step 4: Use a Model Client and Run the Caller Loop

Use a chat completion client (LLM interface) that supports function calling. Then use `tool_agent_caller_loop` to run the interaction loop.

```python
from autogen_core.tool_agent import tool_agent_caller_loop
from autogen_core.models import UserMessage

input_messages = [UserMessage(content="Find the latest news about AI", source="user")]
tool_schema = [search_tool]

messages = await tool_agent_caller_loop(
    caller=runtime,
    tool_agent_id=AgentId("my_tool_agent", "default"),
    model_client=my_chat_completion_client,
    input_messages=input_messages,
    tool_schema=tool_schema,
)
```

### Step 5: Run Your Agent Script

Put the above code in a Python script (e.g., `agent.py`) and run it directly:

```bash
python agent.py
```

---

## References and Further Reading

- **ToolAgent Implementation:**  
  `src/autogen_core/tool_agent/_tool_agent.py` (lines 10-70)  
  Handles function call messages and executes tools.

- **Tool Agent Caller Loop:**  
  `src/autogen_core/tool_agent/_caller_loop.py` (lines 10-70)  
  Implements the interaction loop between the model and tool agent.

- **FunctionTool for Wrapping Python Functions:**  
  `src/autogen_core/tools/_function_tool.py` (lines 10-180)  
  Wraps Python functions as tools with schema and execution support.

- **RoutedAgent Base Class and Decorators:**  
  `src/autogen_core/_routed_agent.py` (lines 10-300)  
  Provides decorators `@event` and `@rpc` for message routing.

- **Test Example for ToolAgent:**  
  `packages/autogen-core/tests/test_tool_agent.py` (lines 10-150)  
  Demonstrates creating and testing a tool agent with function tools.

- **Autogen Core Package Init:**  
  `src/autogen_core/__init__.py`  
  Shows the main exports and components of the package.

---

This guide should enable you to create a Python ReAct agent with tool calling using the Autogen Core API efficiently, leveraging the provided scaffolding and tools for rapid development.