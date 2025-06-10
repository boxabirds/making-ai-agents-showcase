# AgentStack API Usage Guide for Creating and Running Agents in Python

This document provides an exhaustive guide on how to use the AgentStack API to create an agent that can be run directly in Python (e.g., `python agent.py`), with a focus on creating a Python ReAct agent with tool calling. The guide includes detailed references to the source code and explains the use of scaffold tools provided by the package.

---

## 1. Overview of AgentStack Agent Configuration

### AgentConfig Class (`agentstack/agents.py`)

- **Purpose**: Represents an agent configuration stored in a YAML file (`src/config/agents.yaml`).
- **Usage**: Use as a context manager to load, modify, and save agent configurations.
- **Key Attributes**:
  - `name`: Agent's unique name.
  - `role`: The role of the agent.
  - `goal`: The agent's goal.
  - `backstory`: Background story for the agent.
  - `llm`: The language model identifier (e.g., `openai/gpt-4o`).

### Example Usage

```python
from agentstack.agents import AgentConfig

with AgentConfig('agent_name') as config:
    config.llm = "openai/gpt-4o"
    config.role = "Research Assistant"
    config.goal = "Help with AI research"
    config.backstory = "Experienced AI researcher"
```

- The agent configurations are persisted automatically on exiting the context manager.
- The class also provides properties to parse the LLM provider and model.

---

## 2. Creating and Adding an Agent Programmatically

### `add_agent` Function (`agentstack/generation/agent_generation.py`)

- **Purpose**: Adds a new agent to the user's project.
- **Parameters**:
  - `name`: Agent name.
  - `role`, `goal`, `backstory`: Optional descriptive fields.
  - `llm`: Optional LLM model string.
  - `allow_delegation`: Currently not implemented.
  - `position`: Optional insertion point in the codebase.

### How it Works

- Validates the project.
- Loads or creates an `AgentConfig`.
- Sets the agent's properties.
- Delegates to the framework-specific `add_agent` method to update the codebase.
- Logs success or raises validation errors.

### Example Usage

```python
from agentstack.generation.agent_generation import add_agent

add_agent(
    name="research_agent",
    role="Research Assistant",
    goal="Assist with research tasks",
    backstory="Experienced in AI and ML",
    llm="openai/gpt-4o"
)
```

---

## 3. Framework Abstraction and Code Generation

### Framework Modules (`agentstack/frameworks/__init__.py`)

- AgentStack supports multiple frameworks (e.g., `crewai`, `langgraph`, `openai_swarm`, `llamaindex`).
- Each framework module implements:
  - Validation of the project structure.
  - Adding agents, tasks, and tools.
  - Wrapping tool functions for integration.
  - Managing the codebase's entrypoint file (usually a Python file with a base class defining agents and tasks).

### Entrypoint File Handling

- The base class in the entrypoint file (e.g., `UserStack`) contains:
  - Methods decorated with `@agentstack.agent` (agents).
  - Methods decorated with `@agentstack.task` (tasks).
  - A `run` method accepting `inputs`.

- The framework module can:
  - Add new agent methods.
  - Add new task methods.
  - Modify the list of tools an agent uses.

---

## 4. Creating a Python ReAct Agent with Tool Calling

### Using Scaffold Tools (`examples/howards_agent/src/crew.py`)

- The `crewai` framework is used as an example.
- Define a crew class decorated with `@CrewBase`.
- Define agents with the `@agent` decorator.
- Define tasks with the `@task` decorator.
- Define the crew with the `@crew` decorator, specifying agents, tasks, and process type.

### Example Crew Definition

```python
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
import tools

@CrewBase
class HowardsagentCrew():
    @agent
    def agent1(self) -> Agent:
        return Agent(
            config=self.agents_config['agent1'],
            tools=[*tools.composio_tools],  # Tools for the agent
            verbose=True
        )

    @task
    def new_task(self) -> Task:
        return Task(config=self.tasks_config['new_task'])

    @task
    def task1(self) -> Task:
        return Task(config=self.tasks_config['task1'])

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
```

### Tools Integration (`examples/howards_agent/src/tools/composio_tool.py`)

- Tools are imported and passed to agents.
- Example uses `ComposioToolSet` with `App.CODEINTERPRETER`.
- Tools enable the agent to perform actions beyond text generation.

---

## 5. Running the Agent Locally

### Example Main Script (`examples/howards_agent/src/main.py`)

- Initialize the environment and AgentOps.
- Create an instance of the crew.
- Kick off the crew with input parameters.

```python
#!/usr/bin/env python
import sys
from crew import HowardsagentCrew
import agentops
from dotenv import load_dotenv

load_dotenv()
agentops.init(default_tags=['howards_agent', 'agentstack'])

def run():
    inputs = {'topic': 'AI LLMs'}
    HowardsagentCrew().crew().kickoff(inputs=inputs)

if __name__ == "__main__":
    run()
```

- Run the agent with `python main.py`.

---

## 6. Summary of Key API Components

| Component               | Location                                   | Description                                                                                   |
|------------------------|--------------------------------------------|-----------------------------------------------------------------------------------------------|
| `AgentConfig`          | `agentstack/agents.py`                      | Load, edit, and save agent configurations stored in YAML.                                    |
| `add_agent`            | `agentstack/generation/agent_generation.py`| Add a new agent to the project, updating config and codebase.                                |
| Framework modules      | `agentstack/frameworks/`                    | Handle framework-specific code generation and validation.                                    |
| Crew and Agent classes | `examples/howards_agent/src/crew.py`        | Define agents, tasks, and crew using decorators for easy scaffolding.                        |
| Tools                  | `examples/howards_agent/src/tools/`          | Define and import tools to extend agent capabilities.                                        |
| Main script            | `examples/howards_agent/src/main.py`         | Run the agent locally with input parameters.                                                 |

---

## 7. Additional Notes

- The framework abstraction allows switching between different agent execution frameworks with minimal code changes.
- The `agentstack` CLI provides commands to generate agents and tasks, which internally use the same API (`add_agent` etc.).
- Tools are wrapped with `agentops` events for telemetry and integrated with the framework's decorators.
- The project expects a certain structure in the entrypoint file, including a base class with decorated methods for agents and tasks.

---

## 8. References to Source Code

- Agent configuration and persistence: [`agentstack/agents.py`](output/cache/AgentOps-AI/AgentStack/agentstack/agents.py) (lines 1-150)
- Adding agents programmatically: [`agentstack/generation/agent_generation.py`](output/cache/AgentOps-AI/AgentStack/agentstack/generation/agent_generation.py) (lines 1-50)
- Framework abstraction and code generation: [`agentstack/frameworks/__init__.py`](output/cache/AgentOps-AI/AgentStack/agentstack/frameworks/__init__.py) (lines 1-300+)
- Example crew and agent definition: [`examples/howards_agent/src/crew.py`](output/cache/AgentOps-AI/AgentStack/examples/howards_agent/src/crew.py) (lines 1-60)
- Example tools integration: [`examples/howards_agent/src/tools/composio_tool.py`](output/cache/AgentOps-AI/AgentStack/examples/howards_agent/src/tools/composio_tool.py) (lines 1-10)
- Example main script to run agent: [`examples/howards_agent/src/main.py`](output/cache/AgentOps-AI/AgentStack/examples/howards_agent/src/main.py) (lines 1-50)

---

# Conclusion

To create and run an agent directly in Python using AgentStack:

1. Define your agent configuration using `AgentConfig` or the `add_agent` API.
2. Use the framework abstraction to scaffold agent and task methods in your project.
3. Define a crew class with agents and tasks using decorators (`@agent`, `@task`, `@crew`).
4. Integrate tools to enable tool calling within your agent.
5. Use a main script to instantiate and run your crew with input parameters.
6. Run the script with `python agent.py` or equivalent.

This approach leverages scaffold tools and framework abstractions to minimize hand-coding and ensure consistency across projects.

If you want to create a Python ReAct agent with tool calling, the `crewai` framework example (`examples/howards_agent`) is a practical starting point, demonstrating how to define agents with tools and run them locally.

For more detailed usage, refer to the source files and the inline comments provided in the codebase.