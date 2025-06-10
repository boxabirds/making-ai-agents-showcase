# Griptape AI Package: Comprehensive Guide to Creating and Running a Python ReAct Agent with Tool Calling

This document provides an exhaustive guide on how to use the Griptape AI package API to create an agent that can be run directly in Python (e.g., `python agent.py`). It also answers the question: "How can I use this API to create a Python ReAct agent with tool calling?" The guide includes detailed references to the source code and highlights useful components and patterns for building such agents.

---

## Table of Contents

1. [Overview of the Griptape AI Package](#overview-of-the-griptape-ai-package)
2. [Creating and Running an Agent in Python](#creating-and-running-an-agent-in-python)
3. [Building a Python ReAct Agent with Tool Calling](#building-a-python-react-agent-with-tool-calling)
4. [Key Classes and Components](#key-classes-and-components)
5. [Example: Minimal Python Agent Script](#example-minimal-python-agent-script)
6. [Additional Notes and References](#additional-notes-and-references)

---

## Overview of the Griptape AI Package

Griptape AI is a framework designed to build AI agents with modular components such as tasks, tools, drivers, and memory. It supports advanced agent architectures like ReAct (Reasoning + Acting) with tool calling capabilities.

- The core agent abstraction is provided by the `Agent` class in `griptape.structures.agent`.
- Tasks, especially `PromptTask`, drive the agent's behavior and interaction with language models and tools.
- Tools encapsulate external capabilities or APIs that the agent can call.
- Drivers handle communication with language models and other services.
- The package uses `attrs` for declarative class definitions and validation.

---

## Creating and Running an Agent in Python

### The `Agent` Class

The `Agent` class is the main entry point for creating an agent. It is defined in:

- **File:** `griptape/structures/agent.py`

Key points from the `Agent` class:

- It inherits from `Structure`.
- It accepts an `input` which can be a string, list, tuple, artifact, or callable returning an artifact.
- It supports a `prompt_driver` (language model driver) and a list of `tools`.
- It manages a single `PromptTask` internally.
- The `try_run()` method runs the agent's task and returns the agent instance.

Excerpt from `Agent` class initialization and run:

```python
@define
class Agent(Structure):
    input: Union[str, list, tuple, BaseArtifact, Callable[[BaseTask], BaseArtifact]] = field(
        default=lambda task: task.full_context["args"][0] if task.full_context["args"] else TextArtifact(value=""),
    )
    stream: Optional[bool] = field(default=None, kw_only=True)
    prompt_driver: Optional[BasePromptDriver] = field(default=None, kw_only=True)
    tools: list[BaseTool] = field(factory=list, kw_only=True)
    # ... other fields ...

    def __attrs_post_init__(self) -> None:
        super().__attrs_post_init__()
        if len(self.tasks) == 0:
            self._init_task()

    @observable
    def try_run(self, *args) -> Agent:
        self.task.run()
        return self

    def _init_task(self) -> None:
        # Initialize prompt driver if not set
        if self.stream is None:
            with validators.disabled():
                self.stream = Defaults.drivers_config.prompt_driver.stream

        if self.prompt_driver is None:
            with validators.disabled():
                prompt_driver = evolve(Defaults.drivers_config.prompt_driver, stream=self.stream)
                self.prompt_driver = prompt_driver
        else:
            prompt_driver = self.prompt_driver

        task = PromptTask(
            self.input,
            prompt_driver=prompt_driver,
            tools=self.tools,
            output_schema=self.output_schema,
            max_meta_memory_entries=self.max_meta_memory_entries,
        )
        self.add_task(task)
```

### Running the Agent

To run the agent, instantiate it with the desired input, tools, and optionally a prompt driver, then call `try_run()`:

```python
agent = Agent(input="Hello, world!", tools=[...])
agent.try_run()
```

---

## Building a Python ReAct Agent with Tool Calling

### The `PromptTask` Class

The `PromptTask` class is the core task that drives the agent's prompt-based reasoning and tool usage.

- **File:** `griptape/tasks/prompt_task.py`

Key features:

- Supports tools and tool calling.
- Manages subtasks representing reasoning steps and tool invocations.
- Uses a prompt driver to generate outputs.
- Supports output schema validation.
- Implements ReAct style reasoning with subtasks and tool calls.

Excerpt from `PromptTask`:

```python
@define
class PromptTask(BaseTask, RuleMixin, ActionsSubtaskOriginMixin):
    prompt_driver: BasePromptDriver = field(default=Factory(lambda: Defaults.drivers_config.prompt_driver), kw_only=True)
    tools: list[BaseTool] = field(factory=list, kw_only=True)
    max_subtasks: int = field(default=20, kw_only=True)
    response_stop_sequence: str = field(default="<|Response|>", kw_only=True)
    reflect_on_tool_use: bool = field(default=True, kw_only=True)

    def try_run(self) -> BaseArtifact:
        self.subtasks.clear()
        if self.response_stop_sequence not in self.prompt_driver.tokenizer.stop_sequences:
            self.prompt_driver.tokenizer.stop_sequences.append(self.response_stop_sequence)

        output = self.prompt_driver.run(self.prompt_stack).to_artifact(
            meta={"is_react_prompt": not self.prompt_driver.use_native_tools}
        )
        for subtask_runner in self.subtask_runners:
            output = subtask_runner(output)

        return output
```

### Using Tools

Tools are defined as subclasses of `BaseTool` and provide specific capabilities. The agent can call these tools during its reasoning process.

- Tools are passed to the `Agent` or `PromptTask` via the `tools` parameter.
- The `PromptTask` manages tool calling via subtasks (`ActionsSubtask`).

Example tools include:

- `ComputerTool` (executes Python code or shell commands in Docker containers)
- `CalculatorTool`
- `WebSearchTool`
- `RestApiTool`
- And many others (see `griptape/tools/__init__.py` for the full list)

---

## Key Classes and Components

| Component               | Location                                  | Description                                                                                   |
|------------------------|-------------------------------------------|-----------------------------------------------------------------------------------------------|
| `Agent`                | `griptape/structures/agent.py`            | Main agent class, manages a single `PromptTask` and tools.                                   |
| `PromptTask`           | `griptape/tasks/prompt_task.py`           | Task that handles prompt generation, tool calling, and ReAct subtasks.                       |
| `BaseTool`             | `griptape/tools/base_tool.py`              | Base class for all tools.                                                                     |
| `ComputerTool`         | `griptape/tools/computer/tool.py`          | Tool to execute Python code or shell commands inside Docker containers.                       |
| `PromptDriver` (default) | Configured via `Defaults.drivers_config` | Driver that interfaces with language models for prompt generation.                            |
| `TextArtifact`         | `griptape/artifacts/text_artifact.py`      | Represents text data passed between components.                                              |

---

## Example: Minimal Python Agent Script

Below is a minimal example of how to create and run an agent with tool calling using the Griptape API:

```python
from griptape.structures import Agent
from griptape.tools.computer.tool import ComputerTool

def main():
    # Instantiate tools
    computer_tool = ComputerTool()

    # Create an agent with input, tools, and default prompt driver
    agent = Agent(
        input="Calculate the factorial of 5 using Python code.",
        tools=[computer_tool]
    )

    # Run the agent
    agent.try_run()

    # Access the output of the agent's task
    print(agent.task.output.to_text())

if __name__ == "__main__":
    main()
```

Save this as `agent.py` and run it with:

```bash
python agent.py
```

---

## Additional Notes and References

- The `Agent` class only supports a single task internally, which is typically a `PromptTask`.
- The `PromptTask` manages subtasks that represent reasoning steps and tool calls, enabling ReAct style behavior.
- Tools must have unique names when passed to the agent or task.
- The `ComputerTool` is a powerful example of a tool that can execute arbitrary Python code or shell commands inside Docker containers, enabling complex programmatic reasoning.
- The prompt driver can be customized or replaced by passing a different `prompt_driver` to the `Agent` or `PromptTask`.
- The package uses `attrs` for declarative class definitions and validation, and `pydantic` or `schema` for output schema validation.
- The `try_run()` method on the `Agent` or `PromptTask` triggers the execution of the agent's reasoning and tool calling.

---

## References to Source Code

- Agent class: [`griptape/structures/agent.py`](output/cache/griptape-ai/griptape/griptape/structures/agent.py) (lines 1-120)
- PromptTask class: [`griptape/tasks/prompt_task.py`](output/cache/griptape-ai/griptape/griptape/tasks/prompt_task.py) (lines 1-300 approx)
- ComputerTool example: [`griptape/tools/computer/tool.py`](output/cache/griptape-ai/griptape/griptape/tools/computer/tool.py) (lines 1-150 approx)
- Tools package init: [`griptape/tools/__init__.py`](output/cache/griptape-ai/griptape/griptape/tools/__init__.py)
- Artifacts (e.g., TextArtifact): [`griptape/artifacts/text_artifact.py`]
- Defaults and config: [`griptape/configs/defaults_config.py`]

---

This guide should enable you to create, customize, and run a Python ReAct agent with tool calling using the Griptape AI package efficiently and effectively.