from services.agents import agent_executor
from langchain_core.messages import HumanMessage

# Test 1: New user
print("=== TEST 1: New User ===")
config1 = {'configurable': {'thread_id': 'whatsapp:+1234567890'}}
agent_input1 = {'messages': [HumanMessage(content='My phone number is whatsapp:+1234567890. My message is: Hi, I am new here!')]}

try:
    result1 = agent_executor.invoke(agent_input1, config=config1)
    print('Agent response:')
    print(result1['messages'][-1].content)
except Exception as e:
    print(f'Error: {e}')

print("\n" + "="*50 + "\n")

# Test 2: Simulate a more complex message
print("=== TEST 2: Regular Conversation ===")
config2 = {'configurable': {'thread_id': 'whatsapp:+9876543210'}}
agent_input2 = {'messages': [HumanMessage(content='My phone number is whatsapp:+9876543210. My message is: I want to lose 10 pounds in 2 months')]}

try:
    result2 = agent_executor.invoke(agent_input2, config=config2)
    print('Agent response:')
    print(result2['messages'][-1].content)
except Exception as e:
    print(f'Error: {e}') 