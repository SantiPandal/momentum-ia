# tools/database_tools.py

from langchain_core.tools import tool
from pydantic import BaseModel, Field
from supabase import create_client, Client
import os
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Supabase client
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# --- Tool 1: get_user_status (Updated for new schema) ---
@tool
def get_user_status(phone_number: str) -> str:
    """
    Looks up a user by their phone number.
    If the user does not exist, it creates a new user record.
    It returns one of three statuses:
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
                print(f"New user created: {phone_number}")
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
        print(f"Error checking user status: {e}")
        return "error_database_check"


# --- Tool 2: update_user_name (Same - no changes needed) ---
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
            print(f"Updated name for {phone_number} to {name}")
            return f"Successfully updated user's name to {name}."
        else:
            return "Error: Could not find user to update."
    except Exception as e:
        print(f"Error updating user name: {e}")
        return "Error updating name in database."
    

# --- Tool 3: create_commitment (Updated from create_challenge) ---
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
            commitment_id = commitment_response.data[0]["id"]
            print(f"Commitment created for {phone_number}: {goal_description}")
            return f"Successfully created commitment! Goal: {goal_description}, Stake: ${stake_amount} ({stake_type}), Period: {start_date} to {end_date}"
        else:
            return "Error: Could not create commitment."
            
    except Exception as e:
        print(f"Error creating commitment: {e}")
        return "Error creating commitment in database."


# --- Tool 4: get_active_commitment (New tool) ---
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
        print(f"Error getting active commitment: {e}")
        return "Error retrieving commitment details."


# --- Tool 5: create_verification (New tool) ---
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
        print(f"Error creating verification: {e}")
        return "Error creating verification record."


# --- Tool 6: manage_proof_submission_state (New tool for state-based proof collection) ---
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
            print(f"⚠️ Proof columns don't exist, using basic user lookup: {schema_error}")
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
        print(f"Error managing proof submission state: {e}")
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
            print(f"⚠️ Proof columns don't exist in get_proof_submission_state: {schema_error}")
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
        print(f"Error getting proof submission state: {e}")
        return "Error retrieving proof submission state"