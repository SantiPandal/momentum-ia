"""
Verification tools for processing WhatsApp Flow responses and validating images.
"""
import json
import base64
from typing import Dict, Any
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field


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
            print(f"Verification completed for user {user_phone}: {verification_result.completed}")
            
            return json.dumps(verification_result.dict())
            
        except (json.JSONDecodeError, Exception) as e:
            # Fallback response if JSON parsing fails
            print(f"Error parsing OpenAI response: {e}")
            return json.dumps({
                "completed": False,
                "confidence": 0.5,
                "reasoning": "Unable to properly analyze the image",
                "feedback": "I had trouble analyzing your image. Please try submitting it again or contact support."
            })
        
    except Exception as e:
        print(f"Error processing flow response: {e}")
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
        # Import here to avoid circular imports
        from services.tools.database_tools import create_verification
        
        # Parse verification result
        result_data = json.loads(verification_result)
        
        # Create verification record
        verification_status = "completed" if result_data.get("completed", False) else "attempted"
        
        # Call the existing create_verification tool
        result = create_verification(
            user_phone=user_phone,
            status=verification_status,
            proof_url="flow_verification",  # Placeholder since we're not storing images
            notes=result_data.get("reasoning", "")
        )
        
        return result
        
    except Exception as e:
        print(f"Error creating verification record: {e}")
        return f"Error creating verification record: {str(e)}"