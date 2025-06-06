# tools/database_tools.py

from langchain_core.tools import tool
from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize the Supabase client
# Assumes SUPABASE_URL and SUPABASE_KEY are in your .env file
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

@tool
def get_user_status(phone_number: str) -> str:
    """
    Looks up a user by their phone number to see if they exist and if their onboarding is complete.
    Returns one of three statuses: 'new_user', 'onboarding_incomplete', or 'onboarding_complete'.
    """
    try:
        # Supabase query to find the user
        response = supabase.table("users").select("id", "onboarding_completed").eq("phone_number", phone_number).execute()

        if not response.data:
            # No user found, so we need to create one
            user_data = {"phone_number": phone_number, "onboarding_completed": False}
            insert_response = supabase.table("users").insert(user_data).execute()
            if insert_response.data:
                print(f"New user created: {phone_number}")
                return "new_user"
            else:
                return "error_creating_user"

        user = response.data[0]
        if user.get("onboarding_completed"):
            return "onboarding_complete"
        else:
            return "onboarding_incomplete"

    except Exception as e:
        print(f"Error checking user status: {e}")
        return "error_database_check"


# We will add more tools here later, like save_goal, get_commitment, etc.