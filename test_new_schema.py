from services.agents import agent_executor
from langchain_core.messages import HumanMessage
import os

# Use test credentials to avoid actual Twilio charges
os.environ["TWILIO_ACCOUNT_SID"] = "test"
os.environ["TWILIO_AUTH_TOKEN"] = "test"  
os.environ["TWILIO_WHATSAPP_NUMBER"] = "whatsapp:+15551234567"

def test_complete_workflow():
    print("=== Testing Complete Workflow with New Schema ===")
    
    test_phone = "whatsapp:+15555551234"
    config = {'configurable': {'thread_id': test_phone}}
    
    # Step 1: New user onboarding
    print("\n1. NEW USER - First contact...")
    agent_input = {'messages': [HumanMessage(content=f'My phone number is {test_phone}. My message is: Hi, I want to start using Momentum!')]}
    
    try:
        result = agent_executor.invoke(agent_input, config=config)
        print(f"Agent: {result['messages'][-1].content}")
        
        # Step 2: User provides name
        print("\n2. USER PROVIDES NAME...")
        agent_input2 = {'messages': [HumanMessage(content=f'My phone number is {test_phone}. My message is: My name is Alex')]}
        result2 = agent_executor.invoke(agent_input2, config=config)
        print(f"Agent: {result2['messages'][-1].content}")
        
        # Step 3: User wants to set a goal
        print("\n3. USER WANTS TO SET GOAL...")
        agent_input3 = {'messages': [HumanMessage(content=f'My phone number is {test_phone}. My message is: I want to set up my first goal!')]}
        result3 = agent_executor.invoke(agent_input3, config=config)
        print(f"Agent: {result3['messages'][-1].content}")
        
        # Step 4: User provides goal details step by step
        print("\n4. USER PROVIDES GOAL DESCRIPTION...")
        agent_input4 = {'messages': [HumanMessage(content=f'My phone number is {test_phone}. My message is: I want to exercise for 30 minutes every day')]}
        result4 = agent_executor.invoke(agent_input4, config=config)
        print(f"Agent: {result4['messages'][-1].content}")
        
        print("\n5. USER PROVIDES START DATE...")
        agent_input5 = {'messages': [HumanMessage(content=f'My phone number is {test_phone}. My message is: 2024-01-15')]}
        result5 = agent_executor.invoke(agent_input5, config=config)
        print(f"Agent: {result5['messages'][-1].content}")
        
        print("\n6. USER PROVIDES END DATE...")
        agent_input6 = {'messages': [HumanMessage(content=f'My phone number is {test_phone}. My message is: 2024-02-15')]}
        result6 = agent_executor.invoke(agent_input6, config=config)
        print(f"Agent: {result6['messages'][-1].content}")
        
        print("\n7. USER PROVIDES STAKE AMOUNT...")
        agent_input7 = {'messages': [HumanMessage(content=f'My phone number is {test_phone}. My message is: $25')]}
        result7 = agent_executor.invoke(agent_input7, config=config)
        print(f"Agent: {result7['messages'][-1].content}")
        
        print("\n8. USER PROVIDES VERIFICATION METHOD...")
        agent_input8 = {'messages': [HumanMessage(content=f'My phone number is {test_phone}. My message is: I will send a photo of my workout')]}
        result8 = agent_executor.invoke(agent_input8, config=config)
        print(f"Agent: {result8['messages'][-1].content}")
        
        print("\n9. USER WITH ACTIVE GOAL CHECKS IN...")
        agent_input9 = {'messages': [HumanMessage(content=f'My phone number is {test_phone}. My message is: How am I doing with my goal?')]}
        result9 = agent_executor.invoke(agent_input9, config=config)
        print(f"Agent: {result9['messages'][-1].content}")
        
        print("\n✅ Complete workflow test finished!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_complete_workflow() 