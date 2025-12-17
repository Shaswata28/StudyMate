"""
Test RAG (Retrieval Augmented Generation) integration in chat endpoint.

This test verifies that the chat endpoint correctly:
1. Performs semantic search when course_id is provided
2. Retrieves top 3 relevant materials
3. Includes material context in the AI prompt
4. Handles cases with no relevant materials

Requirements: 5.1, 5.2, 5.3, 5.5
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app
from services.service_manager import service_manager


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_auth(client):
    """Mock authentication."""
    from routers.chat import get_current_user
    
    def override_get_current_user():
        return Mock(
            id="test-user-id",
            access_token="test-token"
        )
    
    app.dependency_overrides[get_current_user] = override_get_current_user
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_supabase():
    """Mock Supabase client."""
    with patch('routers.chat.get_user_client') as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


@pytest.fixture
def mock_processing_service():
    """Mock material processing service."""
    with patch('routers.chat.service_manager') as mock_manager:
        mock_service = AsyncMock()
        mock_manager.processing_service = mock_service
        yield mock_service


@pytest.fixture
def mock_ai_service():
    """Mock local AI service."""
    with patch('routers.chat.local_ai_service') as mock:
        mock.generate_response = AsyncMock(return_value="AI response")
        yield mock


def test_chat_without_course_id_no_rag(client, mock_ai_service):
    """
    Test that chat without course_id does not perform RAG.
    
    Requirement 5.5: When no course context, proceed without RAG
    """
    # Send chat request without course_id
    response = client.post(
        "/api/chat",
        json={
            "message": "What is machine learning?",
            "history": [],
            "attachments": []
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert data["response"] == "AI response"
    
    # Verify AI service was called with original message (no augmentation)
    mock_ai_service.generate_response.assert_called_once()
    call_args = mock_ai_service.generate_response.call_args
    assert call_args[1]["message"] == "What is machine learning?"


def test_chat_with_course_id_performs_search(
    client,
    mock_auth,
    mock_supabase,
    mock_processing_service,
    mock_ai_service
):
    """
    Test that chat with course_id performs semantic search.
    
    Requirement 5.1: Perform semantic search when course_id provided
    """
    # Mock course ownership verification
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        {"id": "course-123"}
    ]
    
    # Mock search results
    mock_processing_service.search_materials.return_value = [
        {
            "material_id": "mat-1",
            "name": "ML Basics.pdf",
            "excerpt": "Machine learning is a subset of AI...",
            "similarity_score": 0.95,
            "file_type": "application/pdf"
        }
    ]
    
    # Send chat request with course_id
    response = client.post(
        "/api/courses/course-123/chat",
        json={
            "message": "What is machine learning?",
            "history": [],
            "attachments": []
        }
    )
    
    assert response.status_code == 201
    
    # Verify search was performed
    mock_processing_service.search_materials.assert_called_once_with(
        course_id="course-123",
        query="What is machine learning?",
        limit=3
    )


def test_chat_retrieves_top_3_materials(
    client,
    mock_auth,
    mock_supabase,
    mock_processing_service,
    mock_ai_service
):
    """
    Test that RAG retrieves top 3 most relevant materials.
    
    Requirement 5.2: Retrieve top 3 most relevant material excerpts
    """
    # Mock course ownership verification
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        {"id": "course-123"}
    ]
    
    # Mock search results with 5 materials (should only use top 3)
    mock_processing_service.search_materials.return_value = [
        {
            "material_id": "mat-1",
            "name": "Material 1",
            "excerpt": "Content 1",
            "similarity_score": 0.95,
            "file_type": "application/pdf"
        },
        {
            "material_id": "mat-2",
            "name": "Material 2",
            "excerpt": "Content 2",
            "similarity_score": 0.90,
            "file_type": "application/pdf"
        },
        {
            "material_id": "mat-3",
            "name": "Material 3",
            "excerpt": "Content 3",
            "similarity_score": 0.85,
            "file_type": "application/pdf"
        }
    ]
    
    # Send chat request
    response = client.post(
        "/api/courses/course-123/chat",
        json={
            "message": "Test question",
            "history": [],
            "attachments": []
        }
    )
    
    assert response.status_code == 201
    
    # Verify search was called with limit=3
    mock_processing_service.search_materials.assert_called_once()
    call_args = mock_processing_service.search_materials.call_args
    assert call_args[1]["limit"] == 3


def test_chat_includes_material_context_in_prompt(
    client,
    mock_auth,
    mock_supabase,
    mock_processing_service,
    mock_ai_service
):
    """
    Test that material context is included in the AI prompt.
    
    Requirement 5.3: Include material context in AI prompt
    """
    # Mock course ownership verification
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        {"id": "course-123"}
    ]
    
    # Mock search results
    mock_processing_service.search_materials.return_value = [
        {
            "material_id": "mat-1",
            "name": "ML Basics.pdf",
            "excerpt": "Machine learning is a subset of AI that enables systems to learn from data.",
            "similarity_score": 0.95,
            "file_type": "application/pdf"
        },
        {
            "material_id": "mat-2",
            "name": "Deep Learning.pdf",
            "excerpt": "Deep learning uses neural networks with multiple layers.",
            "similarity_score": 0.88,
            "file_type": "application/pdf"
        }
    ]
    
    # Send chat request
    response = client.post(
        "/api/courses/course-123/chat",
        json={
            "message": "What is machine learning?",
            "history": [],
            "attachments": []
        }
    )
    
    assert response.status_code == 201
    
    # Verify AI service was called with augmented message
    mock_ai_service.generate_response.assert_called_once()
    call_args = mock_ai_service.generate_response.call_args
    augmented_message = call_args[1]["message"]
    
    # Verify material context is included
    assert "RELEVANT COURSE MATERIALS" in augmented_message
    assert "ML Basics.pdf" in augmented_message
    assert "Machine learning is a subset of AI" in augmented_message
    assert "Deep Learning.pdf" in augmented_message
    assert "Deep learning uses neural networks" in augmented_message
    assert "What is machine learning?" in augmented_message
    
    # Verify relevance scores are included
    assert "0.95" in augmented_message
    assert "0.88" in augmented_message


def test_chat_handles_no_relevant_materials(
    client,
    mock_auth,
    mock_supabase,
    mock_processing_service,
    mock_ai_service
):
    """
    Test that chat proceeds without RAG when no relevant materials found.
    
    Requirement 5.5: Proceed without material context when no relevant materials
    """
    # Mock course ownership verification
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        {"id": "course-123"}
    ]
    
    # Mock empty search results
    mock_processing_service.search_materials.return_value = []
    
    # Send chat request
    response = client.post(
        "/api/courses/course-123/chat",
        json={
            "message": "What is machine learning?",
            "history": [],
            "attachments": []
        }
    )
    
    assert response.status_code == 201
    
    # Verify AI service was called with original message (no augmentation)
    mock_ai_service.generate_response.assert_called_once()
    call_args = mock_ai_service.generate_response.call_args
    message = call_args[1]["message"]
    
    # Verify no material context was added
    assert "RELEVANT COURSE MATERIALS" not in message
    assert message == "What is machine learning?"


def test_chat_handles_search_failure_gracefully(
    client,
    mock_auth,
    mock_supabase,
    mock_processing_service,
    mock_ai_service
):
    """
    Test that chat continues without RAG if material search fails.
    
    Requirement 5.5: Handle search failures gracefully
    """
    # Mock course ownership verification
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        {"id": "course-123"}
    ]
    
    # Mock search failure
    mock_processing_service.search_materials.side_effect = Exception("Search service unavailable")
    
    # Send chat request
    response = client.post(
        "/api/courses/course-123/chat",
        json={
            "message": "What is machine learning?",
            "history": [],
            "attachments": []
        }
    )
    
    # Should still succeed (proceed without RAG)
    assert response.status_code == 201
    
    # Verify AI service was called with original message
    mock_ai_service.generate_response.assert_called_once()
    call_args = mock_ai_service.generate_response.call_args
    message = call_args[1]["message"]
    assert message == "What is machine learning?"


def test_chat_with_query_parameter_course_id(
    client,
    mock_processing_service,
    mock_ai_service
):
    """
    Test that chat endpoint accepts course_id as query parameter.
    
    Requirement 5.1: Accept optional course_id parameter
    """
    # Mock search results
    mock_processing_service.search_materials.return_value = [
        {
            "material_id": "mat-1",
            "name": "Test Material",
            "excerpt": "Test content",
            "similarity_score": 0.90,
            "file_type": "application/pdf"
        }
    ]
    
    # Send chat request with course_id as query parameter
    response = client.post(
        "/api/chat?course_id=course-123",
        json={
            "message": "Test question",
            "history": [],
            "attachments": []
        }
    )
    
    assert response.status_code == 200
    
    # Verify search was performed with the course_id
    mock_processing_service.search_materials.assert_called_once_with(
        course_id="course-123",
        query="Test question",
        limit=3
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
