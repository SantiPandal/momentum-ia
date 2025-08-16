# tools/communication_tools.py

from langchain_core.tools import tool
from pydantic import BaseModel, Field
from twilio.rest import Client
import os
import json

@tool
def send_whatsapp_message(to_number: str, body: str) -> str:
    """
    Sends a WhatsApp message to a specified phone number using Twilio.
    Use this as your final step to communicate with the user.
    """
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    from_number_twilio = os.environ.get("TWILIO_WHATSAPP_NUMBER")

    if not all([account_sid, auth_token, from_number_twilio]):
        return "Error: Twilio credentials are not configured."

    if not from_number_twilio.startswith("whatsapp:"):
        from_number_twilio = f"whatsapp:{from_number_twilio}"

    try:
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            from_=from_number_twilio,
            body=body,
            to=to_number
        )
        return f"Message sent successfully with SID: {message.sid}"
    except Exception as e:
        print(f"Error sending Twilio message: {e}")
        return f"Error sending message: {e}"


@tool
def send_whatsapp_flow(to_number: str, flow_id: str = None, cta_text: str = "Submit Proof") -> str:
    """
    Sends a WhatsApp Flow for proof verification.
    Use this to request photo verification from users.
    If no flow_id is provided, uses the default proof submission flow.
    """
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    from_number_twilio = os.environ.get("TWILIO_WHATSAPP_NUMBER")
    default_flow_id = os.environ.get("WHATSAPP_FLOW_ID")

    if not all([account_sid, auth_token, from_number_twilio]):
        return "Error: Twilio credentials are not configured."

    if not from_number_twilio.startswith("whatsapp:"):
        from_number_twilio = f"whatsapp:{from_number_twilio}"

    # Use provided flow_id or default
    flow_content_id = flow_id or default_flow_id
    
    if not flow_content_id:
        return "Error: No Flow ID provided and WHATSAPP_FLOW_ID not configured."

    try:
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            from_=from_number_twilio,
            to=to_number,
            content_sid=flow_content_id,
            content_variables=json.dumps({
                "cta_text": cta_text
            })
        )
        return f"Flow sent successfully with SID: {message.sid}"
    except Exception as e:
        print(f"Error sending WhatsApp Flow: {e}")
        return f"Error sending flow: {e}" 