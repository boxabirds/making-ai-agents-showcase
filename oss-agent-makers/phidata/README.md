# How to Use the PhiData API to Create a ReAct Agent with Tool Calling

This document provides an exhaustive guide on how to use the PhiData API to create a ReAct (Reasoning and Acting) agent that can call external tools during its reasoning process. The guide is based on the analysis of the PhiData codebase, specifically focusing on how agents are constructed with tools and how tool calls are integrated into the agent's workflow.

---

## Table of Contents

- [Overview](#overview)
- [Key Concepts](#key-concepts)
- [Creating an Agent with Tools](#creating-an-agent-with-tools)
- [Example: AI News Reporter Agent](#example-ai-news-reporter-agent)
- [Agent Configuration Parameters](#agent-configuration-parameters)
- [Using Tools in the Agent](#using-tools-in-the-agent)
- [Running the Agent](#running-the-agent)
- [Additional Notes](#additional-notes)
- [Summary](#summary)

---

## Overview

The PhiData API provides a flexible framework to create AI agents that can reason and act by calling external tools. These agents are built on top of language models and can be enhanced with various tools to extend their capabilities, such as web search, database queries, or custom APIs.

The ReAct pattern involves the agent reasoning about a problem, deciding to call a tool to gather information or perform an action, and then using the tool's output to continue reasoning or produce a final response.

---

## Key Concepts

- **Agent**: The core AI entity that uses a language model to process instructions and interact with tools.
- **Model**: The underlying language model used by the agent (e.g., OpenAI GPT-4).
- **Tools**: External capabilities or APIs that the agent can call to perform specific tasks or fetch information.
- **Instructions**: The prompt or guidelines that shape the agent's behavior and personality.
- **Tool Calls**: The mechanism by which the agent invokes tools during its reasoning process.

---

## Creating an Agent with Tools

To create a ReAct agent with tool calling using the PhiData API, you typically:

1. **Import the necessary classes** from the PhiData API:
   - `Agent` class to create the agent.
   - A language model class (e.g., `OpenAIChat`).
   - Tool classes that provide external capabilities.

2. **Instantiate the language model** with the desired model ID.

3. **Define the agent's instructions** to guide its behavior and how it should use tools.

4. **Create instances of the tools** you want the agent to use.

5. **Create the agent** by passing the model, instructions, and tools.

6. **Use the agent to process queries**, optionally streaming the response and showing tool calls.

---

## Example: AI News Reporter Agent

The following example is adapted from the file `cookbook/getting_started/02_agent_with_tools.py` and demonstrates how to create an AI news reporter agent that uses a web search tool (DuckDuckGo) to fetch real-time news and respond with a distinctive personality.

```python
from textwrap import dedent

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools

# Create a News Reporter Agent with a fun personality
agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    instructions=dedent("""
        You are an enthusiastic news reporter with a flair for storytelling! 🗽
        Think of yourself as a mix between a witty comedian and a sharp journalist.

        Follow these guidelines for every report:
        1. Start with an attention-grabbing headline using relevant emoji
        2. Use the search tool to find current, accurate information
        3. Present news with authentic NYC enthusiasm and local flavor
        4. Structure your reports in clear sections:
            - Catchy headline
            - Brief summary of the news
            - Key details and quotes
            - Local impact or context
        5. Keep responses concise but informative (2-3 paragraphs max)
        6. Include NYC-style commentary and local references
        7. End with a signature sign-off phrase

        Sign-off examples:
        - 'Back to you in the studio, folks!'
        - 'Reporting live from the city that never sleeps!'
        - 'This is [Your Name], live from the heart of Manhattan!'

        Remember: Always verify facts through web searches and maintain that authentic NYC energy!
    """),
    tools=[DuckDuckGoTools()],
    show_tool_calls=True,
    markdown=True,
)

# Example usage
agent.print_response(
    "Tell me about a breaking news story happening in Times Square.", stream=True
)
```

### Explanation

- The agent uses the `OpenAIChat` model with the ID `"gpt-4o"`.
- The instructions define the agent's personality and how it should use the search tool.
- The `DuckDuckGoTools` is passed as the tool, enabling the agent to perform web searches.
- `show_tool_calls=True` enables logging or displaying the tool calls made by the agent.
- `markdown=True` formats the output in markdown for better readability.
- The `print_response` method is used to send a query to the agent and stream the response.

---

## Agent Configuration Parameters

When creating an `Agent` instance, the following parameters are commonly used:

- `model`: The language model instance (e.g., `OpenAIChat`).
- `instructions`: A string with detailed instructions or prompt for the agent.
- `tools`: A list of tool instances that the agent can call.
- `show_tool_calls`: Boolean to enable showing tool call details.
- `markdown`: Boolean to enable markdown formatting in responses.
- Other optional parameters may exist depending on the API version.

---

## Using Tools in the Agent

Tools are external capabilities that the agent can invoke during its reasoning process. The PhiData API provides many pre-built tools (e.g., DuckDuckGo search, SQL tools, Python execution tools) and supports custom tools.

- Tools are passed as a list to the `Agent` constructor.
- The agent's instructions should guide when and how to use these tools.
- The agent internally manages tool calling and integrates tool outputs into its reasoning.
- Tool calls can be shown or logged for transparency and debugging.

---

## Running the Agent

To run the agent:

1. Instantiate the agent as shown above.
2. Use methods like `agent.print_response()` or `agent.run()` to send queries.
3. Optionally enable streaming to get partial outputs as the agent generates them.
4. Observe tool calls if enabled to understand how the agent interacts with tools.

---

## Additional Notes

- The PhiData API supports many models and tools; you can swap out the model or add multiple tools as needed.
- The agent can be customized with different instructions to change its behavior and personality.
- The API supports advanced features like memory, knowledge bases, and multi-agent teams, but the basic ReAct with tool calling is as shown.
- For asynchronous or more complex workflows, explore other examples in the `cookbook` directory.

---

## Summary

Using the PhiData API, you can create a ReAct agent with tool calling by:

- Importing the `Agent` class and a language model.
- Defining clear instructions that include how to use tools.
- Passing a list of tool instances to the agent.
- Running the agent with queries and optionally streaming responses.
- Enabling tool call visibility for debugging and transparency.

The example in `cookbook/getting_started/02_agent_with_tools.py` provides a concrete, ready-to-run demonstration of an AI news reporter agent that uses the DuckDuckGo search tool to fetch real-time information and respond with a lively personality.

---

If you need further details on specific tools or advanced agent configurations, the PhiData codebase contains many examples and tool implementations under the `cookbook/tools` and `cookbook/agents_from_scratch` directories.