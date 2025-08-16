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
    
    # Check for Flow response data
    flow_response = form_data.get("FlowResponse", "")
    
    print(f"Received message: '{incoming_msg}' from {from_number}")
    if flow_response:
        print(f"Flow response data: {flow_response}")

    if not from_number:
        return {"status": "error", "message": "Missing sender number"}

    thread_id = from_number
    config = {"configurable": {"thread_id": thread_id}}

    # Handle Flow responses differently from regular messages
    if flow_response:
        # This is a Flow response with image data
        agent_input = {
            "messages": [
                HumanMessage(content=f"My phone number is {from_number}. Flow response data: {flow_response}")
            ]
        }
    elif incoming_msg:
        # Regular text message
        agent_input = {
            "messages": [
                HumanMessage(content=f"My phone number is {from_number}. My message is: '{incoming_msg}'")
            ]
        }
    else:
        return {"status": "error", "message": "No message or flow data received"}

    # Invoke the agent
    try:
        await agent_executor.ainvoke(agent_input, config=config)
    except Exception as e:
        print(f"Error invoking agent: {e}")

    return {"status": "ok"}