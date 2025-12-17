"""
AI Provider abstraction layer for OCR, embeddings, and chat functionality.
Supports multiple AI providers (Gemini, Router, etc.) through a common interface.
"""

from abc import ABC, abstractmethod
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class AIProviderError(Exception):
    """Base exception for AI provider errors."""
    pass


class AIProvider(ABC):
    """
    Abstract interface for AI providers.
    Implementations must provide OCR, embedding generation, and chat capabilities.
    """
    
    @abstractmethod
    async def extract_text(self, file_data: bytes, mime_type: str) -> str:
        """
        Extract text from a file using OCR capabilities.
        
        Args:
            file_data: Raw bytes of the file (PDF, image, etc.)
            mime_type: MIME type of the file (e.g., 'application/pdf', 'image/jpeg')
        
        Returns:
            Extracted text content as a string. Returns empty string if no text found.
        
        Raises:
            AIProviderError: If text extraction fails.
        """
        pass
    
    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate a vector embedding from text.
        
        Args:
            text: Text content to generate embedding for.
        
        Returns:
            List of floats representing the embedding vector (384 dimensions).
        
        Raises:
            AIProviderError: If embedding generation fails.
        """
        pass
    
    @abstractmethod
    async def chat_with_context(
        self,
        message: str,
        context: List[str],
        history: Optional[List] = None
    ) -> str:
        """
        Generate a chat response with material context (RAG).
        
        Args:
            message: User's chat message.
            context: List of material excerpts to use as context.
            history: Optional conversation history.
        
        Returns:
            AI-generated response text.
        
        Raises:
            AIProviderError: If chat generation fails.
        """
        pass
