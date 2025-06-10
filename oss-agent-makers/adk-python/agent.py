import asyncio  
from google.adk.agents import Agent  
from google.adk.runners import InMemoryRunner  
from google.genai import types  
  
# Define your agent  
root_agent = Agent(  
    name="hello_agent",  
    model="gemini-2.0-flash",  
    instruction="You are a helpful assistant. Answer user questions politely and helpfully.",  
    description="A simple helpful assistant agent"  
)  
  
async def main():  
    # Create runner with in-memory services for development  
    runner = InMemoryRunner(agent=root_agent, app_name='my_agent_app')  
      
    # Create a session  
    session = await runner.session_service.create_session(  
        app_name='my_agent_app',   
        user_id='user1'  
    )  
      
    # Interactive loop  
    print("ADK Agent is ready! Type 'quit' to exit.")  
    while True:  
        user_input = input("\nYou: ")  
        if user_input.lower() in ['quit', 'exit']:  
            break  
              
        # Create user content  
        content = types.Content(  
            role='user',   
            parts=[types.Part.from_text(text=user_input)]  
        )  
          
        # Run the agent and stream responses  
        print("Agent: ", end="", flush=True)  
        async for event in runner.run_async(  
            user_id='user1',  
            session_id=session.id,  
            new_message=content  
        ):  
            if event.content.parts and event.content.parts[0].text:  
                print(event.content.parts[0].text, end="", flush=True)  
        print()  # New line after response  
  
if __name__ == '__main__':  
    asyncio.run(main())