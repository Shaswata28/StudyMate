"""
Service Manager for initializing and managing application services.

This module provides centralized service initialization and management,
including the AI Brain client and Material Processing Service.
"""

import logging
from typing import Optional

from services.ai_brain_client import AIBrainClient
from services.material_processing_service import MaterialProcessingService
from config import config

logger = logging.getLogger(__name__)


class ServiceManager:
    """
    Manages application services and their lifecycle.
    
    Provides singleton access to services like AI Brain client
    and Material Processing Service.
    """
    
    def __init__(self):
        """Initialize the service manager."""
        self._ai_brain_client: Optional[AIBrainClient] = None
        self._processing_service: Optional[MaterialProcessingService] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """
        Initialize all services.
        
        This should be called during application startup.
        """
        if self._initialized:
            logger.warning("Services already initialized")
            return
        
        logger.info("Initializing services...")
        
        # Initialize AI Brain client
        self._ai_brain_client = AIBrainClient(
            brain_endpoint=config.AI_BRAIN_ENDPOINT
        )
        
        # Check AI Brain service health
        is_healthy = await self._ai_brain_client.health_check()
        if not is_healthy:
            logger.warning(
                f"AI Brain service not available at {config.AI_BRAIN_ENDPOINT}. "
                "Material processing will fail until service is started."
            )
        else:
            logger.info("AI Brain service connection verified")
        
        # Initialize Material Processing Service
        self._processing_service = MaterialProcessingService(
            ai_brain_client=self._ai_brain_client,
            timeout=config.AI_BRAIN_TIMEOUT
        )
        
        self._initialized = True
        logger.info("Services initialized successfully")
    
    @property
    def ai_brain_client(self) -> AIBrainClient:
        """Get the AI Brain client instance."""
        if not self._initialized or not self._ai_brain_client:
            raise RuntimeError("Services not initialized. Call initialize() first.")
        return self._ai_brain_client
    
    @property
    def processing_service(self) -> MaterialProcessingService:
        """Get the Material Processing Service instance."""
        if not self._initialized or not self._processing_service:
            raise RuntimeError("Services not initialized. Call initialize() first.")
        return self._processing_service


# Global service manager instance
service_manager = ServiceManager()
