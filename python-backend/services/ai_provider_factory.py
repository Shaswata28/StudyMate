"""
Factory for creating AI provider instances based on configuration.
"""

import logging
from typing import Optional

from services.ai_provider import AIProvider
from config import config

logger = logging.getLogger(__name__)

# Global provider instance (singleton pattern)
_provider_instance: Optional[AIProvider] = None


def get_ai_provider() -> AIProvider:
    """
    Factory function to get the configured AI provider instance.
    Uses singleton pattern to reuse the same provider instance.
    
    Returns:
        AIProvider: Configured AI provider instance (Gemini, Router, etc.)
    
    Raises:
        ValueError: If the configured provider type is unknown.
        ImportError: If the provider implementation is not available.
    """
    global _provider_instance
    
    # Return existing instance if already created
    if _provider_instance is not None:
        return _provider_instance
    
    provider_type = config.AI_PROVIDER.lower()
    
    logger.info(f"Initializing AI provider: {provider_type}")
    
    if provider_type == "gemini":
        try:
            from services.gemini_provider import GeminiProvider
            _provider_instance = GeminiProvider(
                api_key=config.GEMINI_API_KEY,
                model=config.GEMINI_MODEL,
                embedding_model=config.GEMINI_EMBEDDING_MODEL,
                temperature=config.GEMINI_TEMPERATURE,
                max_output_tokens=config.GEMINI_MAX_OUTPUT_TOKENS,
                timeout=config.GEMINI_TIMEOUT,
                embedding_api_key=config.GEMINI_EMBEDDING_API_KEY
            )
            logger.info("Gemini provider initialized successfully")
            if config.GEMINI_EMBEDDING_API_KEY != config.GEMINI_API_KEY:
                logger.info("Using separate API key for embeddings")
            return _provider_instance
            
        except ImportError as e:
            error_msg = f"Failed to import GeminiProvider: {str(e)}"
            logger.error(error_msg)
            raise ImportError(error_msg) from e
    
    elif provider_type == "router":
        try:
            from services.router_provider import RouterProvider
            _provider_instance = RouterProvider(
                router_endpoint=config.ROUTER_ENDPOINT,
                api_key=config.ROUTER_API_KEY
            )
            logger.info("Router provider initialized successfully")
            return _provider_instance
            
        except ImportError as e:
            error_msg = f"Failed to import RouterProvider: {str(e)}"
            logger.error(error_msg)
            raise ImportError(error_msg) from e
    
    else:
        error_msg = f"Unknown AI provider: {provider_type}. Valid options: gemini, router"
        logger.error(error_msg)
        raise ValueError(error_msg)


def reset_provider():
    """
    Reset the provider instance (useful for testing or configuration changes).
    """
    global _provider_instance
    _provider_instance = None
    logger.info("AI provider instance reset")
