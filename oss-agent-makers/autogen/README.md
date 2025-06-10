# How to Use the Microsoft AutoGen API to Create a ReAct Agent with Tool Calling

This document provides an exhaustive guide on how to use the Microsoft AutoGen API (specifically the .NET SDK) to create a ReAct (Reasoning + Acting) agent that can call external tools during its reasoning process.

---

## Overview

The ReAct agent pattern allows an AI agent to interleave reasoning steps with actions (tool calls) to solve complex tasks. This package provides a way to create such an agent by combining:

- A **reasoner** agent that generates reasoning steps.
- An **actor** agent that executes tool calls based on the reasoning.
- A **helper** agent for auxiliary tasks like extracting questions or summarizing.

The agent uses a prompt template to guide the reasoning and tool invocation process, and it supports multiple tools registered with function contracts and executors.

---

## Key Components

### 1. `OpenAIReActAgent` Class

This is the main class implementing the ReAct agent pattern.

- **Constructor Parameters:**
  - `ChatClient client`: The OpenAI chat client used for LLM interactions.
  - `string name`: The agent's name.
  - `FunctionContract[] tools`: Array of tools the agent can invoke.
  - `Dictionary<string, Func<string, Task<string>>> toolExecutors`: Mapping from tool names to async functions that execute the tool logic.

- **Internal Agents:**
  - `reasoner`: An `OpenAIChatAgent` that generates reasoning steps.
  - `actor`: An `OpenAIChatAgent` that executes tool calls using a `FunctionCallMiddleware`.
  - `helper`: An `OpenAIChatAgent` used for auxiliary tasks like extracting questions and summarizing.

- **Main Method:**
  - `GenerateReplyAsync`: The method that drives the ReAct loop.
    - Extracts the user question from chat history.
    - Creates a ReAct prompt with tool descriptions.
    - Iteratively:
      - Sends the current chat history to the reasoner to get reasoning.
      - Checks if the final answer is found.
      - Sends the reasoning to the actor to perform tool calls.
    - If no final answer after max steps, summarizes the chat history.

- **Prompt Template:**
  The prompt instructs the agent to answer questions by invoking tools in a structured format:
  ```
  Question: the input question you must answer
  Thought: you should always think about what to do
  Tool: the tool to invoke
  Tool Input: the input to the tool
  Observation: the invoke result of the tool
  ...
  Thought: I now know the final answer
  Final Answer: the final answer to the original input question
  ```

---

## Example Code Snippet

```csharp
public class OpenAIReActAgent : IAgent
{
    private readonly ChatClient _client;
    private readonly FunctionContract[] tools;
    private readonly Dictionary<string, Func<string, Task<string>>> toolExecutors = new();
    private readonly IAgent reasoner;
    private readonly IAgent actor;
    private readonly IAgent helper;
    private readonly int maxSteps = 10;

    private const string ReActPrompt = @"
Answer the following questions as best you can.
You can invoke the following tools:
{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Tool: the tool to invoke
Tool Input: the input to the tool
Observation: the invoke result of the tool
... (this process can repeat multiple times)

Once you have the final answer, provide the final answer in the following format:
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!
Question: {input}";

    public OpenAIReActAgent(ChatClient client, string name, FunctionContract[] tools, Dictionary<string, Func<string, Task<string>>> toolExecutors)
    {
        _client = client;
        this.Name = name;
        this.tools = tools;
        this.toolExecutors = toolExecutors;
        this.reasoner = CreateReasoner();
        this.actor = CreateActor();
        this.helper = new OpenAIChatAgent(client, "helper")
            .RegisterMessageConnector();
    }

    public string Name { get; }

    public async Task<IMessage> GenerateReplyAsync(IEnumerable<IMessage> messages, GenerateReplyOptions? options = null, CancellationToken cancellationToken = default)
    {
        // Extract the input question
        var userQuestion = await helper.SendAsync("Extract the question from chat history", chatHistory: messages);
        if (userQuestion.GetContent() is not string question)
        {
            return new TextMessage(Role.Assistant, "I couldn't find a question in the chat history. Please ask a question.", from: Name);
        }
        var reactPrompt = CreateReActPrompt(question);
        var promptMessage = new TextMessage(Role.User, reactPrompt);
        var chatHistory = new List<IMessage>() { promptMessage };

        // ReAct loop
        for (int i = 0; i != this.maxSteps; i++)
        {
            // Reasoning step
            var reasoning = await reasoner.SendAsync(chatHistory: chatHistory);
            if (reasoning.GetContent() is not string reasoningContent)
            {
                return new TextMessage(Role.Assistant, "I couldn't find a reasoning in the chat history. Please provide a reasoning.", from: Name);
            }
            if (reasoningContent.Contains("I now know the final answer"))
            {
                return new TextMessage(Role.Assistant, reasoningContent, from: Name);
            }

            chatHistory.Add(reasoning);

            // Action step (tool call)
            var action = await actor.SendAsync(reasoning);
            chatHistory.Add(action);
        }

        // If no final answer, summarize chat history
        var summary = await helper.SendAsync("Summarize the chat history and find out what's missing", chatHistory: chatHistory);
        summary.From = Name;

        return summary;
    }

    private string CreateReActPrompt(string input)
    {
        var toolPrompt = tools.Select(t => $"{t.Name}: {t.Description}").Aggregate((a, b) => $"{a}\n{b}");
        var prompt = ReActPrompt.Replace("{tools}", toolPrompt);
        prompt = prompt.Replace("{input}", input);
        return prompt;
    }

    private IAgent CreateReasoner()
    {
        return new OpenAIChatAgent(
            chatClient: _client,
            name: "reasoner")
            .RegisterMessageConnector()
            .RegisterPrintMessage();
    }

    private IAgent CreateActor()
    {
        var functionCallMiddleware = new FunctionCallMiddleware(tools, toolExecutors);
        return new OpenAIChatAgent(
            chatClient: _client,
            name: "actor")
            .RegisterMessageConnector()
            .RegisterMiddleware(functionCallMiddleware)
            .RegisterPrintMessage();
    }
}
```

---

## Defining Tools

Tools are defined as methods with the `[Function]` attribute. Each tool has a corresponding `FunctionContract` and an executor wrapper function.

Example tools:

```csharp
public partial class Tools
{
    [Function]
    public async Task<string> WeatherReport(string city, string date)
    {
        return $"Weather report for {city} on {date} is sunny";
    }

    [Function]
    public async Task<string> GetLocalization(string dummy)
    {
        return $"Paris";
    }

    [Function]
    public async Task<string> GetDateToday(string dummy)
    {
        return $"27/05/2024";
    }
}
```

---

## How to Instantiate and Use the ReAct Agent

Example usage:

```csharp
public class Example17_ReActAgent
{
    public static async Task RunAsync()
    {
        var openAIKey = Environment.GetEnvironmentVariable("OPENAI_API_KEY") ?? throw new Exception("Please set OPENAI_API_KEY environment variable.");
        var modelName = "gpt-4-turbo";
        var tools = new Tools();
        var openAIClient = new OpenAIClient(openAIKey);
        var reactAgent = new OpenAIReActAgent(
            client: openAIClient.GetChatClient(modelName),
            name: "react-agent",
            tools: new FunctionContract[] { tools.GetLocalizationFunctionContract, tools.GetDateTodayFunctionContract, tools.WeatherReportFunctionContract },
            toolExecutors: new Dictionary<string, Func<string, Task<string>>>
            {
                { tools.GetLocalizationFunctionContract.Name, tools.GetLocalizationWrapper },
                { tools.GetDateTodayFunctionContract.Name, tools.GetDateTodayWrapper },
                { tools.WeatherReportFunctionContract.Name, tools.WeatherReportWrapper },
            }
        )
        .RegisterPrintMessage();

        var message = new TextMessage(Role.User, "What is the weather here", from: "user");

        var response = await reactAgent.SendAsync(message);
        // Use the response as needed
    }
}
```

---

## Summary of Steps to Create a ReAct Agent with Tool Calling

1. **Define your tools** as async methods with `[Function]` attribute and provide function contracts and executor wrappers.

2. **Create an OpenAI chat client** with your API key and model name.

3. **Instantiate the `OpenAIReActAgent`** with:
   - The chat client.
   - A name for the agent.
   - The array of tool function contracts.
   - A dictionary mapping tool names to executor functions.

4. **Call `GenerateReplyAsync` or `SendAsync`** on the agent with user messages to get responses.

5. The agent will:
   - Extract the question.
   - Use the reasoner to think.
   - Use the actor to call tools.
   - Repeat until a final answer is found or max steps reached.
   - Return the final answer or a summary.

---

## Additional Notes

- The `FunctionCallMiddleware` is used in the actor agent to intercept reasoning outputs and execute the corresponding tool calls.

- The prompt template is customizable to guide the agent's reasoning and tool invocation format.

- The helper agent is used for auxiliary tasks like extracting questions from chat history and summarizing.

- The example uses OpenAI GPT-4 Turbo as the underlying LLM, but other models supported by the `ChatClient` can be used.

---

This detailed explanation and example code should enable you to create and use a ReAct agent with tool calling using the Microsoft AutoGen API in .NET. For more advanced usage, explore the other samples and documentation in the package.