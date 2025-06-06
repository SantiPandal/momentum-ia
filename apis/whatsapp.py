# apis/whatsapp.py

from fastapi import APIRouter, Request
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from services.agents import agent_executor

load_dotenv()
router = APIRouter()

@router.post("/webhook")
async def handle_whatsapp_message(request: Request):
    form_data = await request.form()
    incoming_msg = form_data.get("Body", "")
    from_number = form_data.get("From", "")

    print(f"Received message: '{incoming_msg}' from {from_number}")

    if not incoming_msg or not from_number:
        return {"status": "error", "message": "Missing message body or sender number"}

    thread_id = from_number
    config = {"configurable": {"thread_id": thread_id}}

    # The agent input needs to know who to reply to, so we'll add it to the message.
    # A better way is to pass this in the agent state, but this is simplest for now.
    agent_input = {
        "messages": [
            HumanMessage(content=f"My phone number is {from_number}. My message is: '{incoming_msg}'")
        ]
    }

    # We just need to invoke the agent and let it do its work.
    # We don't need to capture the response here because the agent itself sends the reply.
    try:
        # Using .ainvoke() for async compatibility in FastAPI
        await agent_executor.ainvoke(agent_input, config=config)
    except Exception as e:
        print(f"Error invoking agent: {e}")

    return {"status": "ok"}