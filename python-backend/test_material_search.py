"""
Tests for material semantic search functionality.

This test suite verifies:
1. Query embedding generation
2. Vector similarity search
3. Result ranking by relevance
4. Edge cases (empty course, no results)
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from services.material_processing_service import MaterialProcessingService, MaterialProcessingError
from services.ai_brain_client import AIBrainClient


@pytest.fixture
def mock_ai_brain_client():
    """Create a mock AI Brain client."""
    client = Mock(spec=AIBrainClient)
    client.generate_embedding = AsyncMock()
    return client


@pytest.fixture
def processing_service(mock_ai_brain_client):
    """Create a material processing service with mocked dependencies."""
    return MaterialProcessingService(
        ai_brain_client=mock_ai_brain_client,
        timeout=300.0
    )


@pytest.mark.asyncio
async def test_search_materials_generates_query_embedding(processing_service, mock_ai_brain_client):
    """
    Test that search generates an embedding for the query.
    
    Requirements: 4.1, 4.2
    """
    # Setup
    course_id = "test-course-123"
    query = "machine learning algorithms"
    mock_embedding = [0.1] * 1024
    
    mock_ai_brain_client.generate_embedding.return_value = mock_embedding
    
    # Mock Supabase to return empty results
    with patch('services.material_processing_service.supabase_admin') as mock_supabase:
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.not_.is_.return_value.execute.return_value.data = []
        
        # Execute
        results = await processing_service.search_materials(course_id, query, limit=3)
        
        # Verify embedding was generated for the query
        mock_ai_brain_client.generate_embedding.assert_called_once_with(query)
        assert results == []  # Empty course returns empty results


@pytest.mark.asyncio
async def test_search_materials_returns_ranked_results(processing_service, mock_ai_brain_client):
    """
    Test that search results are ranked by similarity score.
    
    Requirements: 4.3
    """
    # Setup
    course_id = "test-course-123"
    query = "neural networks"
    query_embedding = [0.5] * 1024
    
    mock_ai_brain_client.generate_embedding.return_value = query_embedding
    
    # Mock materials with different embeddings (different similarities)
    # Create embeddings with varying similarity to query_embedding [0.5] * 1024
    mock_materials = [
        {
            "id": "material-1",
            "name": "intro.pdf",
            "extracted_text": "Introduction to neural networks and deep learning",
            "file_type": "application/pdf",
            "embedding": [0.4] * 512 + [0.6] * 512  # Medium similarity (mixed values)
        },
        {
            "id": "material-2",
            "name": "advanced.pdf",
            "extracted_text": "Advanced neural network architectures",
            "file_type": "application/pdf",
            "embedding": [0.5] * 1024  # Highest similarity (exact match)
        },
        {
            "id": "material-3",
            "name": "basics.pdf",
            "extracted_text": "Basic concepts in machine learning",
            "file_type": "application/pdf",
            "embedding": [0.3] * 512 + [0.7] * 512  # Lower similarity (more variation)
        }
    ]
    
    with patch('services.material_processing_service.supabase_admin') as mock_supabase:
        # Mock the RPC call to raise an exception (fallback to direct query)
        mock_supabase.rpc.side_effect = Exception("RPC not available")
        
        # Mock the direct query chain
        mock_execute = Mock()
        mock_execute.data = mock_materials
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_execute
        
        # Execute
        results = await processing_service.search_materials(course_id, query, limit=3)
        
        # Verify results are ranked by similarity (descending)
        assert len(results) == 3
        assert results[0]["material_id"] == "material-2"  # Highest similarity
        assert results[1]["material_id"] == "material-1"  # Medium similarity
        assert results[2]["material_id"] == "material-3"  # Lowest similarity
        
        # Verify similarity scores are in descending order
        assert results[0]["similarity_score"] >= results[1]["similarity_score"]
        assert results[1]["similarity_score"] >= results[2]["similarity_score"]


@pytest.mark.asyncio
async def test_search_materials_includes_metadata_and_scores(processing_service, mock_ai_brain_client):
    """
    Test that search results include all required metadata and similarity scores.
    
    Requirements: 4.4
    """
    # Setup
    course_id = "test-course-123"
    query = "data structures"
    query_embedding = [0.5] * 1024
    
    mock_ai_brain_client.generate_embedding.return_value = query_embedding
    
    mock_materials = [
        {
            "id": "material-1",
            "name": "data_structures.pdf",
            "extracted_text": "This is a comprehensive guide to data structures including arrays, linked lists, trees, and graphs. " * 10,
            "file_type": "application/pdf",
            "embedding": [0.5] * 1024
        }
    ]
    
    with patch('services.material_processing_service.supabase_admin') as mock_supabase:
        # Mock the RPC call to raise an exception (fallback to direct query)
        mock_supabase.rpc.side_effect = Exception("RPC not available")
        
        # Mock the direct query chain
        mock_execute = Mock()
        mock_execute.data = mock_materials
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_execute
        
        # Execute
        results = await processing_service.search_materials(course_id, query, limit=3)
        
        # Verify result structure
        assert len(results) == 1
        result = results[0]
        
        # Check all required fields are present
        assert "material_id" in result
        assert "name" in result
        assert "excerpt" in result
        assert "similarity_score" in result
        assert "file_type" in result
        
        # Verify field values
        assert result["material_id"] == "material-1"
        assert result["name"] == "data_structures.pdf"
        assert result["file_type"] == "application/pdf"
        assert isinstance(result["similarity_score"], float)
        assert 0 <= result["similarity_score"] <= 1
        
        # Verify excerpt is truncated to 500 chars
        assert len(result["excerpt"]) <= 503  # 500 + "..."


@pytest.mark.asyncio
async def test_search_materials_empty_course_returns_empty_results(processing_service, mock_ai_brain_client):
    """
    Test that searching an empty course returns empty results.
    
    Requirements: 4.5
    """
    # Setup
    course_id = "empty-course-123"
    query = "test query"
    query_embedding = [0.5] * 1024
    
    mock_ai_brain_client.generate_embedding.return_value = query_embedding
    
    with patch('services.material_processing_service.supabase_admin') as mock_supabase:
        # Mock the RPC call to raise an exception (fallback to direct query)
        mock_supabase.rpc.side_effect = Exception("RPC not available")
        
        # Mock empty course (no materials)
        mock_execute = Mock()
        mock_execute.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_execute
        
        # Execute
        results = await processing_service.search_materials(course_id, query, limit=3)
        
        # Verify empty results
        assert results == []
        assert isinstance(results, list)


@pytest.mark.asyncio
async def test_search_materials_no_processed_materials_returns_empty(processing_service, mock_ai_brain_client):
    """
    Test that searching a course with no processed materials returns empty results.
    
    Requirements: 4.5
    """
    # Setup
    course_id = "course-with-pending-materials"
    query = "test query"
    query_embedding = [0.5] * 1024
    
    mock_ai_brain_client.generate_embedding.return_value = query_embedding
    
    with patch('services.material_processing_service.supabase_admin') as mock_supabase:
        # Mock the RPC call to raise an exception (fallback to direct query)
        mock_supabase.rpc.side_effect = Exception("RPC not available")
        
        # Mock course with materials but none completed/with embeddings
        mock_execute = Mock()
        mock_execute.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_execute
        
        # Execute
        results = await processing_service.search_materials(course_id, query, limit=3)
        
        # Verify empty results
        assert results == []


@pytest.mark.asyncio
async def test_search_materials_respects_limit(processing_service, mock_ai_brain_client):
    """
    Test that search respects the limit parameter.
    
    Requirements: 4.3
    """
    # Setup
    course_id = "test-course-123"
    query = "test query"
    query_embedding = [0.5] * 1024
    
    mock_ai_brain_client.generate_embedding.return_value = query_embedding
    
    # Create 10 mock materials
    mock_materials = [
        {
            "id": f"material-{i}",
            "name": f"file-{i}.pdf",
            "extracted_text": f"Content {i}",
            "file_type": "application/pdf",
            "embedding": [0.5 + i * 0.01] * 1024
        }
        for i in range(10)
    ]
    
    with patch('services.material_processing_service.supabase_admin') as mock_supabase:
        # Mock the RPC call to raise an exception (fallback to direct query)
        mock_supabase.rpc.side_effect = Exception("RPC not available")
        
        # Mock the direct query chain
        mock_execute = Mock()
        mock_execute.data = mock_materials
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_execute
        
        # Execute with limit=3
        results = await processing_service.search_materials(course_id, query, limit=3)
        
        # Verify only 3 results returned
        assert len(results) == 3


@pytest.mark.asyncio
async def test_search_materials_handles_embedding_generation_failure(processing_service, mock_ai_brain_client):
    """
    Test that search handles embedding generation failures gracefully.
    
    Requirements: 4.1
    """
    # Setup
    course_id = "test-course-123"
    query = "test query"
    
    # Mock embedding generation failure
    from services.ai_brain_client import AIBrainClientError
    mock_ai_brain_client.generate_embedding.side_effect = AIBrainClientError("AI Brain service unavailable")
    
    # Execute and verify exception
    with pytest.raises(MaterialProcessingError) as exc_info:
        await processing_service.search_materials(course_id, query, limit=3)
    
    assert "Failed to generate query embedding" in str(exc_info.value)


@pytest.mark.asyncio
async def test_cosine_similarity_calculation():
    """
    Test the cosine similarity calculation helper method.
    """
    service = MaterialProcessingService(
        ai_brain_client=Mock(spec=AIBrainClient),
        timeout=300.0
    )
    
    # Test identical vectors (similarity = 1.0)
    vec1 = [1.0, 0.0, 0.0]
    vec2 = [1.0, 0.0, 0.0]
    similarity = service._cosine_similarity(vec1, vec2)
    assert abs(similarity - 1.0) < 0.001
    
    # Test orthogonal vectors (similarity = 0.0)
    vec1 = [1.0, 0.0, 0.0]
    vec2 = [0.0, 1.0, 0.0]
    similarity = service._cosine_similarity(vec1, vec2)
    assert abs(similarity - 0.0) < 0.001
    
    # Test opposite vectors (similarity should be clamped to 0.0)
    vec1 = [1.0, 0.0, 0.0]
    vec2 = [-1.0, 0.0, 0.0]
    similarity = service._cosine_similarity(vec1, vec2)
    assert similarity == 0.0
    
    # Test zero vector (should return 0.0)
    vec1 = [0.0, 0.0, 0.0]
    vec2 = [1.0, 0.0, 0.0]
    similarity = service._cosine_similarity(vec1, vec2)
    assert similarity == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
