# BabyAGI API Usage Guide for Creating a ReAct Agent with Tool Calling

This document provides an exhaustive and detailed explanation of how to use the BabyAGI API to create a ReAct (Reasoning and Acting) agent that can perform tool calling. It is based on the BabyAGI framework by Yohei Nakajima, which is designed for building autonomous agents with a function execution framework and tool integration.

---

## Table of Contents

- [Overview of BabyAGI](#overview-of-babyagi)
- [Core Concepts](#core-concepts)
- [Setting Up BabyAGI](#setting-up-babyagi)
- [Creating a ReAct Agent with Tool Calling](#creating-a-react-agent-with-tool-calling)
  - [Understanding the `react_agent` Function](#understanding-the-react_agent-function)
  - [Step-by-Step Explanation of `react_agent`](#step-by-step-explanation-of-react_agent)
- [Using the API to Create Your Own ReAct Agent](#using-the-api-to-create-your-own-react-agent)
- [Example Usage](#example-usage)
- [Additional Notes and Best Practices](#additional-notes-and-best-practices)
- [References to Related Functions and Packs](#references-to-related-functions-and-packs)

---

## Overview of BabyAGI

BabyAGI is an experimental framework for building autonomous agents that can self-build and self-manage functions. It uses a function database and a graph-based structure to manage dependencies, imports, and secret keys. The framework supports:

- Registering and managing functions with metadata.
- Loading function packs (collections of related functions).
- Executing functions with dependency resolution.
- Integrating with language models (e.g., OpenAI GPT models) for reasoning and tool use.
- Providing a dashboard and API for managing functions and keys.

---

## Core Concepts

- **Function Registration:** Functions are registered with metadata, dependencies, and key requirements.
- **Function Packs:** Bundles of functions that can be loaded together.
- **Tool Calling:** The agent can call registered functions as tools during its reasoning process.
- **LiteLLM Integration:** Uses LiteLLM for language model completions with tool calling support.
- **Chain-of-Thought Reasoning:** The agent reasons step-by-step, calling functions as needed until the task is complete.

---

## Setting Up BabyAGI

1. **Install BabyAGI:**

   ```bash
   pip install babyagi
   ```

2. **Create a Flask app with BabyAGI dashboard:**

   ```python
   import babyagi
   import os

   app = babyagi.create_app('/dashboard')

   # Add your OpenAI API key for function descriptions and embeddings
   babyagi.add_key_wrapper('openai_api_key', os.environ['OPENAI_API_KEY'])

   if __name__ == "__main__":
       app.run(host='0.0.0.0', port=8080)
   ```

3. **Access the dashboard:**

   Open your browser at `http://localhost:8080/dashboard` to manage functions and keys.

---

## Creating a ReAct Agent with Tool Calling

### Understanding the `react_agent` Function

The core example of a ReAct agent with tool calling is implemented in the file:

`babyagi/functionz/packs/drafts/react_agent.py`

This function is registered with the BabyAGI framework and demonstrates how to:

- Retrieve available functions (tools) from the BabyAGI function database.
- Convert function input parameters to JSON schema for tool descriptions.
- Use LiteLLM to perform chain-of-thought reasoning with tool calls.
- Execute functions dynamically and feed results back into the reasoning loop.
- Avoid repeated function calls with the same arguments.
- Return a detailed reasoning path and final answer.

### Step-by-Step Explanation of `react_agent`

```python
@func.register_function(
    metadata={
        "description": "An agent that takes an input, plans using LLM, executes actions using functions from display_functions_wrapper(), and continues until the task is complete using chain-of-thought techniques while providing detailed reasoning and function execution steps."
    },
    imports=["litellm", "json", "copy"],
    dependencies=["get_function_wrapper", "execute_function_wrapper", "get_all_functions_wrapper"],
    key_dependencies=["OPENAI_API_KEY"]
)
def react_agent(input_text) -> str:
    ...
```

- **Function Registration:** The function is registered with metadata describing its purpose, imports required, dependencies on other BabyAGI functions, and key dependencies (e.g., OpenAI API key).

- **Mapping Python Types to JSON Schema:** The agent converts Python function parameter types to JSON schema types to describe the tools for LiteLLM.

- **Fetching Available Functions:** It uses `get_all_functions_wrapper()` to get all registered functions, then fetches detailed info for each using `get_function_wrapper()`.

- **Building Tools List:** Constructs a list of tools with their names, descriptions, and parameter schemas for LiteLLM.

- **Chat Context Initialization:** Sets up a system prompt that instructs the LLM to think step-by-step, use functions, and avoid repeated calls.

- **Iterative Reasoning Loop:** Runs up to a maximum number of iterations (default 5), each time:

  - Updating the system prompt with the history of function calls.
  - Calling LiteLLM's completion API with the current chat context and tools.
  - Parsing the response for any function calls.
  - Executing the called functions using `execute_function_wrapper`.
  - Appending function outputs back into the chat context.
  - Continuing until no more function calls are made or max iterations reached.

- **Final Answer Extraction:** Extracts the final answer from the LLM's last message.

- **Return Value:** Returns a detailed string including the full reasoning path, functions used, and the final answer.

---

## Using the API to Create Your Own ReAct Agent

To create a ReAct agent with tool calling using BabyAGI, follow these steps:

1. **Register your functions** with `@babyagi.register_function()` including metadata, dependencies, and key dependencies.

2. **Load necessary function packs** that provide utility functions like `get_function_wrapper`, `execute_function_wrapper`, and `get_all_functions_wrapper`.

3. **Implement your agent function** similar to `react_agent`:

   - Fetch available functions dynamically.
   - Convert function parameters to JSON schema for tool descriptions.
   - Use LiteLLM's `completion` API with the `tools` argument to enable tool calling.
   - Maintain a chat context with system and user messages.
   - Parse LLM responses for tool calls and execute them.
   - Append tool outputs back to the chat context.
   - Iterate until the task is complete or a max iteration count is reached.
   - Return the final answer along with reasoning and function call history.

4. **Add your OpenAI API key** or other keys using `babyagi.add_key_wrapper()`.

5. **Run your agent function** by calling it with an input string describing the task.

---

## Example Usage

Here is a minimal example to run the `react_agent` function:

```python
import babyagi
import os

# Add OpenAI API key
babyagi.add_key_wrapper('openai_api_key', os.environ['OPENAI_API_KEY'])

# Load the draft react_agent function pack
babyagi.load_functions("drafts/react_agent")

# Call the react_agent function with a task description
result = babyagi.react_agent("Find the current weather in New York and summarize it.")

print(result)
```

This will:

- Load the `react_agent` function.
- Use the OpenAI GPT-4 Turbo model via LiteLLM.
- Dynamically call registered functions as tools.
- Provide detailed reasoning and function call outputs.
- Return the final answer.

---

## Additional Notes and Best Practices

- **Function Metadata:** Properly document your functions with descriptions and parameter info to improve tool usability.

- **Key Dependencies:** Ensure all required API keys are added via `add_key_wrapper`.

- **Function Packs:** Use `babyagi.load_functions()` to load function packs that provide useful utilities and plugins.

- **Avoid Infinite Loops:** The `react_agent` limits iterations to prevent infinite reasoning loops.

- **Verbose Logging:** The agent enables verbose logging for LiteLLM to help debug interactions.

- **Error Handling:** The agent catches and reports errors during function execution.

---

## References to Related Functions and Packs

- `babyagi.register_function`: Decorator to register functions with metadata and dependencies.

- `get_function_wrapper`, `execute_function_wrapper`, `get_all_functions_wrapper`: Core utility functions to fetch and execute registered functions.

- `babyagi.load_functions`: Load function packs, e.g., `"drafts/react_agent"`.

- `babyagi.add_key_wrapper`: Add secret keys like OpenAI API keys.

- `babyagi.create_app`: Create a Flask app with BabyAGI dashboard and API.

- Example function pack with tool calling chat: `babyagi/functionz/packs/default/function_calling_chat.py` (similar pattern to `react_agent`).

---

# Summary

The BabyAGI API provides a powerful framework to create ReAct agents with tool calling by:

- Registering functions as tools with metadata.
- Dynamically fetching and describing these tools for the LLM.
- Using LiteLLM's tool calling interface to reason and act iteratively.
- Executing functions and feeding results back into the reasoning loop.
- Returning detailed reasoning and final answers.

The `react_agent` function in the drafts pack is a comprehensive example demonstrating this approach. By following its pattern and using the BabyAGI API functions, you can build your own autonomous agents capable of complex reasoning and tool use.

---

If you need further details or examples, the BabyAGI repository includes multiple example scripts under `examples/` and detailed documentation in the `README.md`.