"""
Gemini AI Provider implementation.
Implements the AIProvider interface using Google's Gemini API for OCR, embeddings, and chat.
"""

import logging
import base64
from typing import List, Optional
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from google.api_core import exceptions as google_exceptions

from services.ai_provider import AIProvider, AIProviderError

logger = logging.getLogger(__name__)


class GeminiProvider(AIProvider):
    """
    Gemini API implementation of the AI provider interface.
    Provides OCR, embedding generation, and RAG-enabled chat using Google's Gemini API.
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-flash",
        embedding_model: str = "models/embedding-001",
        temperature: float = 0.7,
        max_output_tokens: int = 1024,
        timeout: int = 30,
        embedding_api_key: Optional[str] = None
    ):
        """
        Initialize the Gemini provider.
        
        Args:
            api_key: Gemini API key for authentication.
            model: Gemini model name for chat and OCR (default: gemini-1.5-flash).
            embedding_model: Gemini embedding model name (default: models/embedding-001).
            temperature: Temperature for text generation (0.0-1.0).
            max_output_tokens: Maximum tokens in generated responses.
            timeout: Request timeout in seconds.
            embedding_api_key: Optional separate API key for embeddings (defaults to api_key).
        
        Raises:
            AIProviderError: If initialization fails.
        """
        self.api_key = api_key
        self.embedding_api_key = embedding_api_key or api_key
        self.model_name = model
        self.embedding_model_name = embedding_model
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.timeout = timeout
        
        self._initialize_client()
    
    def _initialize_client(self):
        """
        Initialize the Gemini client with API key and configuration.
        
        Raises:
            AIProviderError: If client initialization fails.
        """
        try:
            # Configure Gemini API
            genai.configure(api_key=self.api_key)
            
            # Create generation config
            generation_config = GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_output_tokens,
            )
            
            # Initialize the generative model
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=generation_config,
            )
            
            logger.info(f"Gemini provider initialized successfully with model: {self.model_name}")
            
        except Exception as e:
            error_msg = f"Failed to initialize Gemini provider: {str(e)}"
            logger.error(error_msg)
            raise AIProviderError(error_msg) from e
    
    async def extract_text(self, file_data: bytes, mime_type: str) -> str:
        """
        Extract text from a file using Gemini's vision/PDF capabilities.
        
        Args:
            file_data: Raw bytes of the file (PDF, image, etc.).
            mime_type: MIME type of the file (e.g., 'application/pdf', 'image/jpeg').
        
        Returns:
            Extracted text content as a string. Returns empty string if no text found.
        
        Raises:
            AIProviderError: If text extraction fails.
        """
        try:
            logger.info(f"Extracting text from file (mime_type: {mime_type}, size: {len(file_data)} bytes)")
            
            # Prepare the file part for Gemini
            file_part = {
                "mime_type": mime_type,
                "data": file_data
            }
            
            # Create a prompt for OCR
            prompt = (
                "Extract all text content from this document. "
                "Return only the extracted text without any additional commentary or formatting. "
                "If there is no text in the document, return an empty response."
            )
            
            # Generate content with the file and prompt
            response = self.model.generate_content(
                [file_part, prompt],
                request_options={"timeout": self.timeout}
            )
            
            # Extract text from response
            extracted_text = response.text.strip() if response.text else ""
            
            logger.info(f"Text extraction completed (extracted {len(extracted_text)} characters)")
            return extracted_text
            
        except google_exceptions.DeadlineExceeded as e:
            error_msg = f"Text extraction timeout: {str(e)}"
            logger.error(error_msg)
            raise AIProviderError(error_msg) from e
            
        except google_exceptions.ResourceExhausted as e:
            error_msg = f"Gemini API quota exceeded during text extraction: {str(e)}"
            logger.error(error_msg)
            raise AIProviderError(error_msg) from e
            
        except google_exceptions.InvalidArgument as e:
            error_msg = f"Invalid file format for text extraction: {str(e)}"
            logger.error(error_msg)
            raise AIProviderError(error_msg) from e
            
        except Exception as e:
            error_msg = f"Text extraction failed: {type(e).__name__}: {str(e)}"
            logger.error(error_msg)
            raise AIProviderError(error_msg) from e
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate a vector embedding from text using Gemini's embedding model.
        
        Args:
            text: Text content to generate embedding for.
        
        Returns:
            List of floats representing the embedding vector (384 dimensions).
        
        Raises:
            AIProviderError: If embedding generation fails.
        """
        try:
            logger.info(f"Generating embedding for text (length: {len(text)} characters)")
            
            # Handle empty text
            if not text or not text.strip():
                logger.warning("Empty text provided for embedding generation")
                raise AIProviderError("Cannot generate embedding for empty text")
            
            # Temporarily configure with embedding API key if different
            original_api_key = None
            if self.embedding_api_key != self.api_key:
                original_api_key = self.api_key
                genai.configure(api_key=self.embedding_api_key)
            
            try:
                # Generate embedding using Gemini's embedding model
                result = genai.embed_content(
                    model=self.embedding_model_name,
                    content=text,
                    task_type="retrieval_document"
                )
                
                # Extract embedding vector
                embedding = result['embedding']
                
                logger.info(f"Embedding generated successfully (dimensions: {len(embedding)})")
                return embedding
            finally:
                # Restore original API key if it was changed
                if original_api_key:
                    genai.configure(api_key=original_api_key)
            
        except google_exceptions.DeadlineExceeded as e:
            error_msg = f"Embedding generation timeout: {str(e)}"
            logger.error(error_msg)
            raise AIProviderError(error_msg) from e
            
        except google_exceptions.ResourceExhausted as e:
            error_msg = f"Gemini API quota exceeded during embedding generation: {str(e)}"
            logger.error(error_msg)
            raise AIProviderError(error_msg) from e
            
        except google_exceptions.InvalidArgument as e:
            error_msg = f"Invalid text for embedding generation: {str(e)}"
            logger.error(error_msg)
            raise AIProviderError(error_msg) from e
            
        except Exception as e:
            error_msg = f"Embedding generation failed: {type(e).__name__}: {str(e)}"
            logger.error(error_msg)
            raise AIProviderError(error_msg) from e
    
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
            history: Optional conversation history (list of dicts with 'role' and 'parts').
        
        Returns:
            AI-generated response text.
        
        Raises:
            AIProviderError: If chat generation fails.
        """
        try:
            logger.info(f"Generating chat response (context items: {len(context)}, history: {len(history) if history else 0})")
            
            # Build the prompt with context
            prompt_parts = []
            
            # Add material context if provided
            if context and len(context) > 0:
                context_text = "\n\n".join([
                    f"Material {i+1}:\n{excerpt}"
                    for i, excerpt in enumerate(context)
                ])
                
                prompt_parts.append(
                    "You are a helpful AI assistant. Use the following course materials to help answer the user's question. "
                    "Reference the materials when relevant, but also use your general knowledge when appropriate.\n\n"
                    f"Course Materials:\n{context_text}\n\n"
                    f"User Question: {message}"
                )
            else:
                # No context, just use the message
                prompt_parts.append(message)
            
            # Format history for Gemini if provided
            formatted_history = []
            if history:
                # Apply sliding window - keep only last 10 messages
                recent_history = history[-10:] if len(history) > 10 else history
                formatted_history = recent_history
            
            # Start a chat session with history
            chat = self.model.start_chat(history=formatted_history)
            
            # Send the message and get response
            response = chat.send_message(
                prompt_parts,
                request_options={"timeout": self.timeout}
            )
            
            # Extract text from response
            response_text = response.text
            
            logger.info(f"Chat response generated successfully (length: {len(response_text)} characters)")
            return response_text
            
        except google_exceptions.DeadlineExceeded as e:
            error_msg = f"Chat generation timeout: {str(e)}"
            logger.error(error_msg)
            raise AIProviderError(error_msg) from e
            
        except google_exceptions.ResourceExhausted as e:
            error_msg = f"Gemini API quota exceeded during chat: {str(e)}"
            logger.error(error_msg)
            raise AIProviderError(error_msg) from e
            
        except google_exceptions.InvalidArgument as e:
            error_msg = f"Invalid chat request: {str(e)}"
            logger.error(error_msg)
            raise AIProviderError(error_msg) from e
            
        except Exception as e:
            error_msg = f"Chat generation failed: {type(e).__name__}: {str(e)}"
            logger.error(error_msg)
            raise AIProviderError(error_msg) from e
