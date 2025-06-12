import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

async def main():
    # Create the model client
    model_client = OpenAIChatCompletionClient(
        model="gpt-4o-mini"
        # api_key is automatically loaded from OPENAI_API_KEY env var
    )
    
    # Create a simple assistant agent
    agent = AssistantAgent(
        name="assistant",
        model_client=model_client,
        system_message="You are a helpful AI assistant."
    )
    
    # Run the agent with a simple task
    result = await agent.run(task="Tell me a joke about programming")
    
    # Print the messages
    for message in result.messages:
        if hasattr(message, 'content'):
            print(f"{message.source}: {message.content}")

if __name__ == "__main__":
    asyncio.run(main())