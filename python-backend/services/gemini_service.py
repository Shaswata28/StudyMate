"""
Gemini API service for handling AI chat interactions.
Manages Gemini client initialization, conversation formatting, and API calls.
"""

import logging
from typing import List, Optional
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from google.api_core import exceptions as google_exceptions

from models.schemas import Message
from config import config

logger = logging.getLogger(__name__)


class GeminiServiceError(Exception):
    """Base exception for Gemini service errors."""
    pass


class GeminiAPIError(GeminiServiceError):
    """Exception for Gemini API-related errors."""
    pass


class GeminiTimeoutError(GeminiServiceError):
    """Exception for timeout errors."""
    pass


class GeminiService:
    """
    Service class for interacting with Google's Gemini API.
    Handles client initialization, conversation formatting, and API calls.
    """
    
    def __init__(self):
        """Initialize the Gemini service with API key from configuration."""
        self.model = None
        self._initialize_client()
    
    def _initialize_client(self):
        """
        Initialize the Gemini client with the API key from configuration.
        
        Raises:
            GeminiServiceError: If client initialization fails.
        """
        try:
            genai.configure(api_key=config.GEMINI_API_KEY)
            
            # Create generation config
            generation_config = GenerationConfig(
                temperature=config.GEMINI_TEMPERATURE,
                max_output_tokens=config.GEMINI_MAX_OUTPUT_TOKENS,
            )
            
            # Initialize the model
            self.model = genai.GenerativeModel(
                model_name=config.GEMINI_MODEL,
                generation_config=generation_config,
            )
            
            logger.info(f"Gemini client initialized successfully with model: {config.GEMINI_MODEL}")
            
        except Exception as e:
            error_msg = f"Failed to initialize Gemini client: {str(e)}"
            logger.error(error_msg)
            raise GeminiServiceError(error_msg) from e
    
    def format_conversation_history(self, history: List[Message]) -> List[dict]:
        """
        Format conversation history for Gemini API.
        Implements sliding window to keep only the last 10 messages.
        
        Args:
            history: List of Message objects from the chat request.
        
        Returns:
            List of dictionaries formatted for Gemini API with 'role' and 'parts' keys.
        """
        # Apply sliding window - keep only last 10 messages
        recent_history = history[-10:] if len(history) > 10 else history
        
        # Format for Gemini API
        formatted_history = []
        for msg in recent_history:
            formatted_history.append({
                "role": msg.role,
                "parts": [msg.content]
            })
        
        logger.debug(f"Formatted {len(formatted_history)} messages for Gemini API")
        return formatted_history
    
    def generate_response(
        self,
        message: str,
        history: Optional[List[Message]] = None
    ) -> str:
        """
        Call Gemini API with a message and optional conversation history.
        
        Args:
            message: The user's message to send to Gemini.
            history: Optional list of previous messages for context.
        
        Returns:
            The AI-generated response text.
        
        Raises:
            GeminiAPIError: If the API call fails.
            GeminiTimeoutError: If the API call times out.
        """
        if not self.model:
            raise GeminiServiceError("Gemini client not initialized")
        
        try:
            # Format conversation history if provided
            formatted_history = []
            if history:
                formatted_history = self.format_conversation_history(history)
            
            # Start a chat session with history
            chat = self.model.start_chat(history=formatted_history)
            
            # Send the message and get response with timeout
            logger.info(f"Sending message to Gemini API (history length: {len(formatted_history)})")
            
            response = chat.send_message(
                message,
                request_options={"timeout": config.GEMINI_TIMEOUT}
            )
            
            # Extract text from response
            response_text = response.text
            
            logger.info(f"Received response from Gemini API (length: {len(response_text)} chars)")
            return response_text
            
        except google_exceptions.DeadlineExceeded as e:
            error_msg = "I'm taking too long to respond. Please try again."
            logger.error(f"Gemini API timeout: {str(e)}")
            raise GeminiTimeoutError(error_msg) from e
            
        except google_exceptions.ResourceExhausted as e:
            error_msg = "I've reached my usage limit. Please try again later."
            logger.error(f"Gemini API quota exceeded: {str(e)}")
            raise GeminiAPIError(error_msg) from e
            
        except google_exceptions.InvalidArgument as e:
            error_msg = "I couldn't process your message. Please try rephrasing it."
            logger.error(f"Gemini API invalid argument: {str(e)}")
            raise GeminiAPIError(error_msg) from e
            
        except google_exceptions.PermissionDenied as e:
            error_msg = "I'm having authentication issues. Please contact support."
            logger.error(f"Gemini API permission denied: {str(e)}")
            raise GeminiAPIError(error_msg) from e
            
        except Exception as e:
            error_msg = "I'm having trouble connecting right now. Please try again."
            logger.error(f"Unexpected Gemini API error: {type(e).__name__}: {str(e)}")
            raise GeminiAPIError(error_msg) from e


# Global service instance
gemini_service = GeminiService()
