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
        
        # If user exists, check for an active goal (we'll build this logic out more later)
        # For now, if their name is missing, we'll assume they need to finish basic onboarding.
        user = response.data[0]
        if not user.get("name"):
             return "new_user" # Treat them as new if they don't have a name yet.

        # Here we would check the 'commitments' table. For now, we'll assume no active goal.
        # This is where you would add a query to your commitments table later.
        has_active_goal = False 

        if has_active_goal:
            return "user_exists_active_goal"
        else:
            return "user_exists_no_goal"

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