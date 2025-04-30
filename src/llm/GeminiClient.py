from google import genai
from google.genai import types
import os
from typing import List, Optional, Generator, Any
from dotenv import load_dotenv

class GeminiClient:
    """Client for processing content with Google Gemini AI"""
    
    # System instruction for transcript processing (only used for chat)
    SYSTEM_INSTRUCTION = """
    You are an expert in the field being discussed. 
    Explain concepts clearly and directly, and keeping things minimalistic.
    Use first principles thinking and analogies.
    Keep the structure logical and sequential.

    Use vocabulary and style matching the provided context.
    Use minimal amount of emojis and icons to make it easier to understand and interperate.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize client with API key from parameter or environment"""
        load_dotenv()
        
        # Get API key with explicit error handling
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables. Please check your .env file.")
        
        print(f"Initializing Gemini client with API key: {self.api_key[:3]}...{self.api_key[-2:]}")
        self.client = genai.Client(api_key=self.api_key)
        self.chat = None
    
    def create_chat(self, model: str = "gemini-2.0-flash", system_instructions: str = SYSTEM_INSTRUCTION):
        """Create a new chat session with system instruction"""
        self.chat = self.client.chats.create(
            model=model,
            config=types.GenerateContentConfig(
                system_instruction=system_instructions,
                temperature=0.9
            )
        )
        return self.chat
    
    def send_message_stream(self, content: str) -> Generator:
        """Send a message to the chat and stream the response"""
        if not self.chat:
            self.create_chat()
        
        try:
            return self.chat.send_message_stream(content)
        except Exception as e:
            def error_generator():
                yield types.GenerateContentResponse(text=f"Error: {str(e)}")
            return error_generator()
    
    def generate_content(self, model: str, contents: List) -> Any:
        """Generate content directly without chat context
        
        This method calls the models API directly for one-time generation 
        without using any chat history or system instructions.
        Used for image processing, PDF conversion, etc.
        
        Args:
            model: Name of the model to use (e.g., "gemini-2.0-flash")
            contents: List of content parts (text, images, etc.)
            
        Returns:
            Generation response
        """
        try:
            # Direct model call without chat context or system instructions
            response = self.client.models.generate_content(
                model=model,
                contents=contents
            )
            return response
        except Exception as e:
            # Provide more informative error that mimics the response structure
            error_message = f"Error generating content: {str(e)}"
            print(error_message)  # Log the error
            
            # Return a similar error structure as the chat method to maintain consistency
            class ErrorResponse:
                def __init__(self, error_text):
                    self.text = error_text
            
            return ErrorResponse(error_message)
