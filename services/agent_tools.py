"""
Consolidated agent tools for Momentum-IA.

Following the orthogonality principle, all agent tools are consolidated into a single file
to eliminate circular dependencies and provide a single source of truth for agent capabilities.

Tool Categories:
1. Database Tools (7): User management, commitments, verifications
2. Communication Tools (4): WhatsApp messaging and flows  
3. Verification Tools (2): Image processing and verification records
"""

# Core imports
import json
import base64
from datetime import datetime, date
from typing import Optional, Dict, Any

# Framework imports
from langchain_core.tools import tool
from pydantic import BaseModel, Field

# External service imports
from supabase import create_client, Client
from twilio.rest import Client as TwilioClient
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# Internal imports
from config import settings
from logger import get_logger

logger = get_logger(__name__)

# =============================================================================
# MODULE-LEVEL INITIALIZATION & VALIDATION
# =============================================================================

# Initialize Supabase client
try:
    supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    logger.info("Supabase client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {e}")
    raise

# Validate Twilio credentials
if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_WHATSAPP_NUMBER]):
    logger.error("Missing required Twilio credentials")
    raise ValueError("Twilio credentials not configured properly")
else:
    logger.info("Twilio credentials validated")

# =============================================================================
# DATABASE TOOLS (7 tools)
# =============================================================================

@tool
def get_user_status(phone_number: str) -> str:
    """
    Looks up a user by their phone number.
    If the user does not exist, it creates a new user record.
    Returns one of three statuses:
    - 'new_user': For users messaging for the very first time.
    - 'user_exists_no_goal': For existing users who do not have an active commitment.
    - 'user_exists_active_goal': For existing users who have an active commitment.
    """
    try:
        response = supabase.table("users").select("id, name").eq("phone_number", phone_number).execute()
        
        if not response.data:
            user_data = {"phone_number": phone_number}
            insert_response = supabase.table("users").insert(user_data).execute()
            if insert_response.data:
                logger.info(f"New user created: {phone_number}")
                return "new_user"
            else:
                return "error_creating_user"
        
        # If user exists, check if they have completed basic setup (have a name)
        user = response.data[0]
        if not user.get("name"):
             return "new_user" # Treat them as new if they don't have a name yet.

        # Check if user has active commitments
        commitments_response = supabase.table("commitments").select("id, goal_description").eq("user_id", user["id"]).eq("status", "active").execute()
        
        has_active_goal = len(commitments_response.data) > 0

        if has_active_goal:
            return f"user_exists_active_goal:{user.get('name', 'User')}"
        else:
            return f"user_exists_no_goal:{user.get('name', 'User')}"

    except Exception as e:
        logger.error(f"Database error in get_user_status for {phone_number}: {e}")
        return "error_database_check"


class UpdateUserNameArgs(BaseModel):
    phone_number: str = Field(description="The user's phone number, including the 'whatsapp:' prefix.")
    name: str = Field(description="The user's first name to save.")

@tool(args_schema=UpdateUserNameArgs)
def update_user_name(phone_number: str, name: str) -> str:
    """
    Updates the user's record with their name after they provide it during onboarding.
    """
    try:
        response = supabase.table("users").update({"name": name}).eq("phone_number", phone_number).execute()
        if response.data:
            logger.info(f"Updated name for {phone_number} to {name}")
            return f"Successfully updated user's name to {name}."
        else:
            return "Error: Could not find user to update."
    except Exception as e:
        logger.error(f"Error updating user name: {e}")
        return "Error updating name in database."


class CreateCommitmentArgs(BaseModel):
    phone_number: str = Field(description="The user's phone number to identify them.")
    goal_description: str = Field(description="High-level description of the goal/commitment.")
    task_description: Optional[str] = Field(description="Specific task or action to be done daily/periodically.", default=None)
    stake_amount: float = Field(description="Amount the user is willing to stake/risk.")
    stake_type: str = Field(description="Type of stake: 'per_missed_day' or 'one_time_on_failure'.", default="one_time_on_failure")
    start_date: str = Field(description="Start date in YYYY-MM-DD format.")
    end_date: str = Field(description="End date in YYYY-MM-DD format.")
    schedule: Optional[Dict[str, Any]] = Field(description="Schedule configuration (e.g., {'daily': True} or {'weekly': ['monday', 'wednesday']}).", default=None)
    verification_method: Optional[str] = Field(description="How the commitment will be verified.", default=None)

@tool(args_schema=CreateCommitmentArgs)
def create_commitment(
    phone_number: str, 
    goal_description: str, 
    stake_amount: float, 
    start_date: str, 
    end_date: str,
    task_description: Optional[str] = None,
    stake_type: str = "one_time_on_failure",
    schedule: Optional[Dict[str, Any]] = None,
    verification_method: Optional[str] = None
) -> str:
    """
    Creates a new commitment/goal for a user with stake amount, dates, and schedule.
    """
    try:
        # First, find the user by phone number to get their user_id
        user_response = supabase.table("users").select("id").eq("phone_number", phone_number).execute()
        
        if not user_response.data:
            return "Error: User not found. Please make sure the user is registered first."
        
        user_id = user_response.data[0]["id"]
        
        # Default schedule if none provided
        if schedule is None:
            schedule = {"daily": True}
        
        # Create the commitment
        commitment_data = {
            "user_id": user_id,
            "goal_description": goal_description,
            "task_description": task_description,
            "stake_amount": stake_amount,
            "stake_type": stake_type,
            "start_date": start_date,
            "end_date": end_date,
            "schedule": schedule,
            "verification_method": verification_method
        }
        
        commitment_response = supabase.table("commitments").insert(commitment_data).execute()
        
        if commitment_response.data:
            logger.info(f"Commitment created for {phone_number}: {goal_description}")
            return f"Successfully created commitment! Goal: {goal_description}, Stake: ${stake_amount} ({stake_type}), Period: {start_date} to {end_date}"
        else:
            return "Error: Could not create commitment."
            
    except Exception as e:
        logger.error(f"Error creating commitment: {e}")
        return "Error creating commitment in database."


@tool
def get_active_commitment(phone_number: str) -> str:
    """
    Retrieves the active commitment details for a user.
    """
    try:
        # Get user ID
        user_response = supabase.table("users").select("id").eq("phone_number", phone_number).execute()
        if not user_response.data:
            return "Error: User not found."
        
        user_id = user_response.data[0]["id"]
        
        # Get active commitment
        commitment_response = supabase.table("commitments").select("*").eq("user_id", user_id).eq("status", "active").execute()
        
        if not commitment_response.data:
            return "No active commitment found."
        
        commitment = commitment_response.data[0]
        
        return f"Active Goal: {commitment['goal_description']}\nTask: {commitment.get('task_description', 'Not specified')}\nStake: ${commitment['stake_amount']} ({commitment['stake_type']})\nPeriod: {commitment['start_date']} to {commitment['end_date']}\nVerification: {commitment.get('verification_method', 'Not specified')}"
        
    except Exception as e:
        logger.error(f"Error getting active commitment: {e}")
        return "Error retrieving commitment details."


class CreateVerificationArgs(BaseModel):
    phone_number: str = Field(description="The user's phone number to identify them.")
    due_date: str = Field(description="Due date for this verification in YYYY-MM-DD format.")
    proof_url: Optional[str] = Field(description="URL to proof (e.g., photo URL).", default=None)
    justification: Optional[str] = Field(description="Text justification/explanation.", default=None)

@tool(args_schema=CreateVerificationArgs)
def create_verification(
    phone_number: str, 
    due_date: str, 
    proof_url: Optional[str] = None, 
    justification: Optional[str] = None
) -> str:
    """
    Creates a verification record for the user's active commitment.
    """
    try:
        # Get user and their active commitment
        user_response = supabase.table("users").select("id").eq("phone_number", phone_number).execute()
        if not user_response.data:
            return "Error: User not found."
        
        user_id = user_response.data[0]["id"]
        
        commitment_response = supabase.table("commitments").select("id").eq("user_id", user_id).eq("status", "active").execute()
        if not commitment_response.data:
            return "Error: No active commitment found."
        
        commitment_id = commitment_response.data[0]["id"]
        
        # Create verification
        verification_data = {
            "commitment_id": commitment_id,
            "due_date": due_date,
            "status": "completed_on_time",  # Default to on-time completion
            "proof_url": proof_url,
            "justification": justification,
            "verified_at": datetime.now().isoformat()
        }
        
        verification_response = supabase.table("verifications").insert(verification_data).execute()
        
        if verification_response.data:
            return f"Verification recorded successfully for {due_date}!"
        else:
            return "Error: Could not create verification."
            
    except Exception as e:
        logger.error(f"Error creating verification: {e}")
        return "Error creating verification record."


class ManageProofStateArgs(BaseModel):
    phone_number: str = Field(description="The user's phone number to identify them.")
    state: Optional[str] = Field(description="New state to set: 'awaiting_proof_photo' or None to clear", default=None)
    proof_data: Optional[Dict[str, Any]] = Field(description="Proof data to store (type, image_url, description)", default=None)

@tool(args_schema=ManageProofStateArgs)
def manage_proof_submission_state(
    phone_number: str, 
    state: Optional[str] = None,
    proof_data: Optional[Dict[str, Any]] = None
) -> str:
    """
    Manages proof submission state for users. Simple photo-only workflow:
    'awaiting_proof_photo' -> user sends photo -> state cleared (complete)
    """
    try:
        # Get user - try with proof columns first, fallback to basic columns
        try:
            user_response = supabase.table("users").select("id, proof_submission_state, proof_submission_data").eq("phone_number", phone_number).execute()
        except Exception as schema_error:
            logger.warning(f"Proof columns don't exist, using basic user lookup: {schema_error}")
            # Fallback to basic user columns if proof columns don't exist
            user_response = supabase.table("users").select("id").eq("phone_number", phone_number).execute()
            # Return error for now since we can't manage state without the columns
            return "Error: Database schema missing proof_submission_state column"
        if not user_response.data:
            return "Error: User not found."
        
        user = user_response.data[0]
        user_id = user["id"]
        
        # Get current proof data or initialize empty
        current_proof_data = user.get("proof_submission_data") or {}
        
        # Update proof data if provided
        if proof_data:
            current_proof_data.update(proof_data)
        
        # Update user state
        update_data = {
            "proof_submission_state": state,
            "proof_submission_data": current_proof_data if current_proof_data else None
        }
        
        update_response = supabase.table("users").update(update_data).eq("id", user_id).execute()
        
        if update_response.data:
            if state:
                return f"User proof submission state updated to: {state}"
            else:
                return "User proof submission state cleared"
        else:
            return "Error updating user state"
            
    except Exception as e:
        logger.error(f"Error managing proof submission state: {e}")
        return "Error managing proof submission state"


@tool
def get_proof_submission_state(phone_number: str) -> str:
    """
    Gets the current proof submission state and data for a user.
    """
    try:
        try:
            user_response = supabase.table("users").select("proof_submission_state, proof_submission_data").eq("phone_number", phone_number).execute()
        except Exception as schema_error:
            logger.warning(f"Proof columns don't exist in get_proof_submission_state: {schema_error}")
            return "No active proof submission process"
        if not user_response.data:
            return "Error: User not found."
        
        user = user_response.data[0]
        state = user.get("proof_submission_state")
        data = user.get("proof_submission_data") or {}
        
        if not state:
            return "No active proof submission process"
        
        return f"State: {state}, Data: {data}"
        
    except Exception as e:
        logger.error(f"Error getting proof submission state: {e}")
        return "Error retrieving proof submission state"

# =============================================================================
# COMMUNICATION TOOLS (4 tools)
# =============================================================================

@tool
def send_whatsapp_message(to_number: str, body: str) -> str:
    """
    Sends a WhatsApp message to a specified phone number using Twilio.
    Use this as your final step to communicate with the user.
    """
    from_number_twilio = settings.TWILIO_WHATSAPP_NUMBER
    if not from_number_twilio.startswith("whatsapp:"):
        from_number_twilio = f"whatsapp:{from_number_twilio}"

    logger.debug(f"Sending WhatsApp message from {from_number_twilio} to {to_number}")
    logger.info(f"MESSAGE CONTENT: '{body}'")  # Debug the actual message content

    try:
        client = TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            from_=from_number_twilio,
            body=body,
            to=to_number
        )
        logger.info(f"WhatsApp message sent successfully to {to_number}")
        return f"Message sent successfully with SID: {message.sid}"
    except Exception as e:
        logger.error(f"Error sending WhatsApp message to {to_number}: {e}")
        return f"Error sending message: {e}"


@tool
def send_whatsapp_flow(to_number: str, flow_id: str = None, cta_text: str = "Submit Proof") -> str:
    """
    Sends a WhatsApp Flow for proof verification.
    Use this to request photo verification from users.
    If no flow_id is provided, uses the default proof submission flow.
    """
    from_number_twilio = settings.TWILIO_WHATSAPP_NUMBER
    if not from_number_twilio.startswith("whatsapp:"):
        from_number_twilio = f"whatsapp:{from_number_twilio}"

    # Use provided flow_id or default
    flow_content_id = flow_id or settings.WHATSAPP_FLOW_ID
    
    if not flow_content_id:
        return "Error: No Flow ID provided and WHATSAPP_FLOW_ID not configured."

    try:
        client = TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            from_=from_number_twilio,
            to=to_number,
            content_sid=flow_content_id,
            content_variables=json.dumps({
                "cta_text": cta_text
            })
        )
        logger.info(f"WhatsApp Flow sent successfully to {to_number}")
        return f"Flow sent successfully with SID: {message.sid}"
    except Exception as e:
        logger.error(f"Error sending WhatsApp Flow to {to_number}: {e}")
        return f"Error sending flow: {e}"


@tool
def start_proof_submission(to_number: str) -> str:
    """
    Starts a photo-only proof submission process for a user.
    This matches the original WhatsApp Flow JSON structure - simple photo submission only.
    """
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
        client = TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        from_number_twilio = settings.TWILIO_WHATSAPP_NUMBER
        if not from_number_twilio.startswith("whatsapp:"):
            from_number_twilio = f"whatsapp:{from_number_twilio}"

        message = client.messages.create(
            from_=from_number_twilio,
            body=message_body,
            to=to_number
        )
        logger.info(f"Proof submission process started for {to_number}")
        return f"Proof submission process started with SID: {message.sid}"
    except Exception as e:
        logger.error(f"Error starting proof submission for {to_number}: {e}")
        return f"Error starting proof submission: {e}"


@tool 
def process_proof_submission_response(phone_number: str, user_message: str, media_url: str = None) -> str:
    """
    Processes photo proof submission - simplified to match original WhatsApp Flow JSON.
    Expects: user sends photo -> proof recorded immediately.
    """
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

# =============================================================================
# VERIFICATION TOOLS (2 tools)
# =============================================================================

class VerificationResult(BaseModel):
    """Structure for verification results."""
    completed: bool = Field(description="Whether the goal was completed based on the image")
    confidence: float = Field(description="Confidence level (0-1) of the verification")
    reasoning: str = Field(description="Brief explanation of the verification decision")
    feedback: str = Field(description="Motivational feedback for the user")


@tool
def process_flow_response(flow_response_data: str, goal_description: str, user_phone: str) -> str:
    """
    Process WhatsApp Flow response with image data and validate goal completion.
    
    Args:
        flow_response_data: JSON string containing the flow response with image data
        goal_description: The user's goal that needs verification
        user_phone: User's phone number for logging
        
    Returns:
        JSON string with verification results
    """
    try:
        # Parse the flow response
        flow_data = json.loads(flow_response_data)
        
        # Extract image data from the flow response
        image_data = flow_data.get("image", "")
        if not image_data:
            return json.dumps({
                "completed": False,
                "confidence": 0.0,
                "reasoning": "No image data received",
                "feedback": "I didn't receive an image. Please try submitting your proof again."
            })
        
        # Initialize OpenAI model with vision capabilities
        model = ChatOpenAI(model="gpt-4o", temperature=0.1)
        
        # Create the verification prompt
        verification_prompt = f"""
        Analyze this image to determine if the user has completed their goal: "{goal_description}"
        
        You are an accountability coach reviewing proof of goal completion. Be encouraging but honest.
        
        Respond with a JSON object containing:
        - completed: boolean (true if goal appears completed based on image)
        - confidence: float between 0-1 (how confident you are in your assessment)
        - reasoning: string (brief explanation of your decision)
        - feedback: string (motivational feedback for the user, congratulatory if completed, encouraging if not)
        
        Be specific about what you see in the image that supports your decision.
        """
        
        # Create message with image
        message = HumanMessage(
            content=[
                {"type": "text", "text": verification_prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_data}"
                    }
                }
            ]
        )
        
        # Get verification result from OpenAI
        response = model.invoke([message])
        
        # Parse the response as JSON
        try:
            result = json.loads(response.content)
            
            # Validate the response structure
            verification_result = VerificationResult(**result)
            
            # Log the verification
            logger.info(f"Verification completed for user {user_phone}: {verification_result.completed}")
            
            return json.dumps(verification_result.dict())
            
        except (json.JSONDecodeError, Exception) as e:
            # Fallback response if JSON parsing fails
            logger.error(f"Error parsing OpenAI response: {e}")
            return json.dumps({
                "completed": False,
                "confidence": 0.5,
                "reasoning": "Unable to properly analyze the image",
                "feedback": "I had trouble analyzing your image. Please try submitting it again or contact support."
            })
        
    except Exception as e:
        logger.error(f"Error processing flow response: {e}")
        return json.dumps({
            "completed": False,
            "confidence": 0.0,
            "reasoning": f"Error processing verification: {str(e)}",
            "feedback": "There was an error processing your verification. Please try again."
        })


@tool
def create_verification_record(user_phone: str, verification_result: str, goal_description: str) -> str:
    """
    Create a verification record in the database.
    
    Args:
        user_phone: User's phone number
        verification_result: JSON string with verification results
        goal_description: The goal that was verified
        
    Returns:
        Success message
    """
    try:
        # Parse verification result
        result_data = json.loads(verification_result)
        
        # Create verification record
        verification_status = "completed" if result_data.get("completed", False) else "attempted"
        
        # Call the existing create_verification tool
        result = create_verification(
            phone_number=user_phone,
            due_date=date.today().strftime("%Y-%m-%d"),
            proof_url="flow_verification",  # Placeholder since we're not storing images
            justification=result_data.get("reasoning", "")
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error creating verification record: {e}")
        return f"Error creating verification record: {str(e)}"