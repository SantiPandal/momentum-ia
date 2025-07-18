# apis/whatsapp.py

from fastapi import APIRouter, Request
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from services.agents import agent_executor
from services.tools.communication_tools import send_whatsapp_message

load_dotenv()
router = APIRouter()

@router.get("/webhook")
async def webhook_validation(request: Request):
    """Handle Twilio webhook validation"""
    print("🔍 GET webhook validation request received")
    return {"status": "webhook_validation_ok"}

@router.post("/webhook")
async def handle_whatsapp_message(request: Request):
    from services.tools.communication_tools import process_proof_submission_response
    from services.tools.database_tools import get_proof_submission_state
    
    print("🔥 WEBHOOK HIT - Request received!")
    
    # Log all form data for debugging
    form_data = await request.form()
    print(f"📋 Full form data: {dict(form_data)}")
    
    incoming_msg = form_data.get("Body", "")
    from_number = form_data.get("From", "")
    media_url = form_data.get("MediaUrl0", "")  # Twilio sends media as MediaUrl0, MediaUrl1, etc.
    
    # Fix phone number formatting - ensure it has the + prefix
    if from_number and from_number.startswith("whatsapp:"):
        # Remove 'whatsapp:' prefix to get just the number
        number_only = from_number.replace("whatsapp:", "").strip()
        
        # If the number doesn't start with +, add it
        if not number_only.startswith("+"):
            number_only = f"+{number_only}"
        
        # Reconstruct the whatsapp number
        from_number = f"whatsapp:{number_only}"

    print(f"📱 Received message: '{incoming_msg}' from {from_number}")
    if media_url:
        print(f"🖼️ Media URL: {media_url}")

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
        print(f"❌ Error checking proof submission state: {e}")
        print(f"❌ Error type: {type(e)}")
        # Continue to regular agent processing if proof state check fails

    # Regular message handling through agent
    if not incoming_msg:
        incoming_msg = "[Media message received]"  # Handle media-only messages

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
        print("🤖 Invoking agent...")
        # Using .ainvoke() for async compatibility in FastAPI
        result = await agent_executor.ainvoke(agent_input, config=config)
        print(f"✅ Agent execution completed: {result}")
    except Exception as e:
        print(f"❌ Error invoking agent: {e}")
        print(f"❌ Error type: {type(e)}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
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


@router.post("/test_mexican_number")
async def test_mexican_number():
    """Test sending message to the Mexican number"""
    result = send_whatsapp_message.invoke({
        "to_number": "whatsapp:+525564314241",
        "body": "🧪 Test message from the server to Mexican number!"
    })
    return {"status": "test_sent", "result": result}