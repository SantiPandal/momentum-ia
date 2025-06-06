# tools/communication_tools.py

from langchain_core.tools import tool
from pydantic import BaseModel, Field
from twilio.rest import Client
import os

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