#!/bin/bash

# Installation script for Agno Python package using uv package manager

# Create and activate a virtual environment with Python 3.12
uv init
uv venv --python 3.12
source .venv/bin/activate

# Install Agno and dependencies using uv pip
uv add agno 

# Instructions to run example reasoning agent
# Save the following example code to reasoning_agent.py:
# 
# from agno.agent import Agent
# from agno.models.anthropic import Claude
# from agno.tools.reasoning import ReasoningTools
# from agno.tools.yfinance import YFinanceTools
#
# agent = Agent(
#     model=Claude(id="claude-sonnet-4-20250514"),
#     tools=[
#         ReasoningTools(add_instructions=True),
#         YFinanceTools(stock_price=True, analyst_recommendations=True, company_info=True, company_news=True),
#     ],
#     instructions=[
#         "Use tables to display data",
#         "Only output the report, no other text",
#     ],
#     markdown=True,
# )
# agent.print_response(
#     "Write a report on NVDA",
#     stream=True,
#     show_full_reasoning=True,
#     stream_intermediate_steps=True,
# )
#
# Then run the agent:
# python reasoning_agent.py

# Instructions to run example multi-agent team
# Save the following example code to agent_team.py:
#
# from agno.agent import Agent
# from agno.models.openai import OpenAIChat
# from agno.tools.duckduckgo import DuckDuckGoTools
# from agno.tools.yfinance import YFinanceTools
# from agno.team import Team
#
# web_agent = Agent(
#     name="Web Agent",
#     role="Search the web for information",
#     model=OpenAIChat(id="gpt-4o"),
#     tools=[DuckDuckGoTools()],
#     instructions="Always include sources",
#     show_tool_calls=True,
#     markdown=True,
# )
#
# finance_agent = Agent(
#     name="Finance Agent",
#     role="Get financial data",
#     model=OpenAIChat(id="gpt-4o"),
#     tools=[YFinanceTools(stock_price=True, analyst_recommendations=True, company_info=True)],
#     instructions="Use tables to display data",
#     show_tool_calls=True,
#     markdown=True,
# )
#
# agent_team = Team(
#     mode="coordinate",
#     members=[web_agent, finance_agent],
#     model=OpenAIChat(id="gpt-4o"),
#     success_criteria="A comprehensive financial news report with clear sections and data-driven insights.",
#     instructions=["Always include sources", "Use tables to display data"],
#     show_tool_calls=True,
#     markdown=True,
# )
#
# agent_team.print_response("What's the market outlook and financial performance of AI semiconductor companies?", stream=True)
#
# Install additional dependencies for multi-agent example:
# uv pip install duckduckgo-search yfinance
#
# Run the multi-agent team:
# python agent_team.py