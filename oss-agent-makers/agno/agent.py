#!/usr/bin/env python3
"""
Basic Hello World agent using Agno (phidata)
"""

from agno.agent import Agent
from agno.models.openai import OpenAIChat

def main():
    # Create a simple agent without tools
    agent = Agent(
        model=OpenAIChat(id="gpt-4o-mini"),  # Using mini for cost efficiency
        instructions="You are a friendly and helpful assistant.",
        markdown=True,
    )
    
    # Get a simple response
    print("Hello World Agent using Agno\n")
    print("=" * 40)
    
    agent.print_response("Hello! Please introduce yourself.", stream=True)
    
    print("\n" + "=" * 40)
    print("\nAgent interaction complete!")

if __name__ == "__main__":
    main()