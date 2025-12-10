"""
Service Manager for initializing and managing application services.

This module provides centralized service initialization and management,
including the AI Brain client and Material Processing Service with
comprehensive health checks and component status tracking.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from services.ai_brain_client import AIBrainClient
from services.material_processing_service import MaterialProcessingService
from services.supabase_client import supabase_admin
from config import config

logger = logging.getLogger(__name__)


class RAGComponentStatus:
    """Tracks the status of RAG components."""
    
    def __init__(self):
        self.ai_brain_connection = False
        self.ai_brain_embedding = False
        self.database_functions = False
        self.supabase_connection = False
        self.rag_enabled = False
        self.last_check = None
        self.error_messages = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert status to dictionary for logging."""
        return {
            "ai_brain_connection": self.ai_brain_connection,
            "ai_brain_embedding": self.ai_brain_embedding,
            "database_functions": self.database_functions,
            "supabase_connection": self.supabase_connection,
            "rag_enabled": self.rag_enabled,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "error_messages": self.error_messages
        }


class ServiceManager:
    """
    Manages application services and their lifecycle with comprehensive health checks.
    
    Provides singleton access to services like AI Brain client and Material Processing Service,
    with startup verification of all RAG components and component status tracking.
    """
    
    def __init__(self):
        """Initialize the service manager."""
        self._ai_brain_client: Optional[AIBrainClient] = None
        self._processing_service: Optional[MaterialProcessingService] = None
        self._initialized = False
        self._rag_status = RAGComponentStatus()
    
    async def initialize(self) -> None:
        """
        Initialize all services with comprehensive RAG component verification.
        
        This method performs system startup verification of all RAG components,
        adds health check logging and component status tracking, and enables/disables
        RAG functionality based on component availability.
        """
        if self._initialized:
            logger.warning("Services already initialized")
            return
        
        logger.info("=" * 60)
        logger.info("Initializing services with RAG component verification...")
        logger.info("=" * 60)
        
        # Initialize AI Brain client
        logger.info("Step 1: Initializing AI Brain client")
        self._ai_brain_client = AIBrainClient(
            brain_endpoint=config.AI_BRAIN_ENDPOINT
        )
        
        # Perform comprehensive RAG component health checks
        await self._verify_rag_components()
        
        # Initialize Material Processing Service
        logger.info("Step 2: Initializing Material Processing Service")
        self._processing_service = MaterialProcessingService(
            ai_brain_client=self._ai_brain_client,
            timeout=config.AI_BRAIN_TIMEOUT
        )
        
        # Determine RAG functionality status
        self._determine_rag_functionality()
        
        self._initialized = True
        
        # Log final initialization summary
        logger.info("=" * 60)
        logger.info("Service initialization completed")
        logger.info(f"RAG Functionality: {'ENABLED' if self._rag_status.rag_enabled else 'DISABLED'}")
        if not self._rag_status.rag_enabled:
            logger.warning("RAG features will be limited due to component issues")
            for component, error in self._rag_status.error_messages.items():
                logger.warning(f"  - {component}: {error}")
        logger.info("=" * 60)
    
    async def _verify_rag_components(self) -> None:
        """
        Perform comprehensive verification of all RAG components.
        
        This method implements system startup verification of all RAG components
        with detailed logging and status tracking.
        """
        logger.info("Performing comprehensive RAG component verification...")
        self._rag_status.last_check = datetime.now(timezone.utc)
        
        # 1. Verify Supabase Database Connection
        logger.info("Verifying Supabase database connection...")
        try:
            # Test basic database connectivity
            result = supabase_admin.table("courses").select("id").limit(1).execute()
            self._rag_status.supabase_connection = True
            logger.info("✓ Supabase database connection verified")
        except Exception as e:
            self._rag_status.supabase_connection = False
            self._rag_status.error_messages["supabase"] = str(e)
            logger.error(f"✗ Supabase database connection failed: {e}")
        
        # 2. Verify AI Brain Service Connection
        logger.info("Verifying AI Brain service connection...")
        try:
            if await self._ai_brain_client.verify_connection():
                self._rag_status.ai_brain_connection = True
                logger.info("✓ AI Brain service connection verified")
            else:
                self._rag_status.ai_brain_connection = False
                self._rag_status.error_messages["ai_brain_connection"] = "Service not responding"
                logger.error("✗ AI Brain service connection failed - service not responding")
        except Exception as e:
            self._rag_status.ai_brain_connection = False
            self._rag_status.error_messages["ai_brain_connection"] = str(e)
            logger.error(f"✗ AI Brain service connection verification failed: {e}")
        
        # 3. Verify AI Brain Embedding Service
        logger.info("Verifying AI Brain embedding service...")
        try:
            if await self._ai_brain_client.verify_embedding_service():
                self._rag_status.ai_brain_embedding = True
                logger.info("✓ AI Brain embedding service verified")
            else:
                self._rag_status.ai_brain_embedding = False
                self._rag_status.error_messages["ai_brain_embedding"] = "Embedding service not working"
                logger.error("✗ AI Brain embedding service verification failed")
        except Exception as e:
            self._rag_status.ai_brain_embedding = False
            self._rag_status.error_messages["ai_brain_embedding"] = str(e)
            logger.error(f"✗ AI Brain embedding service verification failed: {e}")
        
        # 4. Verify Database Functions
        logger.info("Verifying database search functions...")
        try:
            # Check if search_materials_by_embedding function exists
            await self._verify_database_functions()
            self._rag_status.database_functions = True
            logger.info("✓ Database search functions verified")
        except Exception as e:
            self._rag_status.database_functions = False
            self._rag_status.error_messages["database_functions"] = str(e)
            logger.error(f"✗ Database search functions verification failed: {e}")
    
    async def _verify_database_functions(self) -> None:
        """
        Verify that required database functions exist and are accessible.
        
        This method performs comprehensive database function verification:
        1. Tests function execution with dummy parameters (primary method)
        2. Optionally checks function existence using PostgreSQL system catalogs
        3. Validates function permissions and accessibility
        4. Provides detailed error diagnostics for troubleshooting
        
        Raises:
            Exception: If database functions are not available
        """
        try:
            logger.debug("Verifying database search function 'search_materials_by_embedding'")
            
            # Primary verification: Test function execution with dummy parameters
            dummy_course_id = "00000000-0000-0000-0000-000000000000"
            dummy_embedding = "[" + ",".join(["0.0"] * 1024) + "]"
            
            result = supabase_admin.rpc(
                "search_materials_by_embedding",
                {
                    "query_course_id": dummy_course_id,
                    "query_embedding": dummy_embedding,
                    "match_limit": 1
                }
            ).execute()
            
            # If we get here without exception, function exists and is callable
            logger.debug("Database search function 'search_materials_by_embedding' is accessible")
            
            # Optional: Try to get additional function information if exec_sql is available
            try:
                function_check_query = """
                SELECT 
                    proname as function_name,
                    pronargs as num_args,
                    prorettype::regtype as return_type
                FROM pg_proc 
                WHERE proname = 'search_materials_by_embedding'
                AND pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
                """
                
                catalog_result = supabase_admin.rpc('exec_sql', {
                    'query': function_check_query
                }).execute()
                
                if catalog_result.data and len(catalog_result.data) > 0:
                    function_info = catalog_result.data[0]
                    logger.debug(f"Function details: {function_info['function_name']} with {function_info['num_args']} arguments")
                
            except Exception as catalog_error:
                logger.debug(f"System catalog check failed (not critical): {catalog_error}")
            
        except Exception as e:
            # Provide detailed error information for debugging
            error_str = str(e).lower()
            if "permission denied" in error_str:
                raise Exception(f"Database search function exists but user lacks execute permissions. Check that 'GRANT EXECUTE ON FUNCTION search_materials_by_embedding TO authenticated;' was run: {e}")
            elif "function" in error_str and "does not exist" in error_str:
                raise Exception(f"Database search function 'search_materials_by_embedding' does not exist. Run migration 006_add_vector_search_function.sql: {e}")
            elif "relation" in error_str and "does not exist" in error_str:
                raise Exception(f"Required database tables may not exist. Ensure database migrations have been run: {e}")
            elif "type" in error_str and "vector" in error_str:
                raise Exception(f"pgvector extension may not be installed. Run 'CREATE EXTENSION IF NOT EXISTS vector;': {e}")
            else:
                raise Exception(f"Database search function verification failed: {e}")
    
    def _determine_rag_functionality(self) -> None:
        """
        Determine RAG functionality status based on component health.
        
        RAG is enabled when all critical components are available:
        - Supabase database connection
        - AI Brain service connection
        - AI Brain embedding service
        
        Database functions are optional (fallback methods available).
        """
        critical_components = [
            self._rag_status.supabase_connection,
            self._rag_status.ai_brain_connection,
            self._rag_status.ai_brain_embedding
        ]
        
        self._rag_status.rag_enabled = all(critical_components)
        
        if self._rag_status.rag_enabled:
            logger.info("All critical RAG components are available - RAG functionality ENABLED")
            if not self._rag_status.database_functions:
                logger.warning("Database functions unavailable - will use fallback search methods")
        else:
            logger.warning("Critical RAG components unavailable - RAG functionality DISABLED")
            logger.warning("Chat will work with limited context (no material search)")
    
    async def get_rag_status(self) -> Dict[str, Any]:
        """
        Get current RAG component status.
        
        Returns:
            Dictionary containing current status of all RAG components
        """
        return self._rag_status.to_dict()
    
    async def refresh_rag_status(self) -> None:
        """
        Refresh RAG component status by re-running health checks.
        
        This can be called periodically or on-demand to update component status.
        """
        logger.info("Refreshing RAG component status...")
        await self._verify_rag_components()
        self._determine_rag_functionality()
        logger.info(f"RAG status refreshed - Functionality: {'ENABLED' if self._rag_status.rag_enabled else 'DISABLED'}")
    
    def is_rag_enabled(self) -> bool:
        """
        Check if RAG functionality is currently enabled.
        
        Returns:
            True if RAG functionality is available, False otherwise
        """
        return self._rag_status.rag_enabled
    
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
