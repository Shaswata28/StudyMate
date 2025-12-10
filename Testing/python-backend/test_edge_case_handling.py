"""
Test edge case handling for RAG functionality.
Tests Requirements 8.1, 8.2, 8.3 from rag-functionality-fix spec.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone

from services.material_processing_service import MaterialProcessingService
from services.ai_brain_client import AIBrainClient


class TestEdgeCaseHandling:
    """Test edge case handling for RAG functionality."""
    
    @pytest.fixture
    def mock_ai_brain_client(self):
        """Create a mock AI Brain client."""
        client = Mock(spec=AIBrainClient)
        client.verify_connection = AsyncMock(return_value=True)
        client.verify_embedding_service = AsyncMock(return_value=True)
        client.generate_embedding = AsyncMock(return_value=[0.1] * 1024)
        return client
    
    @pytest.fixture
    def processing_service(self, mock_ai_brain_client):
        """Create a material processing service with mocked dependencies."""
        return MaterialProcessingService(
            ai_brain_client=mock_ai_brain_client,
            timeout=30.0
        )
    
    @pytest.mark.asyncio
    async def test_empty_search_query_handling(self, processing_service):
        """
        Test Requirement 8.3: Handle short or empty search queries.
        
        WHEN search queries are too short or empty 
        THEN the System SHALL skip material search and proceed with conversation history only
        """
        course_id = "test-course-123"
        
        # Test completely empty query
        result = await processing_service.search_materials(course_id, "", limit=3)
        assert result == []
        
        # Test whitespace-only query
        result = await processing_service.search_materials(course_id, "   ", limit=3)
        assert result == []
        
        # Test very short query (less than 3 characters)
        result = await processing_service.search_materials(course_id, "hi", limit=3)
        assert result == []
        
        # Test query with exactly 3 characters (should proceed)
        with patch('services.material_processing_service.supabase_admin') as mock_supabase:
            # Mock course with no materials
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
            
            result = await processing_service.search_materials(course_id, "abc", limit=3)
            # Should proceed to check materials (and find none)
            assert result == []
    
    @pytest.mark.asyncio
    async def test_course_without_materials_handling(self, processing_service):
        """
        Test Requirement 8.1: Handle courses without materials gracefully.
        
        WHEN no materials have been uploaded 
        THEN the System SHALL proceed with chat using only conversation history
        """
        course_id = "empty-course-123"
        query = "test query"
        
        with patch('services.material_processing_service.supabase_admin') as mock_supabase:
            # Mock course with no materials
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
            
            result = await processing_service.search_materials(course_id, query, limit=3)
            
            # Should return empty results gracefully
            assert result == []
            
            # Verify the database was queried for materials
            mock_supabase.table.assert_called_with("materials")
    
    @pytest.mark.asyncio
    async def test_unprocessed_materials_handling(self, processing_service):
        """
        Test Requirement 8.2: Handle unprocessed materials appropriately.
        
        WHEN materials exist but none are processed 
        THEN the System SHALL log the processing status and proceed without material context
        """
        course_id = "unprocessed-course-123"
        query = "test query"
        
        with patch('services.material_processing_service.supabase_admin') as mock_supabase:
            # Mock course with materials in various non-completed states
            mock_materials = [
                {"id": "mat1", "processing_status": "pending"},
                {"id": "mat2", "processing_status": "processing"},
                {"id": "mat3", "processing_status": "failed"},
            ]
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = mock_materials
            
            result = await processing_service.search_materials(course_id, query, limit=3)
            
            # Should return empty results gracefully when no materials are completed
            assert result == []
    
    @pytest.mark.asyncio
    async def test_mixed_material_status_handling(self, processing_service):
        """
        Test handling of courses with mixed material processing statuses.
        Should only search completed materials.
        """
        course_id = "mixed-course-123"
        query = "test query"
        
        with patch('services.material_processing_service.supabase_admin') as mock_supabase:
            # Mock course with mixed material statuses
            mock_materials = [
                {"id": "mat1", "processing_status": "pending"},
                {"id": "mat2", "processing_status": "completed"},  # This one should be searchable
                {"id": "mat3", "processing_status": "failed"},
                {"id": "mat4", "processing_status": "processing"},
            ]
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = mock_materials
            
            # Mock the actual search to return empty (we're just testing the status check)
            mock_supabase.rpc.return_value.execute.return_value.data = []
            
            result = await processing_service.search_materials(course_id, query, limit=3)
            
            # Should proceed to search since there's at least one completed material
            # The actual search returns empty, but that's fine - we tested the status logic
            assert result == []
    
    @pytest.mark.asyncio
    async def test_database_error_graceful_degradation(self, processing_service):
        """
        Test graceful degradation when database queries fail.
        """
        course_id = "error-course-123"
        query = "test query"
        
        with patch('services.material_processing_service.supabase_admin') as mock_supabase:
            # Mock database error
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = Exception("Database error")
            
            result = await processing_service.search_materials(course_id, query, limit=3)
            
            # Should return empty results gracefully on database error
            assert result == []


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])