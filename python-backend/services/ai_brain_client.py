"""
AI Brain Client for communicating with the local AI Brain service.
Provides OCR text extraction and embedding generation using local models.
"""

import logging
from typing import Optional
import httpx
import asyncio
from config import config

logger = logging.getLogger(__name__)


class AIBrainClientError(Exception):
    """Exception raised for AI Brain client errors."""
    pass


class AIBrainClient:
    """
    Client for communicating with the AI Brain service.
    
    The AI Brain service orchestrates specialized Ollama models:
    - qwen3-vl:2b for OCR text extraction
    - mxbai-embed-large for embedding generation
    """
    
    def __init__(
        self,
        brain_endpoint: str = "http://localhost:8001",
        timeout: float = 300.0
    ):
        """
        Initialize the AI Brain client.
        
        Args:
            brain_endpoint: Base URL of the AI Brain service (default: http://localhost:8001)
            timeout: Request timeout in seconds (default: 300.0 = 5 minutes for OCR)
        """
        self.brain_endpoint = brain_endpoint.rstrip('/')
        self.timeout = httpx.Timeout(timeout)
        
        logger.info(f"AI Brain client initialized (endpoint: {self.brain_endpoint}, timeout: {timeout}s)")
    
    async def health_check(self) -> bool:
        """
        Check if AI Brain service is available.
        
        Returns:
            True if service is healthy and responding, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.brain_endpoint}/")
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"AI Brain service health check passed: {data}")
                    return True
                else:
                    logger.warning(f"AI Brain service returned status {response.status_code}")
                    return False
                    
        except httpx.ConnectError as e:
            logger.error(f"AI Brain service connection failed: {e}")
            return False
        except httpx.TimeoutException as e:
            logger.error(f"AI Brain service health check timeout: {e}")
            return False
        except Exception as e:
            logger.error(f"AI Brain service health check error: {e}")
            return False
    
    async def extract_text(
        self,
        file_data: bytes,
        filename: str,
        prompt: str = "Extract all text from this document",
        retry_on_failure: bool = True
    ) -> str:
        """
        Extract text from a file using AI Brain's OCR endpoint with retry logic.
        
        Args:
            file_data: File content as bytes
            filename: Original filename (used for content type detection)
            prompt: Instruction prompt for OCR (default: "Extract all text from this document")
            retry_on_failure: Whether to retry on transient failures (default: True)
        
        Returns:
            Extracted text content as a string. Returns empty string if no text found.
        
        Raises:
            AIBrainClientError: If text extraction fails or service is unavailable
        """
        last_error = None
        max_attempts = config.MAX_RETRY_ATTEMPTS if retry_on_failure else 1
        
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(
                    f"Extracting text from file: {filename} ({len(file_data)} bytes) "
                    f"[Attempt {attempt}/{max_attempts}]"
                )
                
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    # Prepare multipart form data
                    files = {"image": (filename, file_data)}
                    data = {"prompt": prompt}
                    
                    # Send request to AI Brain /router endpoint
                    response = await client.post(
                        f"{self.brain_endpoint}/router",
                        files=files,
                        data=data
                    )
                    
                    # Check for HTTP errors
                    response.raise_for_status()
                    
                    # Parse response
                    result = response.json()
                    extracted_text = result.get("response", "")
                    
                    logger.info(
                        f"Text extraction completed successfully: {len(extracted_text)} characters extracted "
                        f"[Attempt {attempt}/{max_attempts}]"
                    )
                    return extracted_text
                    
            except httpx.ConnectError as e:
                error_msg = f"AI Brain service unavailable (connection error)"
                logger.error(f"{error_msg}: {e} [Attempt {attempt}/{max_attempts}]")
                last_error = AIBrainClientError(error_msg)
                
                # Retry on connection errors (transient)
                if attempt < max_attempts:
                    delay = config.RETRY_DELAY_SECONDS * (config.RETRY_BACKOFF_MULTIPLIER ** (attempt - 1))
                    logger.info(f"Retrying in {delay:.1f} seconds...")
                    await asyncio.sleep(delay)
                    continue
                    
            except httpx.TimeoutException as e:
                error_msg = f"Text extraction timeout after {self.timeout.read}s"
                logger.error(f"{error_msg}: {e} [Attempt {attempt}/{max_attempts}]")
                last_error = AIBrainClientError(error_msg)
                
                # Don't retry on timeout - it's likely the file is too large or complex
                break
                
            except httpx.HTTPStatusError as e:
                error_msg = f"Text extraction HTTP error {e.response.status_code}"
                logger.error(f"{error_msg}: {e} [Attempt {attempt}/{max_attempts}]")
                
                # Retry on 5xx errors (server errors), but not 4xx (client errors)
                if 500 <= e.response.status_code < 600 and attempt < max_attempts:
                    delay = config.RETRY_DELAY_SECONDS * (config.RETRY_BACKOFF_MULTIPLIER ** (attempt - 1))
                    logger.info(f"Server error, retrying in {delay:.1f} seconds...")
                    await asyncio.sleep(delay)
                    last_error = AIBrainClientError(error_msg)
                    continue
                else:
                    # Don't retry on 4xx errors
                    raise AIBrainClientError(error_msg) from e
                    
            except Exception as e:
                error_msg = f"Text extraction failed: {type(e).__name__}"
                logger.error(f"{error_msg}: {e} [Attempt {attempt}/{max_attempts}]", exc_info=True)
                last_error = AIBrainClientError(f"{error_msg}: {e}")
                
                # Retry on unexpected errors
                if attempt < max_attempts:
                    delay = config.RETRY_DELAY_SECONDS * (config.RETRY_BACKOFF_MULTIPLIER ** (attempt - 1))
                    logger.info(f"Unexpected error, retrying in {delay:.1f} seconds...")
                    await asyncio.sleep(delay)
                    continue
        
        # If we exhausted all retries, raise the last error
        if last_error:
            logger.error(f"Text extraction failed after {max_attempts} attempts")
            raise last_error
        
        # Should never reach here, but just in case
        raise AIBrainClientError("Text extraction failed for unknown reason")
    
    async def generate_embedding(self, text: str, retry_on_failure: bool = True) -> list[float]:
        """
        Generate vector embedding from text using AI Brain's embedding endpoint with retry logic.
        
        Args:
            text: Text content to generate embedding for
            retry_on_failure: Whether to retry on transient failures (default: True)
        
        Returns:
            Embedding vector as a list of floats (1024 dimensions for mxbai-embed-large)
        
        Raises:
            AIBrainClientError: If embedding generation fails or service is unavailable
        """
        # Validate input
        if not text or not text.strip():
            error_msg = "Cannot generate embedding for empty text"
            logger.error(error_msg)
            raise AIBrainClientError(error_msg)
        
        last_error = None
        max_attempts = config.MAX_RETRY_ATTEMPTS if retry_on_failure else 1
        
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(
                    f"Generating embedding for text ({len(text)} characters) "
                    f"[Attempt {attempt}/{max_attempts}]"
                )
                
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    # Send request to AI Brain /utility/embed endpoint
                    # Note: The endpoint expects query parameters
                    response = await client.post(
                        f"{self.brain_endpoint}/utility/embed",
                        params={"text": text}
                    )
                    
                    # Check for HTTP errors
                    response.raise_for_status()
                    
                    # Parse response
                    result = response.json()
                    embedding = result.get("embedding", [])
                    
                    if not embedding:
                        error_msg = "AI Brain service returned empty embedding"
                        logger.error(f"{error_msg} [Attempt {attempt}/{max_attempts}]")
                        raise AIBrainClientError(error_msg)
                    
                    logger.info(
                        f"Embedding generated successfully ({len(embedding)} dimensions) "
                        f"[Attempt {attempt}/{max_attempts}]"
                    )
                    return embedding
                    
            except httpx.ConnectError as e:
                error_msg = f"AI Brain service unavailable (connection error)"
                logger.error(f"{error_msg}: {e} [Attempt {attempt}/{max_attempts}]")
                last_error = AIBrainClientError(error_msg)
                
                # Retry on connection errors (transient)
                if attempt < max_attempts:
                    delay = config.RETRY_DELAY_SECONDS * (config.RETRY_BACKOFF_MULTIPLIER ** (attempt - 1))
                    logger.info(f"Retrying in {delay:.1f} seconds...")
                    await asyncio.sleep(delay)
                    continue
                    
            except httpx.TimeoutException as e:
                error_msg = f"Embedding generation timeout after {self.timeout.read}s"
                logger.error(f"{error_msg}: {e} [Attempt {attempt}/{max_attempts}]")
                last_error = AIBrainClientError(error_msg)
                
                # Retry on timeout for embeddings (they should be fast)
                if attempt < max_attempts:
                    delay = config.RETRY_DELAY_SECONDS * (config.RETRY_BACKOFF_MULTIPLIER ** (attempt - 1))
                    logger.info(f"Timeout, retrying in {delay:.1f} seconds...")
                    await asyncio.sleep(delay)
                    continue
                    
            except httpx.HTTPStatusError as e:
                error_msg = f"Embedding generation HTTP error {e.response.status_code}"
                logger.error(f"{error_msg}: {e} [Attempt {attempt}/{max_attempts}]")
                
                # Retry on 5xx errors (server errors), but not 4xx (client errors)
                if 500 <= e.response.status_code < 600 and attempt < max_attempts:
                    delay = config.RETRY_DELAY_SECONDS * (config.RETRY_BACKOFF_MULTIPLIER ** (attempt - 1))
                    logger.info(f"Server error, retrying in {delay:.1f} seconds...")
                    await asyncio.sleep(delay)
                    last_error = AIBrainClientError(error_msg)
                    continue
                else:
                    # Don't retry on 4xx errors
                    raise AIBrainClientError(error_msg) from e
                    
            except Exception as e:
                error_msg = f"Embedding generation failed: {type(e).__name__}"
                logger.error(f"{error_msg}: {e} [Attempt {attempt}/{max_attempts}]", exc_info=True)
                last_error = AIBrainClientError(f"{error_msg}: {e}")
                
                # Retry on unexpected errors
                if attempt < max_attempts:
                    delay = config.RETRY_DELAY_SECONDS * (config.RETRY_BACKOFF_MULTIPLIER ** (attempt - 1))
                    logger.info(f"Unexpected error, retrying in {delay:.1f} seconds...")
                    await asyncio.sleep(delay)
                    continue
        
        # If we exhausted all retries, raise the last error
        if last_error:
            logger.error(f"Embedding generation failed after {max_attempts} attempts")
            raise last_error
        
        # Should never reach here, but just in case
        raise AIBrainClientError("Embedding generation failed for unknown reason")
