# Comprehensive Guide to Creating and Running a Python ReAct Agent with Tool Calling Using Microsoft Semantic Kernel

This document provides an exhaustive, detailed guide on how to use the Microsoft Semantic Kernel Python package to create an agent that can be run directly in Python (e.g., `python agent.py`). It specifically addresses how to create a Python ReAct agent with tool calling capabilities, leveraging the Semantic Kernel API and its scaffolding tools.

---

## Table of Contents

1. [Overview of Semantic Kernel Agent API](#overview-of-semantic-kernel-agent-api)
2. [Creating and Running a Basic Agent in Python](#creating-and-running-a-basic-agent-in-python)
3. [Creating a Python ReAct Agent with Tool Calling](#creating-a-python-react-agent-with-tool-calling)
4. [Using Scaffolding Tools and Declarative Agent Creation](#using-scaffolding-tools-and-declarative-agent-creation)
5. [References to Source Code and Documentation](#references-to-source-code-and-documentation)

---

## Overview of Semantic Kernel Agent API

The Semantic Kernel Python package provides a rich API to create, manage, and run AI agents. The core runtime for in-process agent execution is implemented in:

- `semantic_kernel/agents/runtime/in_process/in_process_runtime.py`

This module defines the `InProcessRuntime` class, which manages message passing, agent instantiation, and message processing asynchronously using Python's `asyncio`.

Key features of the runtime include:

- Registering agent factories to create agents dynamically.
- Sending and publishing messages to agents.
- Managing subscriptions and message queues.
- Handling agent lifecycle (start, stop, save/load state).
- Support for intervention handlers to intercept messages.

The runtime processes messages concurrently but ensures ordered delivery per message queue.

---

## Creating and Running a Basic Agent in Python

The package provides sample code demonstrating how to create and run an agent using the Azure OpenAI assistant agent as an example.

### Example: Basic OpenAI Assistant Agent

File: `samples/getting_started_with_agents/openai_assistant/step1_assistant.py`

This example shows how to:

1. Create an Azure OpenAI client.
2. Create an assistant definition on the Azure OpenAI service.
3. Instantiate an `AzureAssistantAgent` with the client and definition.
4. Interact with the agent by sending user inputs and receiving responses.
5. Manage conversation threads automatically.

```python
import asyncio
from semantic_kernel.agents import AssistantAgentThread, AzureAssistantAgent
from semantic_kernel.connectors.ai.open_ai import AzureOpenAISettings

USER_INPUTS = [
    "Why is the sky blue?",
    "What is the speed of light?",
    "What have we been talking about?",
]

async def main():
    client = AzureAssistantAgent.create_client()
    definition = await client.beta.assistants.create(
        model=AzureOpenAISettings().chat_deployment_name,
        instructions="Answer questions about the world in one sentence.",
        name="Assistant",
    )
    agent = AzureAssistantAgent(client=client, definition=definition)
    thread = None

    try:
        for user_input in USER_INPUTS:
            print(f"# User: '{user_input}'")
            response = await agent.get_response(messages=user_input, thread=thread)
            print(f"# {response.name}: {response}")
            thread = response.thread
    finally:
        await thread.delete() if thread else None
        await agent.client.beta.assistants.delete(assistant_id=agent.id)

if __name__ == "__main__":
    asyncio.run(main())
```

**How to run:** Save as `agent.py` and run `python agent.py`.

---

## Creating a Python ReAct Agent with Tool Calling

ReAct (Reasoning + Acting) agents combine reasoning with tool usage (function calling). Semantic Kernel supports this pattern by allowing agents to call functions/plugins as tools during conversation.

### Key Concepts

- **Plugins/Functions:** Python classes with methods decorated by `@kernel_function` to expose callable tools.
- **Function Calling:** The agent can invoke these functions dynamically based on user input.
- **Declarative Spec:** Agents can be created declaratively from YAML specs that define the agent's behavior, inputs, outputs, and tools.

### Example: OpenAI Assistant with Plugins (Tool Calling)

File: `samples/getting_started_with_agents/openai_assistant/step2_assistant_plugins.py`

This example demonstrates:

- Defining a plugin class with kernel functions.
- Creating an assistant agent with plugins.
- Invoking the agent asynchronously and streaming responses.

```python
import asyncio
from semantic_kernel.agents import AssistantAgentThread, AzureAssistantAgent
from semantic_kernel.connectors.ai.open_ai import AzureOpenAISettings
from semantic_kernel.functions import kernel_function

class MenuPlugin:
    @kernel_function(description="Provides a list of specials from the menu.")
    def get_specials(self) -> str:
        return """
        Special Soup: Clam Chowder
        Special Salad: Cobb Salad
        Special Drink: Chai Tea
        """

    @kernel_function(description="Provides the price of the requested menu item.")
    def get_item_price(self, menu_item: str) -> str:
        return "$9.99"

USER_INPUTS = [
    "Hello",
    "What is the special soup?",
    "What is the special drink?",
    "How much is it?",
    "Thank you",
]

async def main():
    client = AzureAssistantAgent.create_client()
    definition = await client.beta.assistants.create(
        model=AzureOpenAISettings().chat_deployment_name,
        instructions="Answer questions about the menu.",
        name="Host",
    )
    agent = AzureAssistantAgent(client=client, definition=definition, plugins=[MenuPlugin()])
    thread = None

    try:
        for user_input in USER_INPUTS:
            print(f"# User: '{user_input}'")
            async for response in agent.invoke(messages=user_input, thread=thread):
                print(f"# Agent: {response}")
                thread = response.thread
    finally:
        await thread.delete() if thread else None
        await agent.client.beta.assistants.delete(assistant_id=agent.id)

if __name__ == "__main__":
    asyncio.run(main())
```

**How this works:**

- The `MenuPlugin` exposes two functions as tools.
- The agent uses these tools to answer user queries.
- The `invoke` method streams responses asynchronously.

---

## Using Scaffolding Tools and Declarative Agent Creation

Semantic Kernel supports declarative agent creation from YAML specs, which can define the agent type, model, instructions, inputs, outputs, and tools.

### Example: Declarative Agent from YAML String

File: `samples/concepts/agents/openai_assistant/openai_assistant_declarative_templating.py`

```python
import asyncio
from semantic_kernel.agents import AgentRegistry, OpenAIAssistantAgent

spec = """
type: openai_assistant
name: StoryAgent
description: An agent that generates a story about a topic.
instructions: Tell a story about {{$topic}} that is {{$length}} sentences long.
model:
  id: ${OpenAI:ChatModelId}
inputs:
  topic:
    description: The topic of the story.
    required: true
    default: Cats
  length:
    description: The number of sentences in the story.
    required: true
    default: 2
outputs:
  output1:
    description: The generated story.
template:
  format: semantic-kernel
"""

async def main():
    client = OpenAIAssistantAgent.create_client()
    agent = await AgentRegistry.create_from_yaml(yaml_str=spec, client=client)

    async for response in agent.invoke(messages=None):
        print(f"# {response.name}: {response}")

    await client.beta.assistants.delete(agent.id)

if __name__ == "__main__":
    asyncio.run(main())
```

### Example: Declarative Agent from YAML File with Plugins

File: `samples/concepts/agents/openai_assistant/openai_assistant_declarative_function_calling_from_file.py`

This example loads a declarative spec from a YAML file and attaches plugins for tool calling.

```python
import asyncio
import os
from semantic_kernel.agents import AgentRegistry, OpenAIAssistantAgent
from semantic_kernel.functions import kernel_function

class MenuPlugin:
    @kernel_function(description="Provides a list of specials from the menu.")
    def get_specials(self) -> str:
        return """
        Special Soup: Clam Chowder
        Special Salad: Cobb Salad
        Special Drink: Chai Tea
        """

    @kernel_function(description="Provides the price of the requested menu item.")
    def get_item_price(self, menu_item: str) -> str:
        return "$9.99"

async def main():
    client = OpenAIAssistantAgent.create_client()
    file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))),
        "resources",
        "declarative_spec",
        "openai_assistant_spec.yaml",
    )
    agent = await AgentRegistry.create_from_file(file_path, plugins=[MenuPlugin()], client=client)

    user_inputs = [
        "Hello",
        "What is the special soup?",
        "How much does that cost?",
        "Thank you",
    ]
    thread = None

    for user_input in user_inputs:
        print(f"# User: '{user_input}'")
        async for response in agent.invoke(messages=user_input, thread=thread):
            print(f"# {response.name}: {response}")
            thread = response.thread

    await client.beta.assistants.delete(agent.id) if agent else None
    await thread.delete() if thread else None

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Additional Example: Auto Function Calling with ReAct Style

File: `samples/concepts/auto_function_calling/chat_completion_with_auto_function_calling.py`

This example shows how to build a conversational chatbot with auto function calling enabled, using Semantic Kernel's `Kernel` class and plugins.

Key points:

- Plugins like `MathPlugin` and `TimePlugin` are added to the kernel.
- Chat completion service is configured with function calling behavior.
- Chat history is maintained.
- The bot automatically calls functions as needed during conversation.

```python
import asyncio
from semantic_kernel import Kernel
from semantic_kernel.core_plugins.math_plugin import MathPlugin
from semantic_kernel.core_plugins.time_plugin import TimePlugin
from semantic_kernel.functions import KernelArguments
from samples.concepts.setup.chat_completion_services import Services, get_chat_completion_service_and_request_settings
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents import ChatHistory

system_message = """
You are a chat bot. Your name is Mosscap and
you have one goal: figure out what people need.
Your full name, should you need to know it, is
Splendid Speckled Mosscap. You communicate
effectively, but you tend to answer with long
flowery prose. You are also a math wizard,
especially for adding and subtracting.
You also excel at joke telling, where your tone is often sarcastic.
Once you have the answer I am looking for,
you will return a full answer to me as soon as possible.
"""

kernel = Kernel()
kernel.add_plugin(MathPlugin(), plugin_name="math")
kernel.add_plugin(TimePlugin(), plugin_name="time")

chat_function = kernel.add_function(
    prompt="{{$chat_history}}{{$user_input}}",
    plugin_name="ChatBot",
    function_name="Chat",
)

chat_completion_service, request_settings = get_chat_completion_service_and_request_settings(Services.AZURE_OPENAI)
request_settings.function_choice_behavior = FunctionChoiceBehavior.Auto(filters={"excluded_plugins": ["ChatBot"]})

kernel.add_service(chat_completion_service)
arguments = KernelArguments(settings=request_settings)

history = ChatHistory()
history.add_system_message(system_message)
history.add_user_message("Hi there, who are you?")
history.add_assistant_message("I am Mosscap, a chat bot. I'm trying to figure out what people need.")

async def chat() -> bool:
    user_input = input("User:> ")
    if user_input.lower().strip() == "exit":
        return False
    arguments["user_input"] = user_input
    arguments["chat_history"] = history
    result = await kernel.invoke(chat_function, arguments=arguments)
    if result:
        print(f"Mosscap:> {result}")
        history.add_user_message(user_input)
        history.add_message(result.value[0])
    return True

async def main():
    print("Welcome to the chat bot! Type 'exit' to exit.")
    chatting = True
    while chatting:
        chatting = await chat()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Summary: How to Create and Run a Python ReAct Agent with Tool Calling

1. **Set up the environment and dependencies** for Semantic Kernel and your AI service (Azure OpenAI, OpenAI, etc.).

2. **Create or use an existing AI client** (e.g., `AzureAssistantAgent.create_client()`).

3. **Define your agent:**
   - Use a direct Python class (e.g., `AzureAssistantAgent`) with optional plugins exposing tools via `@kernel_function`.
   - Or create declaratively from YAML spec using `AgentRegistry.create_from_yaml()` or `AgentRegistry.create_from_file()`.

4. **Add plugins (tools) to the agent** by passing plugin instances to the agent constructor or kernel.

5. **Invoke the agent asynchronously** using `agent.invoke()` or `agent.get_response()` to send user inputs and receive responses.

6. **Manage conversation threads** to maintain context across interactions.

7. **Run the agent script directly** with `python agent.py`.

---

## References to Source Code and Documentation

- **InProcessRuntime (core runtime for agents):**  
  `semantic_kernel/agents/runtime/in_process/in_process_runtime.py`  
  (See lines 50-600 for full implementation of message handling, agent registration, and runtime lifecycle.)

- **Basic Azure OpenAI Assistant Agent Example:**  
  `samples/getting_started_with_agents/openai_assistant/step1_assistant.py`

- **Assistant Agent with Plugins (Tool Calling):**  
  `samples/getting_started_with_agents/openai_assistant/step2_assistant_plugins.py`

- **Declarative Agent Creation from YAML:**  
  `samples/concepts/agents/openai_assistant/openai_assistant_declarative_templating.py`  
  `samples/concepts/agents/openai_assistant/openai_assistant_declarative_function_calling_from_file.py`

- **Auto Function Calling ReAct Style Chatbot:**  
  `samples/concepts/auto_function_calling/chat_completion_with_auto_function_calling.py`

- **Semantic Kernel GitHub Repository and Docs:**  
  [Semantic Kernel GitHub](https://github.com/microsoft/semantic-kernel)  
  [Semantic Kernel Python SDK Docs](https://aka.ms/semantic-kernel/docs/python)

---

# Final Notes

- The Semantic Kernel Python SDK provides high-level abstractions and scaffolding tools to create powerful AI agents with tool calling capabilities.
- Using declarative YAML specs and plugins simplifies agent creation and maintenance.
- The runtime supports asynchronous message processing and agent lifecycle management.
- The provided sample scripts are runnable and serve as excellent starting points for building your own ReAct agents.

---

This guide should enable you to create, run, and extend Python ReAct agents with tool calling using the Microsoft Semantic Kernel package effectively.