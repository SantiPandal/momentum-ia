# apis/whatsapp.py

from fastapi import APIRouter, Request
from twilio.rest import Client
import os
import dotenv

# --- NEW IMPORTS ---
from langchain_core.messages import HumanMessage
# Import our agent executor from the agent.py file
from services.agents import agent_executor

dotenv.load_dotenv()

router = APIRouter()


@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    form_data = await request.form()
    incoming_msg = form_data.get("Body", "")
    from_number = form_data.get("From", "")

    print(f"Received message: '{incoming_msg}' from {from_number}")

    # --- START: AGENT LOGIC ---
    
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
    except Exception as e:
        print(f"Agent error: {e}")
        final_response_message = ""
    
    # --- END: AGENT LOGIC ---


    # --- TWILIO REPLY LOGIC (Now uses the agent's response) ---
    
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    twilio_number = os.environ.get("TWILIO_WHATSAPP_NUMBER")

    if not all([account_sid, auth_token, twilio_number]):
        print("ERROR: Missing Twilio credentials in environment variables")
        return {"status": "error", "message": "Missing credentials"}
    
    if not twilio_number.startswith("whatsapp:"):
        twilio_number = f"whatsapp:{twilio_number}"

    client = Client(account_sid, auth_token)

    # Use the agent's response instead of the hardcoded message!
    reply_message = final_response_message or "I'm having trouble responding right now. Please try again!"

    try:
        message = client.messages.create(
            from_=twilio_number,
            body=reply_message,
            to=from_number
        )
        print(f"Reply sent with SID: {message.sid}")
    except Exception as e:
        print(f"Error sending reply: {e}")

    return {"status": "ok"}