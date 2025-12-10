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

    async def verify_connection(self) -> bool:
        """
        Verify AI Brain service is accessible and responding properly.
        
        This method performs a comprehensive connection verification including:
        - Basic connectivity test
        - Service response validation
        - Endpoint availability check
        
        Returns:
            True if service is fully operational, False otherwise
        """
        try:
            logger.info("Starting AI Brain service connection verification")
            
            # Test basic connectivity with timeout
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                # Test root endpoint
                response = await client.get(f"{self.brain_endpoint}/")
                
                if response.status_code != 200:
                    logger.error(f"AI Brain service connection verification failed: HTTP {response.status_code}")
                    return False
                
                # Validate response structure
                try:
                    data = response.json()
                    if not isinstance(data, dict):
                        logger.error("AI Brain service returned invalid response format")
                        return False
                    
                    logger.info(f"AI Brain service connection verified successfully: {data}")
                    return True
                    
                except ValueError as e:
                    logger.error(f"AI Brain service returned invalid JSON: {e}")
                    return False
                    
        except httpx.ConnectError as e:
            logger.error(f"AI Brain service connection verification failed - service unavailable: {e}")
            return False
        except httpx.TimeoutException as e:
            logger.error(f"AI Brain service connection verification failed - timeout: {e}")
            return False
        except Exception as e:
            logger.error(f"AI Brain service connection verification failed - unexpected error: {e}", exc_info=True)
            return False

    async def verify_embedding_service(self) -> bool:
        """
        Verify embedding service is working by testing with sample text.
        
        This method performs a comprehensive embedding service verification including:
        - Embedding endpoint availability
        - Sample embedding generation
        - Response validation
        
        Returns:
            True if embedding generation works correctly, False otherwise
        """
        try:
            logger.info("Starting AI Brain embedding service verification")
            
            # Use a simple test text for verification
            test_text = "This is a test for embedding verification."
            
            async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
                # Test embedding endpoint
                response = await client.post(
                    f"{self.brain_endpoint}/utility/embed",
                    params={"text": test_text}
                )
                
                if response.status_code != 200:
                    logger.error(f"AI Brain embedding service verification failed: HTTP {response.status_code}")
                    return False
                
                # Validate response structure
                try:
                    result = response.json()
                    embedding = result.get("embedding", [])
                    
                    if not embedding:
                        logger.error("AI Brain embedding service returned empty embedding")
                        return False
                    
                    if not isinstance(embedding, list):
                        logger.error("AI Brain embedding service returned invalid embedding format")
                        return False
                    
                    if len(embedding) != 1024:
                        logger.error(f"AI Brain embedding service returned unexpected dimension: {len(embedding)} (expected 1024)")
                        return False
                    
                    # Validate that embedding contains numeric values
                    if not all(isinstance(x, (int, float)) for x in embedding):
                        logger.error("AI Brain embedding service returned non-numeric values")
                        return False
                    
                    logger.info(f"AI Brain embedding service verified successfully: {len(embedding)} dimensions")
                    return True
                    
                except ValueError as e:
                    logger.error(f"AI Brain embedding service returned invalid JSON: {e}")
                    return False
                    
        except httpx.ConnectError as e:
            logger.error(f"AI Brain embedding service verification failed - service unavailable: {e}")
            return False
        except httpx.TimeoutException as e:
            logger.error(f"AI Brain embedding service verification failed - timeout: {e}")
            return False
        except Exception as e:
            logger.error(f"AI Brain embedding service verification failed - unexpected error: {e}", exc_info=True)
            return False
    
    async def extract_text(
        self,
        file_data: bytes,
        filename: str,
        prompt: str = "Extract all text from this document",
        retry_on_failure: bool = True
    ) -> str:
        """
        Extract text from a file using AI Brain's OCR endpoint with enhanced retry logic.
        
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
        # Enhanced input validation
        if not file_data:
            error_msg = "Cannot extract text from empty file data"
            logger.error(error_msg)
            raise AIBrainClientError(error_msg)
        
        if not filename or not filename.strip():
            error_msg = "Filename is required for text extraction"
            logger.error(error_msg)
            raise AIBrainClientError(error_msg)
        
        file_size = len(file_data)
        if file_size > 50 * 1024 * 1024:  # 50MB limit
            logger.warning(f"Large file detected ({file_size / 1024 / 1024:.1f}MB) - extraction may be slow")
        
        last_error = None
        max_attempts = config.MAX_RETRY_ATTEMPTS if retry_on_failure else 1
        
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(
                    f"Extracting text from file: {filename} ({file_size} bytes) "
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
                    
                    # Enhanced response parsing and validation
                    try:
                        result = response.json()
                    except ValueError as e:
                        error_msg = f"AI Brain service returned invalid JSON response"
                        logger.error(f"{error_msg}: {e} [Attempt {attempt}/{max_attempts}]")
                        raise AIBrainClientError(error_msg) from e
                    
                    extracted_text = result.get("response", "")
                    
                    # Validate extracted text
                    if not isinstance(extracted_text, str):
                        error_msg = f"AI Brain service returned invalid text type: {type(extracted_text)}"
                        logger.error(f"{error_msg} [Attempt {attempt}/{max_attempts}]")
                        raise AIBrainClientError(error_msg)
                    
                    # Log extraction results
                    text_length = len(extracted_text)
                    if text_length == 0:
                        logger.warning(f"No text extracted from file: {filename} [Attempt {attempt}/{max_attempts}]")
                    else:
                        logger.info(
                            f"Text extraction completed successfully: {text_length} characters extracted "
                            f"from {filename} [Attempt {attempt}/{max_attempts}]"
                        )
                    
                    return extracted_text
                    
            except httpx.ConnectError as e:
                error_msg = f"AI Brain service unavailable (connection error)"
                logger.error(f"{error_msg}: {e} [Attempt {attempt}/{max_attempts}]")
                last_error = AIBrainClientError(error_msg)
                
                # Implement graceful degradation strategy
                if attempt < max_attempts:
                    delay = config.RETRY_DELAY_SECONDS * (config.RETRY_BACKOFF_MULTIPLIER ** (attempt - 1))
                    logger.info(f"Connection failed, implementing graceful degradation - retrying in {delay:.1f} seconds...")
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error("AI Brain service connection failed - graceful degradation: text extraction unavailable")
                    
            except httpx.TimeoutException as e:
                error_msg = f"Text extraction timeout after {self.timeout.read}s"
                logger.error(f"{error_msg}: {e} [Attempt {attempt}/{max_attempts}]")
                last_error = AIBrainClientError(error_msg)
                
                # For large files, timeout is expected - don't retry immediately
                if file_size > 10 * 1024 * 1024:  # 10MB+
                    logger.error(f"Large file timeout ({file_size / 1024 / 1024:.1f}MB) - not retrying to avoid resource exhaustion")
                    break
                elif attempt < max_attempts:
                    delay = config.RETRY_DELAY_SECONDS * (config.RETRY_BACKOFF_MULTIPLIER ** (attempt - 1))
                    logger.info(f"Timeout occurred, retrying with delay: {delay:.1f} seconds...")
                    await asyncio.sleep(delay)
                    continue
                
            except httpx.HTTPStatusError as e:
                error_msg = f"Text extraction HTTP error {e.response.status_code}"
                
                # Enhanced error logging with response details
                try:
                    response_text = e.response.text
                    logger.error(f"{error_msg}: {e} - Response: {response_text} [Attempt {attempt}/{max_attempts}]")
                except:
                    logger.error(f"{error_msg}: {e} [Attempt {attempt}/{max_attempts}]")
                
                # Retry on 5xx errors (server errors), but not 4xx (client errors)
                if 500 <= e.response.status_code < 600 and attempt < max_attempts:
                    delay = config.RETRY_DELAY_SECONDS * (config.RETRY_BACKOFF_MULTIPLIER ** (attempt - 1))
                    logger.info(f"Server error detected, implementing retry strategy in {delay:.1f} seconds...")
                    await asyncio.sleep(delay)
                    last_error = AIBrainClientError(error_msg)
                    continue
                else:
                    # Don't retry on 4xx errors - these are client errors
                    logger.error(f"Client error detected (HTTP {e.response.status_code}) - not retrying")
                    raise AIBrainClientError(error_msg) from e
                    
            except AIBrainClientError:
                # Re-raise our own exceptions without wrapping
                raise
                    
            except Exception as e:
                error_msg = f"Text extraction failed: {type(e).__name__}"
                logger.error(f"{error_msg}: {e} [Attempt {attempt}/{max_attempts}]", exc_info=True)
                last_error = AIBrainClientError(f"{error_msg}: {e}")
                
                # Retry on unexpected errors with graceful degradation logging
                if attempt < max_attempts:
                    delay = config.RETRY_DELAY_SECONDS * (config.RETRY_BACKOFF_MULTIPLIER ** (attempt - 1))
                    logger.info(f"Unexpected error encountered, implementing graceful retry in {delay:.1f} seconds...")
                    await asyncio.sleep(delay)
                    continue
        
        # If we exhausted all retries, raise the last error with enhanced context
        if last_error:
            logger.error(f"Text extraction failed after {max_attempts} attempts - graceful degradation activated")
            raise last_error
        
        # Should never reach here, but just in case
        raise AIBrainClientError("Text extraction failed for unknown reason")
    
    async def generate_embedding(self, text: str, retry_on_failure: bool = True) -> list[float]:
        """
        Generate vector embedding from text using AI Brain's embedding endpoint with enhanced retry logic.
        
        Args:
            text: Text content to generate embedding for
            retry_on_failure: Whether to retry on transient failures (default: True)
        
        Returns:
            Embedding vector as a list of floats (1024 dimensions for mxbai-embed-large)
        
        Raises:
            AIBrainClientError: If embedding generation fails or service is unavailable
        """
        # Enhanced input validation
        if not text or not text.strip():
            error_msg = "Cannot generate embedding for empty text"
            logger.error(error_msg)
            raise AIBrainClientError(error_msg)
        
        # Log text length for debugging
        text_length = len(text)
        if text_length > 10000:
            logger.warning(f"Generating embedding for very long text ({text_length} characters) - this may be slow")
        
        last_error = None
        max_attempts = config.MAX_RETRY_ATTEMPTS if retry_on_failure else 1
        
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(
                    f"Generating embedding for text ({text_length} characters) "
                    f"[Attempt {attempt}/{max_attempts}]"
                )
                
                # Use a more conservative timeout for embedding generation
                embedding_timeout = httpx.Timeout(60.0)  # 1 minute for embeddings
                
                async with httpx.AsyncClient(timeout=embedding_timeout) as client:
                    # Send request to AI Brain /utility/embed endpoint
                    response = await client.post(
                        f"{self.brain_endpoint}/utility/embed",
                        params={"text": text}
                    )
                    
                    # Check for HTTP errors
                    response.raise_for_status()
                    
                    # Parse response with enhanced validation
                    try:
                        result = response.json()
                    except ValueError as e:
                        error_msg = f"AI Brain service returned invalid JSON response"
                        logger.error(f"{error_msg}: {e} [Attempt {attempt}/{max_attempts}]")
                        raise AIBrainClientError(error_msg) from e
                    
                    embedding = result.get("embedding", [])
                    
                    # Enhanced embedding validation
                    if not embedding:
                        error_msg = "AI Brain service returned empty embedding"
                        logger.error(f"{error_msg} [Attempt {attempt}/{max_attempts}]")
                        raise AIBrainClientError(error_msg)
                    
                    if not isinstance(embedding, list):
                        error_msg = f"AI Brain service returned invalid embedding type: {type(embedding)}"
                        logger.error(f"{error_msg} [Attempt {attempt}/{max_attempts}]")
                        raise AIBrainClientError(error_msg)
                    
                    # Validate embedding dimensions (should be 1024 for mxbai-embed-large)
                    if len(embedding) != 1024:
                        error_msg = f"AI Brain service returned unexpected embedding dimension: {len(embedding)} (expected 1024)"
                        logger.error(f"{error_msg} [Attempt {attempt}/{max_attempts}]")
                        raise AIBrainClientError(error_msg)
                    
                    # Validate that all values are numeric
                    if not all(isinstance(x, (int, float)) for x in embedding):
                        error_msg = "AI Brain service returned non-numeric embedding values"
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
                
                # Implement graceful degradation strategy
                if attempt < max_attempts:
                    delay = config.RETRY_DELAY_SECONDS * (config.RETRY_BACKOFF_MULTIPLIER ** (attempt - 1))
                    logger.info(f"Connection failed, implementing graceful degradation - retrying in {delay:.1f} seconds...")
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error("AI Brain service connection failed - graceful degradation: proceeding without embeddings")
                    
            except httpx.TimeoutException as e:
                error_msg = f"Embedding generation timeout after 60s"
                logger.error(f"{error_msg}: {e} [Attempt {attempt}/{max_attempts}]")
                last_error = AIBrainClientError(error_msg)
                
                # Retry on timeout with exponential backoff
                if attempt < max_attempts:
                    delay = config.RETRY_DELAY_SECONDS * (config.RETRY_BACKOFF_MULTIPLIER ** (attempt - 1))
                    logger.info(f"Timeout occurred, retrying with longer delay: {delay:.1f} seconds...")
                    await asyncio.sleep(delay)
                    continue
                    
            except httpx.HTTPStatusError as e:
                error_msg = f"Embedding generation HTTP error {e.response.status_code}"
                
                # Enhanced error logging with response details
                try:
                    response_text = e.response.text
                    logger.error(f"{error_msg}: {e} - Response: {response_text} [Attempt {attempt}/{max_attempts}]")
                except:
                    logger.error(f"{error_msg}: {e} [Attempt {attempt}/{max_attempts}]")
                
                # Retry on 5xx errors (server errors), but not 4xx (client errors)
                if 500 <= e.response.status_code < 600 and attempt < max_attempts:
                    delay = config.RETRY_DELAY_SECONDS * (config.RETRY_BACKOFF_MULTIPLIER ** (attempt - 1))
                    logger.info(f"Server error detected, implementing retry strategy in {delay:.1f} seconds...")
                    await asyncio.sleep(delay)
                    last_error = AIBrainClientError(error_msg)
                    continue
                else:
                    # Don't retry on 4xx errors - these are client errors
                    logger.error(f"Client error detected (HTTP {e.response.status_code}) - not retrying")
                    raise AIBrainClientError(error_msg) from e
                    
            except AIBrainClientError:
                # Re-raise our own exceptions without wrapping
                raise
                    
            except Exception as e:
                error_msg = f"Embedding generation failed: {type(e).__name__}"
                logger.error(f"{error_msg}: {e} [Attempt {attempt}/{max_attempts}]", exc_info=True)
                last_error = AIBrainClientError(f"{error_msg}: {e}")
                
                # Retry on unexpected errors with graceful degradation logging
                if attempt < max_attempts:
                    delay = config.RETRY_DELAY_SECONDS * (config.RETRY_BACKOFF_MULTIPLIER ** (attempt - 1))
                    logger.info(f"Unexpected error encountered, implementing graceful retry in {delay:.1f} seconds...")
                    await asyncio.sleep(delay)
                    continue
        
        # If we exhausted all retries, raise the last error with enhanced context
        if last_error:
            logger.error(f"Embedding generation failed after {max_attempts} attempts - graceful degradation activated")
            raise last_error
        
        # Should never reach here, but just in case
        raise AIBrainClientError("Embedding generation failed for unknown reason")
