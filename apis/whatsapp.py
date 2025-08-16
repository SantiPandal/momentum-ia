# apis/whatsapp.py

from fastapi import APIRouter, Request
from langchain_core.messages import HumanMessage
from logger import get_logger

from services.agents import agent_executor
from services.agent_tools import send_whatsapp_message

logger = get_logger(__name__)
router = APIRouter()

@router.get("/webhook")
async def webhook_validation(request: Request):
    """Handle Twilio webhook validation"""
    logger.info("Webhook validation request received")
    return {"status": "webhook_validation_ok"}

@router.post("/webhook")
async def handle_whatsapp_message(request: Request):
    from services.agent_tools import process_proof_submission_response, get_proof_submission_state
    
    logger.info("WhatsApp webhook request received")
    
    # Get form data
    form_data = await request.form()
    logger.debug(f"Form data received: {dict(form_data)}")
    
    incoming_msg = form_data.get("Body", "")
    from_number = form_data.get("From", "")
    media_url = form_data.get("MediaUrl0", "")  # Twilio sends media as MediaUrl0, MediaUrl1, etc.
    flow_response = form_data.get("FlowResponse", "")  # Check for Flow response data
    
    # Fix phone number formatting - ensure it has the + prefix
    if from_number and from_number.startswith("whatsapp:"):
        # Remove 'whatsapp:' prefix to get just the number
        number_only = from_number.replace("whatsapp:", "").strip()
        
        # If the number doesn't start with +, add it
        if not number_only.startswith("+"):
            number_only = f"+{number_only}"
        
        # Reconstruct the whatsapp number
        from_number = f"whatsapp:{number_only}"

    logger.info(f"Message received from {from_number}: '{incoming_msg[:50]}...' ({'with media' if media_url else 'text only'})")
    if flow_response:
        logger.info(f"Flow response received from {from_number}")

    if not from_number:
        return {"status": "error", "message": "Missing sender number"}

    # Check if user is in a proof submission process
    try:
        state_result = get_proof_submission_state.invoke({"phone_number": from_number})
        print(f"🔍 Proof submission state check result: {state_result}")
        if "No active proof submission process" not in state_result:
            # User is in proof submission flow - handle it specially
            print("📸 Processing proof submission response")
            process_proof_submission_response.invoke({
                "phone_number": from_number,
                "user_message": incoming_msg or "[Media]",
                "media_url": media_url if media_url else None
            })
            return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error checking proof submission state: {e}")
        # Continue to regular agent processing if proof state check fails

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
    elif incoming_msg or media_url:
        # Regular text message or media message
        message_content = incoming_msg if incoming_msg else "[Media message received]"
        agent_input = {
            "messages": [
                HumanMessage(content=f"My phone number is {from_number}. My message is: '{message_content}'")
            ]
        }
    else:
        return {"status": "error", "message": "No message or flow data received"}

    # Invoke the agent
    try:
        logger.info(f"Invoking AI agent for {from_number}")
        result = await agent_executor.ainvoke(agent_input, config=config)
        logger.info(f"Agent execution completed for {from_number}")
    except Exception as e:
        logger.error(f"Error invoking agent for {from_number}: {e}", exc_info=True)
        return {"status": "error", "message": f"Agent error: {e}"}

    return {"status": "ok"}


@router.post("/send_test_message")
async def send_test_message(request: Request):
    """Send a plain WhatsApp text message.

    Expected JSON body:
    {
        "to": "+525564314241",
        "body": "Hello from FastAPI test!"
    }
    """
    data = await request.json()
    to_number = data.get("to")
    body = data.get("body", "Test message from the server")

    if not to_number:
        return {"status": "error", "message": "Missing 'to' field"}

    # Invoke the tool
    result = send_whatsapp_message.invoke({
        "to_number": to_number,
        "body": body
    })

    return {"status": "ok", "detail": result}


@router.get("/test")
async def test_endpoint():
    """Simple test endpoint to verify server is reachable"""
    print("🧪 Test endpoint hit!")
    return {"status": "server_alive", "message": "WhatsApp webhook server is running!"}


@router.post("/test")
async def test_post_endpoint(request: Request):
    """Test POST endpoint to debug webhook issues"""
    print("🧪 POST Test endpoint hit!")
    try:
        form_data = await request.form()
        print(f"📋 Test form data received: {dict(form_data)}")
        return {"status": "post_test_success", "received_data": dict(form_data)}
    except Exception as e:
        print(f"❌ Error in test endpoint: {e}")
        return {"status": "error", "error": str(e)}