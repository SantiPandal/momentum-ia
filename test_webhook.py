from services.agents import agent_executor
from langchain_core.messages import HumanMessage

# Simulate webhook behavior exactly
def test_webhook_logic(incoming_msg, from_number):
    print(f"Received message: '{incoming_msg}' from {from_number}")
    
    # Each user conversation is a separate thread for memory
    thread_id = from_number
    config = {"configurable": {"thread_id": thread_id}}
    
    # Define the input for the agent
    agent_input = {"messages": [HumanMessage(content=incoming_msg)]}

    # Get the response from the agent
    try:
        print("Calling agent...")
        result = agent_executor.invoke(agent_input, config=config)
        final_response_message = result['messages'][-1].content
        print(f"--- Agent Response --- \n{final_response_message}\n----------------------")
        return final_response_message
    except Exception as e:
        print(f"Agent error: {e}")
        import traceback
        traceback.print_exc()
        return ""

# Test it
if __name__ == "__main__":
    response = test_webhook_logic("Hi there, I want to get fit!", "whatsapp:+15551234567")
    print(f"\nFinal response: '{response}'")
    print(f"Fallback would be: '{response or 'I am having trouble responding right now. Please try again!'}'") 