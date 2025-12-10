"""
Local AI service for handling AI chat interactions with the brain service.
Replaces Gemini API with local AI brain service running on port 8001.
"""

import logging
import base64
from typing import List, Optional
import httpx

from models.schemas import Message, FileAttachment

logger = logging.getLogger(__name__)


class LocalAIServiceError(Exception):
    """Base exception for Local AI service errors."""
    pass


class LocalAIAPIError(LocalAIServiceError):
    """Exception for Local AI API-related errors."""
    pass


class LocalAITimeoutError(LocalAIServiceError):
    """Exception for timeout errors."""
    pass


class LocalAIService:
    """
    Service class for interacting with the local AI brain service.
    Handles HTTP communication with the brain service and provides
    a drop-in replacement for GeminiService.
    """
    
    def __init__(self, brain_url: str = "http://localhost:8001"):
        """
        Initialize the Local AI service.
        
        Args:
            brain_url: URL of the brain service (default: http://localhost:8001)
        """
        self.brain_url = brain_url
        self.client = httpx.AsyncClient(timeout=300.0)  # 5 minutes for large document processing
        logger.info(f"Local AI service initialized with brain URL: {self.brain_url}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - close HTTP client."""
        await self.client.aclose()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    def format_conversation_history(self, history: List[Message]) -> List[dict]:
        """
        Format conversation history for compatibility.
        Implements sliding window to keep only the last 10 messages.
        
        Note: The brain service doesn't currently use history, but this method
        maintains interface compatibility with GeminiService.
        
        Args:
            history: List of Message objects from the chat request.
        
        Returns:
            List of dictionaries formatted with 'role' and 'parts' keys.
        """
        # Apply sliding window - keep only last 10 messages
        recent_history = history[-10:] if len(history) > 10 else history
        
        # Format for compatibility
        formatted_history = []
        for msg in recent_history:
            formatted_history.append({
                "role": msg.role,
                "parts": [msg.content]
            })
        
        logger.debug(f"Formatted {len(formatted_history)} messages")
        return formatted_history

    async def generate_response(
        self,
        message: str,
        history: Optional[List[Message]] = None,
        attachments: Optional[List[FileAttachment]] = None
    ) -> str:
        """
        Call the brain service with a message and optional attachments.
        
        This method provides a drop-in replacement for GeminiService.generate_response().
        It sends requests to the brain service's /router endpoint with text, image,
        or audio attachments.
        
        Args:
            message: The user's message to send to the brain service.
            history: Optional list of previous messages (currently not used by brain).
            attachments: Optional list of file attachments (images/audio).
        
        Returns:
            The AI-generated response text.
        
        Raises:
            LocalAIAPIError: If the API call fails.
            LocalAITimeoutError: If the API call times out.
        """
        try:
            # Prepare multipart form data
            files = {}
            data = {"prompt": message}
            
            # Process attachments
            if attachments:
                for idx, attachment in enumerate(attachments):
                    try:
                        # Decode base64 data
                        file_data = base64.b64decode(attachment.data)
                        
                        # Determine if it's an image, PDF, or audio file
                        if attachment.mime_type.startswith("image/") or attachment.mime_type == "application/pdf":
                            # Send image or PDF (brain service accepts one image/PDF)
                            if "image" not in files:
                                files["image"] = (
                                    attachment.filename,
                                    file_data,
                                    attachment.mime_type
                                )
                                file_type = "PDF" if attachment.mime_type == "application/pdf" else "image"
                                logger.debug(f"Added {file_type} attachment: {attachment.filename}")
                        elif attachment.mime_type.startswith("audio/"):
                            # Only send the first audio file (brain service accepts one audio)
                            if "audio" not in files:
                                files["audio"] = (
                                    attachment.filename,
                                    file_data,
                                    attachment.mime_type
                                )
                                logger.debug(f"Added audio attachment: {attachment.filename}")
                        else:
                            logger.warning(f"Unsupported attachment type: {attachment.mime_type}")
                    
                    except Exception as e:
                        logger.error(f"Failed to process attachment {attachment.filename}: {str(e)}")
                        raise LocalAIServiceError(f"Failed to process file: {attachment.filename}")
            
            # Log request details
            logger.info(
                f"Sending request to brain service - "
                f"Message length: {len(message)}, "
                f"Has image: {'image' in files}, "
                f"Has audio: {'audio' in files}"
            )
            
            # Send request to brain service
            response = await self.client.post(
                f"{self.brain_url}/router",
                data=data,
                files=files if files else None
            )
            
            # Check for HTTP errors
            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"Brain service returned error {response.status_code}: {error_detail}")
                raise LocalAIAPIError(f"Brain service error: {error_detail}")
            
            # Parse response
            response_data = response.json()
            response_text = response_data.get("response", "")
            model_used = response_data.get("model", "unknown")
            
            logger.info(f"Received response from brain service (model: {model_used}, length: {len(response_text)} chars)")
            return response_text
        
        except httpx.TimeoutException as e:
            error_msg = "I'm taking too long to respond. Please try again."
            logger.error(f"Brain service timeout: {str(e)}")
            raise LocalAITimeoutError(error_msg) from e
        
        except httpx.ConnectError as e:
            error_msg = "I'm having trouble connecting to the AI service. Please ensure the brain service is running."
            logger.error(f"Brain service connection error: {str(e)}")
            raise LocalAIAPIError(error_msg) from e
        
        except httpx.HTTPStatusError as e:
            error_msg = "I'm having trouble processing your request. Please try again."
            logger.error(f"Brain service HTTP error: {str(e)}")
            raise LocalAIAPIError(error_msg) from e
        
        except LocalAIServiceError:
            # Re-raise our own exceptions
            raise
        
        except Exception as e:
            error_msg = "I'm having trouble connecting right now. Please try again."
            logger.error(f"Unexpected brain service error: {type(e).__name__}: {str(e)}")
            raise LocalAIAPIError(error_msg) from e

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for the given text.
        
        Sends a request to the brain service's /utility/embed endpoint
        to generate a vector representation of the text.
        
        Args:
            text: The text to generate an embedding for.
        
        Returns:
            List of floating-point numbers representing the embedding vector.
        
        Raises:
            LocalAIAPIError: If the API call fails.
            LocalAITimeoutError: If the API call times out.
        """
        try:
            logger.info(f"Generating embedding for text (length: {len(text)} chars)")
            
            # Send request to brain service
            response = await self.client.post(
                f"{self.brain_url}/utility/embed",
                json={"text": text}
            )
            
            # Check for HTTP errors
            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"Brain service returned error {response.status_code}: {error_detail}")
                raise LocalAIAPIError(f"Embedding generation failed: {error_detail}")
            
            # Parse response
            response_data = response.json()
            embedding = response_data.get("embedding", [])
            
            logger.info(f"Received embedding vector (dimension: {len(embedding)})")
            return embedding
        
        except httpx.TimeoutException as e:
            error_msg = "Embedding generation timed out. Please try again."
            logger.error(f"Brain service timeout: {str(e)}")
            raise LocalAITimeoutError(error_msg) from e
        
        except httpx.ConnectError as e:
            error_msg = "Cannot connect to the AI service for embedding generation."
            logger.error(f"Brain service connection error: {str(e)}")
            raise LocalAIAPIError(error_msg) from e
        
        except Exception as e:
            error_msg = "Failed to generate embedding. Please try again."
            logger.error(f"Unexpected embedding error: {type(e).__name__}: {str(e)}")
            raise LocalAIAPIError(error_msg) from e
    
    async def health_check(self) -> bool:
        """
        Check if the brain service is available and responding.
        
        Returns:
            True if the brain service is healthy, False otherwise.
        """
        try:
            response = await self.client.get(f"{self.brain_url}/")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Brain service health check failed: {str(e)}")
            return False


# Global service instance
local_ai_service = LocalAIService()
