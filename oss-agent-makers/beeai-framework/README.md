# BeeAI Framework: How to Use the API to Create a ReAct Agent with Tool Calling

This document provides an exhaustive guide on how to use the BeeAI Framework API to create a ReAct (Reasoning and Acting) agent that can call tools dynamically during its operation. The guide is based on the analysis of the BeeAI Framework codebase, focusing on the `ToolCallingAgent` class and related components.

---

## Table of Contents

- [Overview](#overview)
- [Key Components](#key-components)
- [Creating a ToolCallingAgent](#creating-a-toolcallingagent)
- [Running the Agent with Tool Calling](#running-the-agent-with-tool-calling)
- [Observing Agent Events](#observing-agent-events)
- [Example Usage](#example-usage)
- [Detailed API Explanation](#detailed-api-explanation)
- [Additional Notes](#additional-notes)

---

## Overview

The BeeAI Framework provides a `ToolCallingAgent` class designed to create agents capable of reasoning and acting by calling external tools. This agent integrates a language model (LLM), memory management, and a set of tools that it can invoke to accomplish tasks.

The agent operates by maintaining a conversation memory, sending prompts to the LLM, interpreting tool calls from the LLM's responses, executing those tools, and incorporating the results back into the conversation. This loop continues until the agent produces a final answer.

---

## Key Components

- **ToolCallingAgent**: The main agent class that orchestrates the interaction between the LLM, memory, and tools.
- **ChatModel**: The language model interface used by the agent to generate responses.
- **Tools**: External functionalities the agent can call, e.g., weather tools, search tools.
- **Memory**: Stores conversation history and intermediate states.
- **Emitter**: Event system to observe agent lifecycle events.
- **Prompts**: Templates guiding the system and task instructions.

---

## Creating a ToolCallingAgent

To create a `ToolCallingAgent`, you need to provide:

- An instance of a `ChatModel` (LLM).
- A memory instance (e.g., `TokenMemory`).
- An array of tools the agent can use.

Optionally, you can provide metadata, custom prompt templates, execution configuration, and control whether to save intermediate steps.

### Example Initialization

```typescript
import { ToolCallingAgent } from "beeai-framework/agents/toolCalling/agent";
import { OllamaChatModel } from "beeai-framework/adapters/ollama/backend/chat";
import { TokenMemory } from "beeai-framework/memory/tokenMemory";
import { OpenMeteoTool } from "beeai-framework/tools/weather/openMeteo";

const llm = new OllamaChatModel("llama3.1");
const memory = new TokenMemory();
const tools = [new OpenMeteoTool()];

const agent = new ToolCallingAgent({
  llm,
  memory,
  tools,
  saveIntermediateSteps: true, // optional, defaults to true
});
```

---

## Running the Agent with Tool Calling

The agent is run by calling its `run` method with a prompt and optional context or expected output schema.

The agent internally:

- Initializes conversation memory with system and user messages.
- Iteratively calls the LLM to get responses.
- Detects tool calls in the LLM response.
- Executes the corresponding tools and adds tool results to memory.
- Handles retries and errors.
- Produces a final answer wrapped in a special tool call.

### Running Example

```typescript
const response = await agent.run({ prompt: "What's the weather like in Paris?" });
console.log("Agent response:", response.result.text);
```

---

## Observing Agent Events

The `run` method returns an observable that emits events during the agent's lifecycle. You can listen to events such as `start` and `success` to track progress and intermediate states.

### Example of Observing Events

```typescript
const response = await agent.run({ prompt: "Tell me the weather." }).observe((emitter) => {
  emitter.on("success", ({ state }) => {
    const newMessages = state.memory.messages.slice(previousCount);
    previousCount += newMessages.length;
    console.log("New messages:", newMessages.map(msg => msg.toPlain()));
  });
});
```

---

## Example Usage: Interactive Console Agent

The following example demonstrates a complete interactive console application using the `ToolCallingAgent` with a weather tool and an Ollama LLM model.

```typescript
import "dotenv/config.js";
import { createConsoleReader } from "../../helpers/io.js";
import { Logger } from "beeai-framework/logger/logger";
import { TokenMemory } from "beeai-framework/memory/tokenMemory";
import { OpenMeteoTool } from "beeai-framework/tools/weather/openMeteo";
import { OllamaChatModel } from "beeai-framework/adapters/ollama/backend/chat";
import { ToolCallingAgent } from "beeai-framework/agents/toolCalling/agent";

Logger.root.level = "silent"; // disable internal logs
const logger = new Logger({ name: "app", level: "trace" });

const llm = new OllamaChatModel("llama3.1");
const agent = new ToolCallingAgent({
  llm,
  memory: new TokenMemory(),
  tools: [new OpenMeteoTool()],
});

const reader = createConsoleReader();

try {
  for await (const { prompt } of reader) {
    let messagesCount = agent.memory.messages.length + 1;

    const response = await agent.run({ prompt }).observe((emitter) => {
      emitter.on("success", async ({ state }) => {
        const newMessages = state.memory.messages.slice(messagesCount);
        messagesCount += newMessages.length;

        reader.write(
          `Agent (${newMessages.length} new messages) 🤖 :\n`,
          newMessages.map((msg) => `-> ${JSON.stringify(msg.toPlain())}`).join("\n"),
        );
      });
    });

    reader.write(`Agent 🤖 : `, response.result.text);
  }
} catch (error) {
  logger.error(error);
} finally {
  reader.close();
}
```

This example uses a console reader helper to interactively read user input and display agent responses and intermediate messages.

---

## Detailed API Explanation

### ToolCallingAgent Class

- **Constructor Input (`ToolCallingAgentInput`)**:
  - `llm: ChatModel` - The language model instance.
  - `memory: BaseMemory` - Memory instance to store conversation.
  - `tools: AnyTool[]` - Array of tools the agent can call.
  - `meta?: AgentMeta` - Optional metadata about the agent.
  - `templates?: Partial<ToolCallingAgentTemplates>` - Optional prompt template overrides.
  - `execution?: ToolCallingAgentExecutionConfig` - Execution parameters like max retries.
  - `saveIntermediateSteps?: boolean` - Whether to save all intermediate messages (default true).

- **Run Method (`_run`)**:
  - Accepts `ToolCallingAgentRunInput` with:
    - `prompt?: string` - User prompt.
    - `context?: string` - Additional context.
    - `expectedOutput?: string | ZodSchema` - Expected output format or schema.
  - Accepts `ToolCallingAgentRunOptions` with:
    - `signal?: AbortSignal` - For cancellation.
    - `execution?: ToolCallingAgentExecutionConfig` - Override execution config.
  - Returns `ToolCallingAgentRunOutput`:
    - `result: AssistantMessage` - Final answer message.
    - `memory: BaseMemory` - Final memory state.

- **Execution Flow**:
  - Initializes memory with system prompt and previous messages.
  - Adds user prompt as a task message.
  - Iteratively calls LLM to generate responses.
  - Detects tool calls and executes them, adding results to memory.
  - Handles retries and errors with counters.
  - Supports fallback to plain text final answer if structured tool calls are unsupported.
  - Emits lifecycle events (`start`, `success`) via an `Emitter`.
  - Saves intermediate steps to memory if enabled.

- **Meta Information**:
  - Provides agent metadata including tool descriptions.

- **Templates**:
  - Uses default or overridden prompt templates for system and task instructions.

---

## Additional Notes

- The agent supports dynamic tool calling with error handling and retries.
- Tools must implement the `AnyTool` interface and provide a `run` method.
- The framework supports observing detailed events for debugging or UI updates.
- The example uses `OllamaChatModel` but other models can be used.
- Memory implementations like `TokenMemory` or `UnconstrainedMemory` can be swapped.
- The console reader helper (`createConsoleReader`) facilitates interactive CLI usage.

---

# Summary

To create a ReAct agent with tool calling using the BeeAI Framework:

1. Instantiate a language model (`ChatModel`).
2. Prepare a memory instance.
3. Create or select tools implementing the `AnyTool` interface.
4. Instantiate `ToolCallingAgent` with the above.
5. Use the `run` method with a prompt to execute the agent.
6. Optionally observe events for intermediate states.
7. Integrate into your application or CLI as needed.

This approach enables building powerful agents that can reason, call external tools, and provide informed responses dynamically.

---

If you need further details on specific classes or methods, please ask!