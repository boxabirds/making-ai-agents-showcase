#!/bin/bash

# Installation script for Parlant Python package

# Install the Parlant package using pip
pip install parlant

# Client and Server instructions

# Client: Using the Python SDK
# Save the following example as agent.py and run it to start the conversation server
: '
import parlant.sdk as p
import asyncio
from textwrap import dedent

@p.tool
async def get_on_sale_car(context: p.ToolContext) -> p.ToolResult:
    return p.ToolResult("Hyundai i20")

@p.tool
async def human_handoff(context: p.ToolContext) -> p.ToolResult:
    await notify_sales(context.customer_id, context.session_id)
    return p.ToolResult(
        data="Session handed off to sales team",
        control={"mode": "manual"},
    )

async def start_conversation_server() -> None:
    async with p.Server() as server:
        agent = await server.create_agent(
            name="Johnny",
            description="You work at a car dealership",
        )
        journey = await agent.create_journey(
            title="Research Car",
            conditions=[
                "The customer wants to buy a new car",
                "The customer expressed general interest in new cars",
            ],
            description=dedent("""\
                Help the customer come to a decision of what new car to get.

                The process goes like this:
                1. First try to actively understand their needs
                2. Once needs are clarified, recommend relevant categories or specific models for consideration."""),
        )
        offer_on_sale_car = await journey.create_guideline(
          condition="the customer indicates they're on a budget",
          action="offer them a car that is on sale",
          tools=[get_on_sale_car],
        )
        transfer_to_sales = await journey.create_guideline(
          condition="the customer clearly stated they wish to buy a specific car",
          action="transfer them to the sales team",
          tools=[human_handoff],
        )
        await transfer_to_sales.prioritize_over(offer_on_sale_car)

asyncio.run(start_conversation_server())
'

# Server: Run the Parlant server
parlant-server run
# The server will be available at http://localhost:8800

# End of script