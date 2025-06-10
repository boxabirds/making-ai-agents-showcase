```markdown
# Comprehensive Guide to Using the BeeAI Framework API to Create Python Agents

This document provides an exhaustive, detailed guide on how to use the BeeAI Framework API to create and run agents directly in Python, with a focus on creating a Python ReAct agent with tool calling capabilities. It includes references to source code files and examples within the package to ground the explanations.

---

## 1. Creating and Running a Tool Calling Agent in Python

### Overview

The BeeAI Framework provides a `ToolCallingAgent` class designed to create agents that can call external tools during their reasoning process. This agent can be run directly in Python, for example via a script like `agent.py`.

### Key Example: `examples/agents/tool_calling.py`

- This example script demonstrates how to instantiate and run a `ToolCallingAgent` with a chat model, memory, and tools.
- It uses asynchronous programming (`asyncio`) to run the agent in an interactive loop.
- It includes event handling to process and log agent events such as start and success.

#### Example snippet from `tool_calling.py`:

```python
from beeai_framework.agents.tool_calling import ToolCallingAgent
from beeai_framework.backend import ChatModel
from beeai_framework.memory import UnconstrainedMemory
from beeai_framework.tools.weather import OpenMeteoTool
from examples.helpers.io import ConsoleReader

async def main():
    agent = ToolCallingAgent(
        llm=ChatModel.from_name("ollama:llama3.1"),
        memory=UnconstrainedMemory(),
        tools=[OpenMeteoTool()]
    )

    reader = ConsoleReader()
    for prompt in reader:
        response = await agent.run(prompt).on("*", process_agent_events)
        reader.write("Agent 🤖 : ", response.result.text)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

- The agent is created with:
  - A chat model (`ChatModel.from_name`).
  - An unconstrained memory instance.
  - A list of tools (e.g., `OpenMeteoTool` for weather).
- The agent's `run` method is called with user input prompts.
- Events are handled via `.on("*", process_agent_events)` to log or react to agent lifecycle events.

---

## 2. Creating a Python ReAct Agent with Tool Calling

### What is a ReAct Agent?

- ReAct (Reasoning + Acting) agents combine reasoning steps with actions (tool calls).
- The BeeAI Framework provides a `ReActAgent` class for this purpose.

### Key Example: `examples/agents/react.py`

- This example shows how to create a ReAct agent with multiple tools and memory.
- It supports advanced tools like Wikipedia search, DuckDuckGo search, weather, and optionally a code interpreter.
- It uses `ChatModel` with parameters and asynchronous event-driven interaction.

#### Example snippet from `react.py`:

```python
from beeai_framework.agents.react import ReActAgent
from beeai_framework.backend import ChatModel, ChatModelParameters
from beeai_framework.memory import TokenMemory
from beeai_framework.tools.search.duckduckgo import DuckDuckGoSearchTool
from beeai_framework.tools.search.wikipedia import WikipediaTool
from beeai_framework.tools.weather import OpenMeteoTool
from beeai_framework.tools.code import PythonTool, LocalPythonStorage
import os
import tempfile

def create_agent() -> ReActAgent:
    llm = ChatModel.from_name("ollama:granite3.3:8b", ChatModelParameters(temperature=0))
    tools = [WikipediaTool(), OpenMeteoTool(), DuckDuckGoSearchTool()]

    code_interpreter_url = os.getenv("CODE_INTERPRETER_URL")
    if code_interpreter_url:
        tools.append(
            PythonTool(
                code_interpreter_url,
                LocalPythonStorage(
                    local_working_dir=tempfile.mkdtemp("code_interpreter_source"),
                    interpreter_working_dir=os.getenv("CODE_INTERPRETER_TMPDIR", "./tmp/code_interpreter_target"),
                ),
            )
        )

    agent = ReActAgent(llm=llm, tools=tools, memory=TokenMemory(llm))
    return agent
```

- The agent is created with:
  - A chat model with specific parameters.
  - Multiple tools including search and weather.
  - Optional code interpreter tool if environment variable is set.
  - Token-based memory for efficient context management.

### Running the ReAct Agent

- The example includes an async main loop that reads user input and runs the agent.
- Events such as errors, retries, updates, start, and success are logged.

---

## 3. Using Specialist Scaffold Tools for Agent Creation

### ToolCallingAgent Class (Core API)

- Located at `beeai_framework/agents/tool_calling/agent.py`.
- This class extends `BaseAgent` and provides:
  - Initialization with LLM, memory, tools, templates, and configuration.
  - The `run` method which handles the agent's reasoning and tool calling loop.
  - Tool call cycle detection to avoid infinite loops.
  - Final answer handling as a tool call.
  - Event emission for lifecycle hooks (`start`, `success`).
  - Cloning support for agent instances.

### Highlights from `ToolCallingAgent`:

- The `run` method is asynchronous and manages iterations, retries, and tool calls.
- Tools are dynamically called based on the LLM's output.
- Tool call checker prevents cycles in tool calls.
- Final answers can be returned as tool calls or plain text.
- Memory is updated with all messages and tool results.

### Using `ToolCallingAgent` in Your Code

- Instantiate with your LLM, memory, and tools.
- Optionally override prompt templates.
- Call `await agent.run(prompt)` to execute.
- Listen to events for debugging or UI updates.

---

## 4. Example: Structured Tool Calling with Typed Output

### Example: `examples/agents/tool_calling_structured.py`

- Demonstrates how to use `ToolCallingAgent` with Pydantic models for structured output.
- Shows how to customize system prompt templates.
- Uses a `WeatherForecastModel` Pydantic class to parse and validate the agent's final output.

#### Key snippet:

```python
from pydantic import BaseModel

class WeatherForecatModel(BaseModel):
    location_name: str
    temperature_current_celsius: str
    temperature_max_celsius: str
    temperature_min_celsius: str
    relative_humidity_percent: str
    wind_speed_kmh: str
    explanation: str

agent = ToolCallingAgent(
    llm=ChatModel.from_name("ollama:granite3.3:8b"),
    memory=UnconstrainedMemory(),
    tools=[OpenMeteoTool()],
    templates={
        "system": lambda template: template.update(
            defaults={
                "role": "a weather forecast agent",
                "instructions": "- If user only provides a location, assume they want to know the weather forecast for it.",
            }
        ),
    },
)

response = await agent.run(prompt, expected_output=WeatherForecatModel)
```

- This approach ensures the agent's output is validated and structured.
- The example also logs intermediate steps for debugging.

---

## 5. Summary of Key Files and Their Roles

| File Path | Description |
|-----------|-------------|
| `examples/agents/tool_calling.py` | Simple example to create and run a ToolCallingAgent with weather tool. |
| `beeai_framework/agents/tool_calling/agent.py` | Core implementation of the ToolCallingAgent class with tool calling logic. |
| `examples/agents/react.py` | Example of creating a ReAct agent with multiple tools and memory. |
| `examples/agents/tool_calling_structured.py` | Example showing structured output with Pydantic models and tool calling. |
| `beeai_framework/agents/react/agent.py` | (Not shown here but relevant) Implementation of ReActAgent class. |
| `beeai_framework/backend/chat.py` | ChatModel class used to interface with LLMs. |
| `beeai_framework/tools/weather/openmeteo.py` | Example tool providing weather data. |
| `examples/helpers/io.py` | ConsoleReader utility for interactive input/output. |

---

## 6. How to Run Your Agent Script

1. Ensure environment variables are set (e.g., API keys, model names) - `.env` file supported via `dotenv`.
2. Install dependencies for BeeAI Framework and any backend LLM providers.
3. Create a Python script (or use provided examples) that:
   - Imports the agent class (`ToolCallingAgent` or `ReActAgent`).
   - Instantiates the agent with desired LLM, memory, and tools.
   - Runs an async main loop to read user input and call `agent.run()`.
4. Run the script with Python:

```bash
python agent.py
```

---

## 7. Additional Notes

- The framework supports event-driven programming with an `Emitter` system to hook into agent lifecycle events.
- Memory management is flexible with multiple implementations (e.g., `UnconstrainedMemory`, `TokenMemory`).
- Tools are modular and can be custom-built or imported from the framework's toolsets.
- The framework supports advanced features like tool call cycle detection and final answer as a tool call.
- For advanced use, you can customize prompt templates and tool call checking behavior.

---

## References to Source Code and Docs

- `examples/agents/tool_calling.py` (lines 1-50): Basic ToolCallingAgent usage with event handling.
- `beeai_framework/agents/tool_calling/agent.py` (lines 1-250): Full implementation of ToolCallingAgent.
- `examples/agents/react.py` (lines 1-100): ReActAgent creation with multiple tools and memory.
- `examples/agents/tool_calling_structured.py` (lines 1-80): Structured output example with Pydantic.
- `beeai_framework/tools/weather/openmeteo.py`: Weather tool used in examples.
- `beeai_framework/backend/chat.py`: ChatModel class for LLM integration.
- `examples/helpers/io.py`: ConsoleReader for interactive CLI input/output.

---

# Summary

This guide has shown how to use the BeeAI Framework API to create Python agents that can be run directly, focusing on:

- Creating a ToolCallingAgent with asynchronous event-driven interaction.
- Creating a ReAct agent with tool calling and multiple tools.
- Using scaffold tools and classes provided by the framework to avoid hand-coding everything.
- Structuring agent output with Pydantic models for validation.
- Running the agent interactively from the command line.

By following the examples and referencing the core agent implementation, you can build powerful AI agents with tool integration using the BeeAI Framework.

---

If you want me to generate a ready-to-run minimal example script or further details on any part, please ask!
```
