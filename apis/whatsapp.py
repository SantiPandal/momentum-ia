from fastapi import APIRouter, Request
from twilio.rest import Client
import os
import dotenv

dotenv.load_dotenv()

router = APIRouter()


@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    form_data = await request.form()
    incoming_msg = form_data.get("Body", "")
    from_number = form_data.get("From", "")

    print(f"Received message: '{incoming_msg}' from {from_number}")

    # --- THIS IS THE NEW PART ---
    # Get your Twilio credentials from environment variables (we'll set these up)
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    twilio_number = os.environ.get("TWILIO_WHATSAPP_NUMBER")

    # Make sure the 'from' number has the whatsapp: prefix
    if not twilio_number.startswith("whatsapp:"):
        twilio_number = f"whatsapp:{twilio_number}"

    client = Client(account_sid, auth_token)

    # The hardcoded reply!
    reply_message = "Momentum heard you! This is an automated reply."

    print(f"DEBUG: Sending from '{twilio_number}' to '{from_number}'")
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