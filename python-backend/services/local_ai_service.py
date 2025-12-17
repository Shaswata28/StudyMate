"""
Local AI service for handling AI chat interactions with the brain service.
Replaces Gemini API with local AI brain service running on port 8001.
"""

import logging
import base64
from typing import List, Optional
import httpx

from models.schemas import FileAttachment

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
    
    async def generate_chat_response(
        self,
        messages: List[dict],
        attachments: Optional[List[FileAttachment]] = None
    ) -> str:
        """
        Generate response using ChatML format (messages list).
        
        This method sends a list of messages to the brain service's /chat endpoint,
        which uses ollama.chat() API for proper conversation handling.
        
        Args:
            messages: List of {"role": "system/user/assistant", "content": "..."}
            attachments: Optional file attachments (not yet supported in chat mode)
        
        Returns:
            The AI-generated response text.
        
        Raises:
            LocalAIAPIError: If the API call fails.
            LocalAITimeoutError: If the API call times out.
        """
        try:
            logger.info(f"Sending chat request with {len(messages)} messages")
            
            # Prepare payload
            payload = {
                "messages": messages,
                "model": "studymate"
            }
            
            # Send request to brain service /chat endpoint
            response = await self.client.post(
                f"{self.brain_url}/chat",
                json=payload
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
            
            logger.info(f"Received chat response (model: {model_used}, length: {len(response_text)} chars)")
            return response_text
        
        except httpx.TimeoutException as e:
            error_msg = "I'm taking too long to respond. Please try again."
            logger.error(f"Brain service timeout: {str(e)}")
            raise LocalAITimeoutError(error_msg) from e
        
        except httpx.ConnectError as e:
            error_msg = "I'm having trouble connecting to the AI service. Please ensure the brain service is running."
            logger.error(f"Brain service connection error: {str(e)}")
            raise LocalAIAPIError(error_msg) from e
        
        except LocalAIServiceError:
            # Re-raise our own exceptions
            raise
        
        except Exception as e:
            error_msg = "I'm having trouble connecting right now. Please try again."
            logger.error(f"Unexpected brain service error: {type(e).__name__}: {str(e)}")
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
