#!/usr/bin/env python3
"""Basic LangGraph agent example."""

import os
from typing import Dict, Any
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI


def get_weather(city: str) -> str:
    """Get weather for a given city.
    
    Args:
        city: The name of the city to get weather for
        
    Returns:
        A string describing the weather in that city
    """
    # This is a mock function - in a real application, 
    # this would call a weather API
    return f"It's always sunny in {city}!"


def get_time(timezone: str = "UTC") -> str:
    """Get the current time in a given timezone.
    
    Args:
        timezone: The timezone to get the time for (default: UTC)
        
    Returns:
        A string with the current time
    """
    from datetime import datetime
    import pytz
    
    try:
        tz = pytz.timezone(timezone)
        current_time = datetime.now(tz)
        return f"The current time in {timezone} is {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
    except:
        return f"Unable to get time for timezone: {timezone}"


def calculate(expression: str) -> str:
    """Perform a simple calculation.
    
    Args:
        expression: A mathematical expression to evaluate
        
    Returns:
        The result of the calculation as a string
    """
    try:
        # Note: eval() is used here for simplicity but should be 
        # replaced with a safer alternative in production
        result = eval(expression)
        return f"The result of {expression} is {result}"
    except Exception as e:
        return f"Error calculating {expression}: {str(e)}"


def main():
    """Main function to demonstrate LangGraph agent."""
    
    # Check for API keys
    openai_key = os.environ.get("OPENAI_API_KEY")
    google_key = os.environ.get("GEMINI_API_KEY")
    
    if not openai_key and not google_key:
        print("Error: Please set either OPENAI_API_KEY or GEMINI_API_KEY environment variable")
        return
    
    # Choose model based on available API key
    if openai_key:
        model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        print("Using OpenAI GPT-4o-mini model")
    else:
        model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
        print("Using Google Gemini 1.5 Flash model")
    
    # Create the agent with multiple tools
    agent = create_react_agent(
        model=model,
        tools=[get_weather, get_time, calculate],
    )
    
    # Example interactions
    examples = [
        "What's the weather like in San Francisco?",
        "What time is it in Tokyo?",
        "Calculate 25 * 4 + 10",
        "What's the weather in Paris and what time is it there?",
    ]
    
    print("\n" + "="*50)
    print("LangGraph Basic Agent Demo")
    print("="*50 + "\n")
    
    for question in examples:
        print(f"\nUser: {question}")
        
        # Invoke the agent
        result = agent.invoke(
            {"messages": [{"role": "user", "content": question}]}
        )
        
        # Extract the final message
        final_message = result["messages"][-1]
        print(f"Agent: {final_message.content}")
        print("-" * 40)


if __name__ == "__main__":
    main()