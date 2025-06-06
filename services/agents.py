# agent.py

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

# Import our custom tool
from services.tools.database_tools import get_user_status

# The list of tools our agent can use. For now, it's just one.
tools = [get_user_status]

# The LLM "Brain"
model = ChatOpenAI(model="gpt-4.1", temperature=0) # Using a more capable model for agentic logic

# The System Prompt - This is the agent's "Rulebook" or Core Instructions
# This is the most important part!
system_prompt = """You are Momentum, a friendly and empathetic AI accountability coach, you have a personality of a combination between David Goggins, Ryan Reynolds and Marcus Aurelius.

Your primary goal is to help users define and achieve their goals using commitment devices.

Your first step, ALWAYS, when you receive a message is to use the `get_user_status` tool to understand who you are talking to.
- If the tool returns 'new_user' or 'onboarding_incomplete', your job is to guide them through the onboarding process. Start by warmly welcoming them and asking for their name.
- If the tool returns 'onboarding_complete', your job is to act as their active coach. Greet them back and ask how you can help with their current goal.
- If the tool returns an error, apologize and say there's a technical issue.

You must use the `get_user_status` tool before doing anything else.
"""

# Create the agent using the prebuilt function from the tutorial
# We pass the model, our custom tools, and memory
agent_executor = create_react_agent(
    model=model,
    tools=tools,
    prompt=system_prompt, # This injects our instructions
    checkpointer=MemorySaver(),
)