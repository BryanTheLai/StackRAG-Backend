from google import genai
from google.genai import types
import os
from typing import List, Optional, Generator, Any
from dotenv import load_dotenv
from src.prompts.prompt_manager import PromptManager
from src.config.gemini_config import DEFAULT_CHAT_MODEL

class GeminiClient:
    """Client for interacting with Google Gemini AI."""
    
    GEMINI_CHAT_SYSTEM_PROMPT = PromptManager.get_prompt(
        "chat_system_prompt"
    )
    def __init__(self, api_key: Optional[str] = None):
        """Initialize client with API key."""
        load_dotenv()
        
        # Load API key from environment or argument.
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")
        
        print(f"Initializing Gemini client with API key: {self.api_key[:3]}...{self.api_key[-2:]}")
        self.client = genai.Client(api_key=self.api_key)
        self.chat = None
    
    def create_chat(self, model: str = DEFAULT_CHAT_MODEL, system_instructions: str = GEMINI_CHAT_SYSTEM_PROMPT):
        """Create a new chat session."""
        self.chat = self.client.chats.create(
            model=model,
            config=types.GenerateContentConfig(
                system_instruction=system_instructions,
                temperature=0.5
            )
        )
        return self.chat
    
    def send_message_stream(self, content: str) -> Generator:
        """Send message to chat and stream response."""
        if not self.chat:
            self.create_chat()
        
        try:
            return self.chat.send_message_stream(content)
        except Exception as e:
            def error_generator():
                yield types.GenerateContentResponse(text=f"Error: {str(e)}")
            return error_generator()
    
    def generate_content(self, model: str, contents: List) -> Any:
        """Generate content directly (non-chat).
        
        Use for image processing, structured outputs, etc.
        
        Args:
            model: Model name.
            contents: Content parts (text, image).
            
        Returns:
            API response.
        """
        try:
            # Direct model call without chat history.
            response = self.client.models.generate_content(
                model=model,
                contents=contents
            )
            return response
        except Exception as e:
            # Return consistent error format.
            error_message = f"Error generating content: {str(e)}"
            print(error_message)
            
            class ErrorResponse:
                def __init__(self, error_text):
                    self.text = error_text
            
            return ErrorResponse(error_message)