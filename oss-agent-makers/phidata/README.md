# Guide to Creating a Python ReAct Agent with Tool Calling Using the `phidata` API

This document provides an exhaustive, detailed guide on how to use the `phidata` package API to create an agent that can be run directly in Python (e.g., `python agent.py`). It specifically addresses how to create a Python ReAct agent with tool calling capabilities, leveraging the package's built-in scaffolding and tools.

---

## 1. Overview of the API and Key Concepts

The `phidata` package (imported as `agno` in code) provides a modular framework to create AI agents with integrated tool usage. The core components relevant to agent creation are:

- **Agent**: The main class representing an AI agent that can interact with models and tools.
- **Models**: Language models (e.g., OpenAIChat, Claude) that power the agent's reasoning and responses.
- **Tools**: External capabilities or APIs the agent can call to fetch information or perform actions.
- **Instructions**: Text prompts or guidelines that shape the agent's behavior and personality.
- **Tool Calling**: The ability for the agent to invoke tools dynamically during interaction.

---

## 2. Creating and Running an Agent in Python

### Minimal Example: Agent with Tools

The simplest way to create an agent with tool calling is to instantiate the `Agent` class with a model and a list of tools. Then, you can call the agent's method to get responses.

Example from `cookbook/examples/agents/agent_with_tools.py`:

```python
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.tools.yfinance import YFinanceTools

agent = Agent(
    model=Claude(id="claude-3-7-sonnet-latest"),
    tools=[YFinanceTools(stock_price=True)],
    markdown=True,
)

agent.print_response("What is the stock price of Apple?", stream=True)
```

- **Model**: Here, `Claude` is used with a specific model ID.
- **Tools**: `YFinanceTools` is included to enable stock price queries.
- **Output**: The agent prints a markdown-formatted response, streaming output.

To run this example, save it as `agent.py` and execute:

```bash
python agent.py
```

---

## 3. Creating a ReAct Agent with Tool Calling

ReAct (Reasoning + Acting) agents combine reasoning with the ability to call external tools dynamically during the conversation. The `phidata` API supports this pattern by allowing you to:

- Define an agent with a language model.
- Provide a set of tools the agent can call.
- Supply instructions that guide the agent's reasoning and tool usage.
- Enable tool call visibility and markdown formatting for clarity.

### Detailed Example: AI News Reporter Agent

From `cookbook/getting_started/02_agent_with_tools.py`:

```python
from textwrap import dedent
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools

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

agent.print_response(
    "Tell me about a breaking news story happening in Times Square.", stream=True
)
```

**Key points:**

- The agent uses the `OpenAIChat` model with a GPT-4 variant.
- The `DuckDuckGoTools` tool is provided for web search capabilities.
- Instructions explicitly guide the agent's reasoning and tool usage.
- `show_tool_calls=True` enables logging of tool invocations.
- `markdown=True` formats the output nicely.
- The agent's `print_response` method supports streaming output.

---

## 4. Using Custom Tool Functions with Agents

You can also define custom tool functions that the agent can call. These functions can access the agent's context and perform arbitrary logic.

Example from `cookbook/tools/tool_calls_accesing_agent.py`:

```python
import json
import httpx
from agno.agent import Agent

def get_top_hackernews_stories(agent: Agent) -> str:
    num_stories = agent.context.get("num_stories", 5) if agent.context else 5

    # Fetch top story IDs
    response = httpx.get("https://hacker-news.firebaseio.com/v0/topstories.json")
    story_ids = response.json()

    # Fetch story details
    stories = []
    for story_id in story_ids[:num_stories]:
        story_response = httpx.get(
            f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
        )
        story = story_response.json()
        if "text" in story:
            story.pop("text", None)
        stories.append(story)
    return json.dumps(stories)

agent = Agent(
    context={
        "num_stories": 3,
    },
    tools=[get_top_hackernews_stories],
    markdown=True,
    show_tool_calls=True,
)

agent.print_response("What are the top hackernews stories?", stream=True)
```

- The tool function `get_top_hackernews_stories` is passed as a callable in the `tools` list.
- The agent can call this function dynamically during interaction.
- The agent context can be used to pass parameters to the tool.

---

## 5. Summary of Steps to Create a Python ReAct Agent with Tool Calling

1. **Install dependencies** (if not already installed):

   ```bash
   pip install openai duckduckgo-search agno httpx
   ```

2. **Import necessary classes and tools**:

   - `Agent` from `agno.agent`
   - Language model class (e.g., `OpenAIChat`, `Claude`) from `agno.models`
   - Tools from `agno.tools` or custom tool functions

3. **Define instructions** (optional but recommended) to guide agent behavior.

4. **Create the agent instance** with:

   - `model`: The language model instance.
   - `tools`: List of tool instances or callable functions.
   - `instructions`: Text prompt guiding the agent.
   - `show_tool_calls`: Boolean to enable tool call logging.
   - `markdown`: Boolean to enable markdown output formatting.

5. **Invoke the agent** using `agent.print_response()` or similar methods, optionally with streaming.

6. **Run the script** directly with Python:

   ```bash
   python agent.py
   ```

---

## 6. Additional References and Resources

- **Source code examples:**

  - Agent with tools example:  
    `cookbook/getting_started/02_agent_with_tools.py`  
    (Shows a ReAct style agent with web search tool)

  - Custom tool function example:  
    `cookbook/tools/tool_calls_accesing_agent.py`  
    (Shows how to define and use custom tool functions)

  - Minimal agent with tools example:  
    `cookbook/examples/agents/agent_with_tools.py`

- **API classes:**

  - `Agent` class: `agno.agent.Agent`  
    (Core agent class to instantiate and run agents)

  - Models: e.g., `agno.models.openai.OpenAIChat`, `agno.models.anthropic.Claude`  
    (Language model wrappers)

  - Tools: e.g., `agno.tools.duckduckgo.DuckDuckGoTools`, `agno.tools.yfinance.YFinanceTools`  
    (Prebuilt tools for external API calls)

- **Online documentation:**  
  The package likely has online docs at [https://phidata.ai](https://phidata.ai) or GitHub repository (not provided here). Check for README and docs for more detailed usage.

---

## 7. Example Agent Script for ReAct with Tool Calling

Save the following as `agent.py` and run with `python agent.py`:

```python
from textwrap import dedent
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools

def main():
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

            Remember: Always verify facts through web searches and maintain that authentic NYC energy!
        """),
        tools=[DuckDuckGoTools()],
        show_tool_calls=True,
        markdown=True,
    )

    agent.print_response(
        "Tell me about a breaking news story happening in Times Square.", stream=True
    )

if __name__ == "__main__":
    main()
```

---

# Conclusion

The `phidata` package provides a straightforward and powerful API to create Python agents with ReAct capabilities and tool calling. By combining language models, tools, and clear instructions, you can build agents that reason and act dynamically. The package also supports custom tool functions and streaming responses, making it flexible for various use cases.

Use the provided example scripts as scaffolds to quickly build your own agents and extend them with custom tools as needed.

---

If you need further exploration or examples, please ask!