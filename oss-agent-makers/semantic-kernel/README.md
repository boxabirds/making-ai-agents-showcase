# How to Use the Microsoft Semantic Kernel API to Create a ReAct Agent with Tool Calling

This document provides an exhaustive, detailed guide on how to use the Microsoft Semantic Kernel API to create a ReAct (Reasoning and Acting) agent with tool calling capabilities. The analysis is based on the official sample `Step04_KernelFunctionStrategies.cs` from the Semantic Kernel repository, which demonstrates advanced agent orchestration using kernel function strategies.

---

## Overview

The Semantic Kernel API allows you to create intelligent agents that can reason and act by invoking tools (functions) dynamically during a conversation or task execution. The key components involved in creating a ReAct agent with tool calling are:

- **Agents**: Represent AI personas or roles with specific instructions and capabilities.
- **AgentGroupChat**: Manages multi-agent conversations and orchestrates turn-taking.
- **KernelFunctionTerminationStrategy**: Defines when the agent conversation or task should terminate based on a kernel function.
- **KernelFunctionSelectionStrategy**: Defines how to select the next agent to act based on a kernel function.
- **KernelFunction**: Represents a prompt-based function that can be invoked by the kernel.
- **ChatHistoryTruncationReducer**: Limits the chat history size to optimize token usage.
- **ChatMessageContent**: Represents messages exchanged in the chat.

---

## Step-by-Step Guide to Create a ReAct Agent with Tool Calling

### 1. Define Agents with Instructions and Kernel

Agents are defined with a name, instructions (persona), and a kernel instance that provides the AI capabilities (e.g., chat completion).

```csharp
ChatCompletionAgent agentReviewer = new()
{
    Instructions = ReviewerInstructions,
    Name = ReviewerName,
    Kernel = this.CreateKernelWithChatCompletion(useChatClient, out var chatClient1),
};

ChatCompletionAgent agentWriter = new()
{
    Instructions = CopyWriterInstructions,
    Name = CopyWriterName,
    Kernel = this.CreateKernelWithChatCompletion(useChatClient, out var chatClient2),
};
```

- `ReviewerInstructions` and `CopyWriterInstructions` are prompt instructions defining the role and behavior of each agent.
- `CreateKernelWithChatCompletion` is a helper method to create a kernel with chat completion capabilities, optionally returning a chat client.

### 2. Create Kernel Functions for Termination and Selection Strategies

Kernel functions are prompt-based functions used to decide when to terminate the conversation and which agent should act next.

```csharp
KernelFunction terminationFunction = AgentGroupChat.CreatePromptFunctionForStrategy(
    """
    Determine if the copy has been approved.  If so, respond with a single word: yes

    History:
    {{$history}}
    """,
    safeParameterNames: "history");

KernelFunction selectionFunction = AgentGroupChat.CreatePromptFunctionForStrategy(
    $$$"""
    Determine which participant takes the next turn in a conversation based on the most recent participant.
    State only the name of the participant to take the next turn.
    No participant should take more than one turn in a row.

    Choose only from these participants:
    - {{{ReviewerName}}}
    - {{{CopyWriterName}}}

    Always follow these rules when selecting the next participant:
    - After {{{CopyWriterName}}}, it is {{{ReviewerName}}}'s turn.
    - After {{{ReviewerName}}}, it is {{{CopyWriterName}}}'s turn.

    History:
    {{$history}}
    """,
    safeParameterNames: "history");
```

- The termination function checks if the conversation should end (e.g., if the copy is approved).
- The selection function decides which agent should speak next based on the conversation history.

### 3. Use a ChatHistoryTruncationReducer to Limit History Size

To optimize token usage and performance, limit the chat history used in the strategies to the most recent message.

```csharp
ChatHistoryTruncationReducer strategyReducer = new(1);
```

### 4. Create an AgentGroupChat with Execution Settings

The `AgentGroupChat` manages the conversation between multiple agents and uses the termination and selection strategies.

```csharp
AgentGroupChat chat = new(agentWriter, agentReviewer)
{
    ExecutionSettings = new()
    {
        TerminationStrategy = new KernelFunctionTerminationStrategy(terminationFunction, CreateKernelWithChatCompletion())
        {
            Agents = [agentReviewer], // Only the reviewer can approve
            ResultParser = (result) => result.GetValue<string>()?.Contains("yes", StringComparison.OrdinalIgnoreCase) ?? false,
            HistoryVariableName = "history",
            MaximumIterations = 10,
            HistoryReducer = strategyReducer,
        },
        SelectionStrategy = new KernelFunctionSelectionStrategy(selectionFunction, CreateKernelWithChatCompletion())
        {
            InitialAgent = agentWriter,
            ResultParser = (result) => result.GetValue<string>() ?? CopyWriterName,
            HistoryVariableName = "history",
            HistoryReducer = strategyReducer,
            EvaluateNameOnly = true,
        },
    }
};
```

- `TerminationStrategy` uses the termination function to decide when to stop.
- `SelectionStrategy` uses the selection function to pick the next agent.
- `MaximumIterations` limits the number of turns.
- `HistoryReducer` reduces the history size for efficiency.
- `EvaluateNameOnly` in selection strategy means only agent names are considered, not full messages.

### 5. Add Initial User Message and Invoke the Chat

Add the initial user message to the chat and invoke the conversation asynchronously.

```csharp
ChatMessageContent message = new(AuthorRole.User, "concept: maps made out of egg cartons.");
chat.AddChatMessage(message);
this.WriteAgentChatMessage(message);

await foreach (ChatMessageContent response in chat.InvokeAsync())
{
    this.WriteAgentChatMessage(response);
}

Console.WriteLine($"\n[IS COMPLETED: {chat.IsComplete}]");
```

- `ChatMessageContent` represents a message with an author role and content.
- `InvokeAsync` runs the conversation, yielding responses from agents.
- `IsComplete` indicates if the conversation ended per the termination strategy.

### 6. Dispose of Chat Clients

Dispose of any chat clients created during kernel initialization to release resources.

```csharp
chatClient1?.Dispose();
chatClient2?.Dispose();
```

---

## Summary of Key Classes and Methods

| Class/Method                          | Description                                                                                  |
|-------------------------------------|----------------------------------------------------------------------------------------------|
| `ChatCompletionAgent`                | Defines an AI agent with instructions and a kernel for chat completion.                      |
| `AgentGroupChat`                    | Manages multi-agent chat with execution, termination, and selection strategies.              |
| `KernelFunction`                    | Represents a prompt-based function used for decision-making in strategies.                   |
| `KernelFunctionTerminationStrategy`| Strategy to terminate chat based on kernel function evaluation.                              |
| `KernelFunctionSelectionStrategy`  | Strategy to select the next agent based on kernel function evaluation.                       |
| `ChatHistoryTruncationReducer`      | Reduces chat history size to optimize token usage.                                          |
| `ChatMessageContent`                | Represents a chat message with author role and content.                                     |
| `InvokeAsync()`                    | Asynchronously runs the chat conversation, yielding agent responses.                         |

---

## How This Enables ReAct Agent with Tool Calling

- The **ReAct pattern** involves reasoning (via LLM prompts) and acting (invoking tools/functions).
- The `KernelFunctionSelectionStrategy` can be extended to select tools or agents dynamically based on the conversation context.
- The `KernelFunctionTerminationStrategy` can decide when the agent has completed its task.
- By defining agents with specific tool capabilities (via their kernel functions), the `AgentGroupChat` orchestrates tool calling as part of the conversation.
- The prompt-based kernel functions act as the reasoning engine to decide actions and termination.

---

## Additional Notes

- The sample uses C# and the .NET Semantic Kernel SDK.
- The `CreateKernelWithChatCompletion` method is a helper to create a kernel configured with a chat completion service (e.g., OpenAI, Azure OpenAI).
- The `WriteAgentChatMessage` method is a helper to output messages for demonstration.
- The approach is flexible and can be adapted to more agents, different tools, and more complex strategies.

---

# Example Code Snippet (Simplified)

```csharp
// Define agents
var agent1 = new ChatCompletionAgent { Name = "Agent1", Instructions = "...", Kernel = kernel1 };
var agent2 = new ChatCompletionAgent { Name = "Agent2", Instructions = "...", Kernel = kernel2 };

// Define termination and selection functions
var terminationFunc = AgentGroupChat.CreatePromptFunctionForStrategy("...termination prompt...", "history");
var selectionFunc = AgentGroupChat.CreatePromptFunctionForStrategy("...selection prompt...", "history");

// Create strategies
var terminationStrategy = new KernelFunctionTerminationStrategy(terminationFunc, kernel1) { ... };
var selectionStrategy = new KernelFunctionSelectionStrategy(selectionFunc, kernel1) { ... };

// Create agent group chat
var chat = new AgentGroupChat(agent1, agent2)
{
    ExecutionSettings = new()
    {
        TerminationStrategy = terminationStrategy,
        SelectionStrategy = selectionStrategy,
    }
};

// Add initial user message
chat.AddChatMessage(new ChatMessageContent(AuthorRole.User, "Your input here"));

// Run chat
await foreach (var response in chat.InvokeAsync())
{
    Console.WriteLine(response.Content);
}
```

---

# Conclusion

The Microsoft Semantic Kernel API provides a powerful framework to create ReAct agents with tool calling by leveraging kernel functions for dynamic agent selection and termination strategies. Using `AgentGroupChat` with `KernelFunctionTerminationStrategy` and `KernelFunctionSelectionStrategy`, you can orchestrate multi-agent conversations that reason and act intelligently, invoking tools as needed.

For detailed usage, refer to the sample `Step04_KernelFunctionStrategies.cs` in the Semantic Kernel repository, which demonstrates these concepts in a practical scenario.

---

If you need further details or examples on specific parts of the API or other samples, please ask!