# tools/database_tools.py

from langchain_core.tools import tool
from pydantic import BaseModel, Field
from supabase import create_client, Client
import os

# Initialize Supabase client
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# --- Tool 1: get_user_status (Now Smarter) ---
@tool
def get_user_status(phone_number: str) -> str:
    """
    Looks up a user by their phone number.
    If the user does not exist, it creates a new user record.
    It returns one of three statuses:
    - 'new_user': For users messaging for the very first time.
    - 'user_exists_no_goal': For existing users who do not have an active goal.
    - 'user_exists_active_goal': For existing users who have an active goal.
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
        
        # If user exists, check if they have completed onboarding
        user = response.data[0]
        if not user.get("name"):
             return "new_user" # Treat them as new if they don't have a name yet.

        # Check if user has active challenges
        challenges_response = supabase.table("challenges").select("id").eq("user_id", user["id"]).eq("status", "active").execute()
        
        has_active_goal = len(challenges_response.data) > 0

        if has_active_goal:
            return f"user_exists_active_goal:{user.get('name', 'User')}"
        else:
            return f"user_exists_no_goal:{user.get('name', 'User')}"

    except Exception as e:
        print(f"Error checking user status: {e}")
        return "error_database_check"


# --- Tool 2: update_user_name (Brand New) ---
class UpdateUserNameArgs(BaseModel):
    phone_number: str = Field(description="The user's phone number, including the 'whatsapp:' prefix.")
    name: str = Field(description="The user's first name to save.")

@tool(args_schema=UpdateUserNameArgs)
def update_user_name(phone_number: str, name: str) -> str:
    """
    Updates the user's record with their name after they provide it during onboarding.
    """
    try:
        response = supabase.table("users").update({"name": name, "onboarding_completed": True}).eq("phone_number", phone_number).execute()
        if response.data:
            print(f"Updated name for {phone_number} to {name}")
            return f"Successfully updated user's name to {name}."
        else:
            # This might happen if the phone number somehow doesn't exist, which is unlikely
            return "Error: Could not find user to update."
    except Exception as e:
        print(f"Error updating user name: {e}")
        return "Error updating name in database."
    
# --- Tool 3: create_challenge ---
class CreateChallengeArgs(BaseModel):
    phone_number: str = Field(description="The user's phone number to identify them.")
    goal_description: str = Field(description="Description of the goal/challenge.")
    stake_amount: float = Field(description="Amount the user is willing to stake/risk.")
    target_date: str = Field(description="Target completion date in YYYY-MM-DD format.")
    verification_method: dict = Field(description="How the goal will be verified (e.g., {'type': 'photo', 'description': 'Before/after photos'}).", default={})

@tool(args_schema=CreateChallengeArgs)
def create_challenge(phone_number: str, goal_description: str, stake_amount: float, target_date: str, verification_method: dict = {}) -> str:
    """
    Creates a new challenge/goal for a user with a stake amount and target date.
    """
    try:
        # First, find the user by phone number to get their user_id
        user_response = supabase.table("users").select("id").eq("phone_number", phone_number).execute()
        
        if not user_response.data:
            return "Error: User not found. Please make sure the user is registered first."
        
        user_id = user_response.data[0]["id"]
        
        # Create the challenge
        challenge_data = {
            "user_id": user_id,
            "goal_description": goal_description,
            "stake_amount": stake_amount,
            "target_date": target_date,
            "verification_method": verification_method
        }
        
        challenge_response = supabase.table("challenges").insert(challenge_data).execute()
        
        if challenge_response.data:
            challenge_id = challenge_response.data[0]["id"]
            print(f"Challenge created for {phone_number}: {goal_description}")
            return f"Successfully created challenge! Challenge ID: {challenge_id}. Goal: {goal_description}, Stake: ${stake_amount}, Target: {target_date}"
        else:
            return "Error: Could not create challenge."
            
    except Exception as e:
        print(f"Error creating challenge: {e}")
        return "Error creating challenge in database."