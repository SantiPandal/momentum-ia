from services.agents import agent_executor
from langchain_core.messages import HumanMessage
import os

# Temporarily disable Twilio sending for testing by setting fake credentials
os.environ["TWILIO_ACCOUNT_SID"] = "test"
os.environ["TWILIO_AUTH_TOKEN"] = "test"  
os.environ["TWILIO_WHATSAPP_NUMBER"] = "whatsapp:+15551234567"

def test_new_user_workflow():
    print("=== Testing New User Workflow ===")
    
    # Test phone number that looks real enough for Twilio validation
    test_phone = "whatsapp:+15551234567"
    config = {'configurable': {'thread_id': test_phone}}
    
    # Step 1: First message from new user
    print("\n1. User says hello...")
    agent_input = {'messages': [HumanMessage(content=f'My phone number is {test_phone}. My message is: Hello!')]}
    
    try:
        result = agent_executor.invoke(agent_input, config=config)
        print(f"Agent response: {result['messages'][-1].content}")
        
        # Step 2: User provides their name
        print("\n2. User provides name...")
        agent_input2 = {'messages': [HumanMessage(content=f'My phone number is {test_phone}. My message is: My name is Sarah')]}
        
        result2 = agent_executor.invoke(agent_input2, config=config)
        print(f"Agent response: {result2['messages'][-1].content}")
        
        print("\n✅ Workflow test completed!")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_new_user_workflow() 