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

    print("DEBUG — from:", from_number_twilio, "to:", to_number)

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


@tool
def start_proof_submission(to_number: str) -> str:
    """
    Starts a photo-only proof submission process for a user.
    This matches the original WhatsApp Flow JSON structure - simple photo submission only.
    """
    from .database_tools import manage_proof_submission_state
    
    # Set user to photo submission state
    manage_proof_submission_state.invoke({
        "phone_number": to_number,
        "state": "awaiting_proof_photo"
    })
    
    # Send message matching the original flow intent
    message_body = """📸 **Submit Your Proof**

Please take a photo to verify you've completed your task for today.

Send me the photo now and I'll record your proof submission."""
    
    try:
        account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        from_number_twilio = os.environ.get("TWILIO_WHATSAPP_NUMBER")

        if not all([account_sid, auth_token, from_number_twilio]):
            return "Error: Twilio credentials are not configured."

        if not from_number_twilio.startswith("whatsapp:"):
            from_number_twilio = f"whatsapp:{from_number_twilio}"

        client = Client(account_sid, auth_token)
        message = client.messages.create(
            from_=from_number_twilio,
            body=message_body,
            to=to_number
        )
        return f"Proof submission process started with SID: {message.sid}"
    except Exception as e:
        print(f"Error starting proof submission: {e}")
        return f"Error starting proof submission: {e}"


@tool 
def process_proof_submission_response(phone_number: str, user_message: str, media_url: str = None) -> str:
    """
    Processes photo proof submission - simplified to match original WhatsApp Flow JSON.
    Expects: user sends photo -> proof recorded immediately.
    """
    from .database_tools import get_proof_submission_state, manage_proof_submission_state, create_verification
    from datetime import date
    
    # Get current state
    state_result = get_proof_submission_state.invoke({"phone_number": phone_number})
    
    if "No active proof submission process" in state_result:
        return "No active proof submission process. Use start_proof_submission to begin."
    
    # Simple photo-only workflow
    if "State: awaiting_proof_photo" in state_result:
        if not media_url:
            # No photo provided, ask again
            return send_whatsapp_message.invoke({
                "to_number": phone_number,
                "body": "📸 Please send a photo to complete your proof submission."
            })
        
        # Photo received - complete submission immediately
        manage_proof_submission_state.invoke({
            "phone_number": phone_number,
            "state": None,  # Clear state - submission complete
            "proof_data": None
        })
        
        # Create verification record with the photo
        today = date.today().strftime("%Y-%m-%d")
        create_verification.invoke({
            "phone_number": phone_number,
            "due_date": today,
            "proof_url": media_url,
            "justification": user_message or "Photo proof submitted"
        })
        
        return send_whatsapp_message.invoke({
            "to_number": phone_number,
            "body": "✅ **Proof Submitted Successfully!**\n\nYour photo proof has been recorded. Keep up the great work! 💪"
        })
    
    return "Unknown proof submission state."