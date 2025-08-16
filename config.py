"""
Simple configuration management.
No over-engineering - just centralize environment variables.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Centralized configuration. No fancy validation yet."""
    
    # Database
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
    
    # Twilio
    TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_NUMBER = os.environ.get("TWILIO_WHATSAPP_NUMBER")
    
    # WhatsApp Flow
    WHATSAPP_FLOW_ID = os.environ.get("WHATSAPP_FLOW_ID")
    
    # OpenAI
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Global instance - simple and works
settings = Settings()