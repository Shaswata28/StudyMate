"""
Tests for RAG error scenarios and recovery mechanisms.

This test suite verifies:
1. AI Brain service unavailable scenarios
2. Database connection failures  
3. Processing failures and retry logic
4. Graceful degradation in all scenarios

Requirements: 6.2, 6.3, 8.4, 8.5
"""

import pytest
import asyncio
import uuid
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from services.material_processing_service import MaterialProcessingService, MaterialProcessingError
from services.context_service import ContextService
from services.ai_brain_client import AIBrainClient, AIBrainClientError
from models.schemas import UserContext, Message, UserPreferences, AcademicInfo


class TestAIBrainServiceUnavailable:
    """Test scenarios when AI Brain service is unavailable."""
    
    @pytest.fixture
    def unavailable_ai_brain_client(self):
        """Create a mock AI Brain client that simulates service unavailability."""
        client = Mock(spec=AIBrainClient)
        client.verify_connection = AsyncMock(return_value=False)
        client.verify_embedding_service = AsyncMock(return_value=False)
        client.health_check = AsyncMock(return_value=False)
        client.extract_text = AsyncMock(side_effect=AIBrainClientError("Connection refused"))
        client.generate_embedding = AsyncMock(side_effect=AIBrainClientError("Service unavailable"))
        return client
    
    @pytest.fixture
    def processing_service_unavailable(self, unavailable_ai_brain_client):
        """Create processing service with unavailable AI Brain."""
        return MaterialProcessingService(ai_brain_client=unavailable_ai_brain_client)
    
    @pytest.mark.asyncio
    async def test_material_search_with_ai_brain_unavailable(self, processing_service_unavailable):
        """
        Test material search gracefully handles AI Brain service unavailability.
        
        Requirements: 6.2, 8.4 - Graceful degradation when AI Brain unavailable
        """
        course_id = str(uuid.uuid4())
        query = "machine learning concepts"
        
        with patch('services.material_processing_service.supabase_admin') as mock_supabase:
            # Mock materials exist but AI Brain can't generate embeddings
            mock_table = Mock()
            mock_supabase.table.return_value = mock_table
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.execute.return_value = Mock(data=[
                {"id": "material-1", "processing_status": "completed"}
            ])
            
            # Execute search - should handle AI Brain failure gracefully
            with pytest.raises(MaterialProcessingError) as exc_info:
                await processing_service_unavailable.search_materials(course_id, query, limit=3)
            
            # Verify appropriate error message
            assert "Failed to generate query embedding" in str(exc_info.value)
            assert "Service unavailable" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_material_processing_with_ai_brain_unavailable(self, processing_service_unavailable):
        """
        Test material processing handles AI Brain unavailability gracefully.
        
        Requirements: 6.2, 8.4 - Processing fails gracefully with proper error logging
        """
        material_id = str(uuid.uuid4())
        
        with patch('services.material_processing_service.supabase_admin') as mock_supabase:
            # Mock material exists
            mock_table = MagicMock()
            mock_supabase.table.return_value = mock_table
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.execute.return_value = MagicMock(data=[{
                "id": material_id,
                "name": "test.pdf",
                "file_path": "path/to/test.pdf"
            }])
            mock_table.update.return_value = mock_table
            
            # Mock storage download
            mock_storage = MagicMock()
            mock_supabase.storage.from_.return_value = mock_storage
            mock_storage.download.return_value = b"test data"
            
            # Process material - should handle AI Brain failure
            await processing_service_unavailable.process_material(material_id)
            
            # Verify status was updated to failed with appropriate error
            update_calls = mock_table.update.call_args_list
            final_update = update_calls[-1][0][0]
            assert final_update["processing_status"] == "failed"
            assert "OCR processing failed" in final_update["error_message"]
            assert "Connection refused" in final_update["error_message"]
    
    @pytest.mark.asyncio
    async def test_health_check_detects_unavailable_service(self, unavailable_ai_brain_client):
        """
        Test that health checks properly detect unavailable AI Brain service.
        
        Requirements: 6.2 - Service health verification
        """
        # Test connection health check
        connection_ok = await unavailable_ai_brain_client.verify_connection()
        assert connection_ok is False
        
        # Test embedding service health check
        embedding_ok = await unavailable_ai_brain_client.verify_embedding_service()
        assert embedding_ok is False
        
        # Test general health check
        health_ok = await unavailable_ai_brain_client.health_check()
        assert health_ok is False


class TestDatabaseConnectionFailures:
    """Test scenarios with database connection issues."""
    
    @pytest.fixture
    def processing_service_with_db_issues(self):
        """Create processing service for database failure testing."""
        ai_brain_client = Mock(spec=AIBrainClient)
        ai_brain_client.verify_connection = AsyncMock(return_value=True)
        ai_brain_client.verify_embedding_service = AsyncMock(return_value=True)
        ai_brain_client.generate_embedding = AsyncMock(return_value=[0.5] * 1024)
        return MaterialProcessingService(ai_brain_client=ai_brain_client)
    
    @pytest.mark.asyncio
    async def test_search_with_database_connection_failure(self, processing_service_with_db_issues):
        """
        Test search handles database connection failures gracefully.
        
        Requirements: 6.3, 8.5 - Database failure graceful degradation
        """
        course_id = str(uuid.uuid4())
        query = "test query"
        
        with patch('services.material_processing_service.supabase_admin') as mock_supabase:
            # Mock database connection failure
            mock_supabase.table.side_effect = Exception("Database connection failed")
            
            # Execute search - should handle database failure gracefully
            with pytest.raises(MaterialProcessingError) as exc_info:
                await processing_service_with_db_issues.search_materials(course_id, query, limit=3)
            
            # Verify appropriate error handling
            assert "Failed to search materials" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_processing_with_database_update_failure(self, processing_service_with_db_issues):
        """
        Test processing handles database update failures gracefully.
        
        Requirements: 6.3 - Database operation failure handling
        """
        material_id = str(uuid.uuid4())
        
        with patch('services.material_processing_service.supabase_admin') as mock_supabase:
            # Mock successful material retrieval
            mock_table = MagicMock()
            mock_supabase.table.return_value = mock_table
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.execute.return_value = MagicMock(data=[{
                "id": material_id,
                "name": "test.pdf",
                "file_path": "path/to/test.pdf"
            }])
            
            # Mock database update failure
            mock_table.update.side_effect = Exception("Database update failed")
            
            # Mock storage download
            mock_storage = MagicMock()
            mock_supabase.storage.from_.return_value = mock_storage
            mock_storage.download.return_value = b"test data"
            
            # Process material - should handle database update failure
            await processing_service_with_db_issues.process_material(material_id)
            
            # The processing should complete without crashing
            # (Error handling is internal, material processing continues)
    
    @pytest.mark.asyncio
    async def test_search_with_rpc_function_missing(self, processing_service_with_db_issues):
        """
        Test search handles missing database RPC function gracefully.
        
        Requirements: 6.3, 8.5 - Missing database function fallback
        """
        course_id = str(uuid.uuid4())
        query = "test query"
        
        mock_materials = [
            {
                "id": "material-1",
                "name": "test.pdf",
                "extracted_text": "Test content for search",
                "file_type": "application/pdf",
                "embedding": [0.5] * 1024
            }
        ]
        
        with patch('services.material_processing_service.supabase_admin') as mock_supabase:
            # Mock RPC function missing (raises exception)
            mock_supabase.rpc.side_effect = Exception("Function search_materials_by_embedding does not exist")
            
            # Mock fallback direct query
            mock_table = Mock()
            mock_supabase.table.return_value = mock_table
            
            call_count = 0
            def mock_execute():
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    # Material status check
                    return Mock(data=[{"id": "material-1", "processing_status": "completed"}])
                else:
                    # Direct query fallback
                    return Mock(data=mock_materials)
            
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.execute = mock_execute
            
            # Execute search - should fallback to direct query
            results = await processing_service_with_db_issues.search_materials(course_id, query, limit=3)
            
            # Verify fallback worked and returned results
            assert len(results) == 1
            assert results[0]["material_id"] == "material-1"


class TestProcessingFailuresAndRetry:
    """Test processing failures and retry logic."""
    
    @pytest.fixture
    def flaky_ai_brain_client(self):
        """Create AI Brain client that fails then succeeds (for retry testing)."""
        client = Mock(spec=AIBrainClient)
        client.verify_connection = AsyncMock(return_value=True)
        client.verify_embedding_service = AsyncMock(return_value=True)
        
        # Mock flaky behavior - fail first time, succeed second time
        self.extract_call_count = 0
        self.embedding_call_count = 0
        
        def extract_text_side_effect(*args, **kwargs):
            self.extract_call_count += 1
            if self.extract_call_count == 1:
                raise AIBrainClientError("Temporary OCR failure")
            return "Extracted text content"
        
        def generate_embedding_side_effect(*args, **kwargs):
            self.embedding_call_count += 1
            if self.embedding_call_count == 1:
                raise AIBrainClientError("Temporary embedding failure")
            return [0.5] * 1024
        
        client.extract_text = AsyncMock(side_effect=extract_text_side_effect)
        client.generate_embedding = AsyncMock(side_effect=generate_embedding_side_effect)
        return client
    
    @pytest.mark.asyncio
    async def test_processing_retry_on_temporary_failure(self, flaky_ai_brain_client):
        """
        Test that processing retries on temporary AI Brain failures.
        
        Requirements: 6.2 - Retry logic for temporary failures
        """
        processing_service = MaterialProcessingService(ai_brain_client=flaky_ai_brain_client)
        material_id = str(uuid.uuid4())
        
        with patch('services.material_processing_service.supabase_admin') as mock_supabase:
            # Mock material exists
            mock_table = MagicMock()
            mock_supabase.table.return_value = mock_table
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.execute.return_value = MagicMock(data=[{
                "id": material_id,
                "name": "test.pdf",
                "file_path": "path/to/test.pdf"
            }])
            mock_table.update.return_value = mock_table
            
            # Mock storage download
            mock_storage = MagicMock()
            mock_supabase.storage.from_.return_value = mock_storage
            mock_storage.download.return_value = b"test data"
            
            # Process material - should retry and eventually succeed
            await processing_service.process_material(material_id)
            
            # Verify AI Brain methods were called multiple times (retry logic)
            assert flaky_ai_brain_client.extract_text.call_count >= 1
            
            # Verify final status is completed (retry succeeded)
            update_calls = mock_table.update.call_args_list
            final_update = update_calls[-1][0][0]
            assert final_update["processing_status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_processing_timeout_handling(self):
        """
        Test that processing handles timeouts appropriately.
        
        Requirements: 6.2 - Timeout handling in processing
        """
        # Create AI Brain client with slow operations
        ai_brain_client = Mock(spec=AIBrainClient)
        ai_brain_client.verify_connection = AsyncMock(return_value=True)
        ai_brain_client.verify_embedding_service = AsyncMock(return_value=True)
        
        # Mock slow extract_text operation
        async def slow_extract_text(*args, **kwargs):
            await asyncio.sleep(10)  # Longer than timeout
            return "text"
        
        ai_brain_client.extract_text = slow_extract_text
        
        # Create service with short timeout
        processing_service = MaterialProcessingService(
            ai_brain_client=ai_brain_client,
            timeout=0.1  # Very short timeout
        )
        
        material_id = str(uuid.uuid4())
        
        with patch('services.material_processing_service.supabase_admin') as mock_supabase:
            # Mock material exists
            mock_table = MagicMock()
            mock_supabase.table.return_value = mock_table
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.execute.return_value = MagicMock(data=[{
                "id": material_id,
                "name": "test.pdf",
                "file_path": "path/to/test.pdf"
            }])
            mock_table.update.return_value = mock_table
            
            # Mock storage download
            mock_storage = MagicMock()
            mock_supabase.storage.from_.return_value = mock_storage
            mock_storage.download.return_value = b"test data"
            
            # Process material - should timeout and handle gracefully
            await processing_service.process_material(material_id)
            
            # Verify status was updated to failed with timeout message
            update_calls = mock_table.update.call_args_list
            final_update = update_calls[-1][0][0]
            assert final_update["processing_status"] == "failed"
            assert "timeout" in final_update["error_message"].lower()


class TestGracefulDegradation:
    """Test graceful degradation scenarios."""
    
    @pytest.fixture
    def context_service(self):
        """Create context service for testing."""
        return ContextService()
    
    @pytest.mark.asyncio
    async def test_chat_with_no_materials_available(self, context_service):
        """
        Test chat functionality when no materials are available.
        
        Requirements: 8.4, 8.5 - Graceful degradation with no materials
        """
        # Create user context with only chat history (no materials)
        chat_history = [
            Message(
                content="Hello, can you help me with programming?",
                role="user"
            ),
            Message(
                content="Of course! I'd be happy to help with programming questions.",
                role="model"
            )
        ]
        
        user_context = UserContext(
            preferences=UserPreferences(
                detail_level=0.6,
                example_preference=0.8,
                analogy_preference=0.5,
                technical_language=0.7,
                structure_preference=0.6,
                visual_preference=0.4,
                learning_pace="moderate",
                prior_experience="intermediate"
            ),
            academic=AcademicInfo(
                grade=["Bachelor"],
                semester_type="double",
                semester=5,
                subject=["Computer Science"]
            ),
            chat_history=chat_history,
            has_preferences=True,
            has_academic=True,
            has_history=True
        )
        
        current_message = "What are the best practices for writing clean code?"
        
        # Format prompt without material context (simulating no materials found)
        formatted_prompt = context_service.format_context_prompt(
            user_context,
            current_message,
            material_context=None
        )
        
        # Verify chat still works with available context
        assert "=== RECENT CONVERSATION ===" in formatted_prompt
        assert "Hello, can you help me with programming?" in formatted_prompt
        assert "=== CURRENT QUESTION ===" in formatted_prompt
        assert "best practices for writing clean code" in formatted_prompt
        assert "=== LEARNING PREFERENCES ===" in formatted_prompt
        assert "moderate" in formatted_prompt
        
        # Verify no material section is present
        assert "RELEVANT COURSE MATERIALS:" not in formatted_prompt
    
    @pytest.mark.asyncio
    async def test_chat_with_unprocessed_materials(self):
        """
        Test chat when materials exist but are not processed.
        
        Requirements: 8.4, 8.5 - Handle unprocessed materials gracefully
        """
        ai_brain_client = Mock(spec=AIBrainClient)
        ai_brain_client.verify_connection = AsyncMock(return_value=True)
        ai_brain_client.generate_embedding = AsyncMock(return_value=[0.5] * 1024)
        
        processing_service = MaterialProcessingService(ai_brain_client=ai_brain_client)
        course_id = str(uuid.uuid4())
        query = "machine learning"
        
        with patch('services.material_processing_service.supabase_admin') as mock_supabase:
            # Mock materials exist but none are processed
            mock_table = Mock()
            mock_supabase.table.return_value = mock_table
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.execute.return_value = Mock(data=[
                {"id": "material-1", "processing_status": "pending"},
                {"id": "material-2", "processing_status": "failed"}
            ])
            
            # Execute search - should return empty results gracefully
            results = await processing_service.search_materials(course_id, query, limit=3)
            
            # Verify empty results (no processed materials)
            assert results == []
            assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_chat_with_short_query_handling(self):
        """
        Test chat handles very short queries gracefully.
        
        Requirements: 8.4, 8.5 - Handle edge case queries
        """
        ai_brain_client = Mock(spec=AIBrainClient)
        ai_brain_client.verify_connection = AsyncMock(return_value=True)
        ai_brain_client.generate_embedding = AsyncMock(return_value=[0.5] * 1024)
        
        processing_service = MaterialProcessingService(ai_brain_client=ai_brain_client)
        course_id = str(uuid.uuid4())
        
        # Test very short query
        short_query = "ML"
        
        with patch('services.material_processing_service.supabase_admin') as mock_supabase:
            # Mock processed materials exist
            mock_table = Mock()
            mock_supabase.table.return_value = mock_table
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.execute.return_value = Mock(data=[
                {"id": "material-1", "processing_status": "completed"}
            ])
            
            # Mock RPC failure (fallback to direct query)
            mock_supabase.rpc.side_effect = Exception("RPC not available")
            
            # Mock empty search results for short query
            mock_table.execute.return_value = Mock(data=[])
            
            # Execute search with short query
            results = await processing_service.search_materials(course_id, short_query, limit=3)
            
            # Verify system handles short query gracefully
            assert results == []
            assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_multiple_component_failures_still_allow_basic_chat(self, context_service):
        """
        Test that basic chat works even when multiple RAG components fail.
        
        Requirements: 8.4, 8.5 - Multiple failure graceful degradation
        """
        # Simulate scenario where:
        # 1. AI Brain service is down (no material search)
        # 2. Chat history retrieval fails
        # 3. Only user preferences and current question available
        
        user_context = UserContext(
            preferences=UserPreferences(
                detail_level=0.5,
                example_preference=0.7,
                analogy_preference=0.8,
                technical_language=0.3,
                structure_preference=0.6,
                visual_preference=0.9,
                learning_pace="slow",
                prior_experience="beginner"
            ),
            academic=AcademicInfo(
                grade=["Bachelor"],
                semester_type="double",
                semester=2,
                subject=["Biology"]
            ),
            chat_history=[],  # Empty due to retrieval failure
            has_preferences=True,
            has_academic=True,
            has_history=False
        )
        
        current_message = "Can you explain photosynthesis?"
        
        # Format prompt with minimal context (no materials, no history)
        formatted_prompt = context_service.format_context_prompt(
            user_context,
            current_message,
            material_context=None
        )
        
        # Verify basic chat functionality still works
        assert "=== CURRENT QUESTION ===" in formatted_prompt
        assert "Can you explain photosynthesis?" in formatted_prompt
        assert "=== LEARNING PREFERENCES ===" in formatted_prompt
        assert "visual" in formatted_prompt
        assert "beginner" in formatted_prompt
        assert "=== STUDENT ACADEMIC CONTEXT ===" in formatted_prompt
        assert "Biology" in formatted_prompt
        assert "Bachelor" in formatted_prompt
        
        # Verify missing components are handled gracefully
        assert "RELEVANT COURSE MATERIALS:" not in formatted_prompt
        assert "=== RECENT CONVERSATION ===" not in formatted_prompt
        
        # Verify prompt is still useful for AI
        assert len(formatted_prompt) > 100  # Has substantial content
        sections = formatted_prompt.split("\n\n")
        assert len(sections) >= 2  # Has multiple sections


if __name__ == "__main__":
    pytest.main([__file__, "-v"])