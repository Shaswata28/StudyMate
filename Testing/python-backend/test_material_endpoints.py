"""
Test material endpoints to verify status fields are included.

This test verifies Requirements 6.1, 6.2, 6.3, 6.4, 6.5:
- Material details display current processing status
- Status values are correctly displayed (pending, processing, completed, failed)
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from main import app
from services.auth_service import AuthUser
from routers.materials import get_current_user, get_user_client


@pytest.fixture
def mock_auth_user():
    """Mock authenticated user."""
    return AuthUser(
        id="test-user-id",
        email="test@example.com",
        access_token="test-token"
    )


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client."""
    mock_client = Mock()
    return mock_client


@pytest.fixture
def client_with_auth(mock_auth_user, mock_supabase_client):
    """Test client with authentication overrides."""
    def override_get_current_user():
        return mock_auth_user
    
    def override_get_user_client(token):
        return mock_supabase_client
    
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_user_client] = override_get_user_client
    
    yield TestClient(app), mock_supabase_client
    
    app.dependency_overrides.clear()


def test_list_materials_includes_status_fields(client_with_auth):
    """
    Test that list_materials endpoint includes all new status fields.
    
    Validates Requirements 6.1, 6.2, 6.3, 6.4, 6.5:
    - processing_status field is included
    - processed_at field is included
    - error_message field is included
    - has_embedding field is included
    """
    client, mock_supabase_client = client_with_auth
    
    # Mock materials query with various statuses
    mock_materials_data = [
        {
            "id": "material-1",
            "course_id": "course-123",
            "name": "test1.pdf",
            "file_path": "path/test1.pdf",
            "file_type": "application/pdf",
            "file_size": 1024,
            "processing_status": "pending",
            "processed_at": None,
            "error_message": None,
            "embedding": None,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        },
        {
            "id": "material-2",
            "course_id": "course-123",
            "name": "test2.pdf",
            "file_path": "path/test2.pdf",
            "file_type": "application/pdf",
            "file_size": 2048,
            "processing_status": "completed",
            "processed_at": "2024-01-01T01:00:00Z",
            "error_message": None,
            "embedding": [0.1] * 1024,  # Has embedding
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T01:00:00Z"
        },
        {
            "id": "material-3",
            "course_id": "course-123",
            "name": "test3.pdf",
            "file_path": "path/test3.pdf",
            "file_type": "application/pdf",
            "file_size": 3072,
            "processing_status": "failed",
            "processed_at": None,
            "error_message": "OCR extraction failed",
            "embedding": None,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    ]
    
    # Create separate mock chains for course check and materials query
    course_table = Mock()
    course_select = Mock()
    course_eq1 = Mock()
    course_eq2 = Mock()
    course_execute = Mock()
    course_execute.data = [{"id": "course-123"}]
    course_eq2.execute = Mock(return_value=course_execute)
    course_eq1.eq = Mock(return_value=course_eq2)
    course_select.eq = Mock(return_value=course_eq1)
    course_table.select = Mock(return_value=course_select)
    
    materials_table = Mock()
    materials_select = Mock()
    materials_eq = Mock()
    materials_order = Mock()
    materials_execute = Mock()
    materials_execute.data = mock_materials_data
    materials_order.execute = Mock(return_value=materials_execute)
    materials_eq.order = Mock(return_value=materials_order)
    materials_select.eq = Mock(return_value=materials_eq)
    materials_table.select = Mock(return_value=materials_select)
    
    # Setup table() to return different mocks based on call order
    mock_supabase_client.table = Mock(side_effect=[course_table, materials_table])
    
    response = client.get("/api/courses/course-123/materials")
    
    assert response.status_code == 200
    materials = response.json()
    
    # Verify we got all materials
    assert len(materials) == 3
    
    # Verify pending material (Requirement 6.2)
    pending_material = materials[0]
    assert pending_material["processing_status"] == "pending"
    assert pending_material["processed_at"] is None
    assert pending_material["error_message"] is None
    assert pending_material["has_embedding"] is False
    
    # Verify completed material (Requirement 6.4)
    completed_material = materials[1]
    assert completed_material["processing_status"] == "completed"
    assert completed_material["processed_at"] == "2024-01-01T01:00:00Z"
    assert completed_material["error_message"] is None
    assert completed_material["has_embedding"] is True
    
    # Verify failed material (Requirement 6.5)
    failed_material = materials[2]
    assert failed_material["processing_status"] == "failed"
    assert failed_material["error_message"] == "OCR extraction failed"
    assert failed_material["has_embedding"] is False


def test_get_material_includes_status_fields(client_with_auth):
    """
    Test that get_material endpoint includes all new status fields.
    
    Validates Requirements 6.1, 6.3:
    - processing_status field is included
    - Status 'processing' is correctly displayed
    """
    client, mock_supabase_client = client_with_auth
    
    # Mock material query with processing status
    mock_material_data = {
        "id": "material-123",
        "course_id": "course-123",
        "name": "test.pdf",
        "file_path": "path/test.pdf",
        "file_type": "application/pdf",
        "file_size": 1024,
        "processing_status": "processing",
        "processed_at": None,
        "error_message": None,
        "embedding": None,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "courses": {"user_id": "test-user-id"}
    }
    
    material_mock = Mock()
    material_mock.data = [mock_material_data]
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = material_mock
    
    response = client.get("/api/materials/material-123")
    
    assert response.status_code == 200
    material = response.json()
    
    # Verify all status fields are present (Requirement 6.1)
    assert "processing_status" in material
    assert "processed_at" in material
    assert "error_message" in material
    assert "has_embedding" in material
    
    # Verify processing status (Requirement 6.3)
    assert material["processing_status"] == "processing"
    assert material["processed_at"] is None
    assert material["error_message"] is None
    assert material["has_embedding"] is False


def test_backward_compatibility_with_missing_fields(client_with_auth):
    """
    Test backward compatibility when database records don't have new fields.
    
    This ensures the endpoints handle materials created before the migration gracefully.
    """
    client, mock_supabase_client = client_with_auth
    
    # Mock material without new fields (old record)
    mock_materials_data = [
        {
            "id": "material-old",
            "course_id": "course-123",
            "name": "old.pdf",
            "file_path": "path/old.pdf",
            "file_type": "application/pdf",
            "file_size": 1024,
            # Missing: processing_status, processed_at, error_message, embedding
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    ]
    
    # Create separate mock chains for course check and materials query
    course_table = Mock()
    course_select = Mock()
    course_eq1 = Mock()
    course_eq2 = Mock()
    course_execute = Mock()
    course_execute.data = [{"id": "course-123"}]
    course_eq2.execute = Mock(return_value=course_execute)
    course_eq1.eq = Mock(return_value=course_eq2)
    course_select.eq = Mock(return_value=course_eq1)
    course_table.select = Mock(return_value=course_select)
    
    materials_table = Mock()
    materials_select = Mock()
    materials_eq = Mock()
    materials_order = Mock()
    materials_execute = Mock()
    materials_execute.data = mock_materials_data
    materials_order.execute = Mock(return_value=materials_execute)
    materials_eq.order = Mock(return_value=materials_order)
    materials_select.eq = Mock(return_value=materials_eq)
    materials_table.select = Mock(return_value=materials_select)
    
    # Setup table() to return different mocks based on call order
    mock_supabase_client.table = Mock(side_effect=[course_table, materials_table])
    
    response = client.get("/api/courses/course-123/materials")
    
    assert response.status_code == 200
    materials = response.json()
    
    # Verify backward compatibility - defaults are applied
    assert len(materials) == 1
    material = materials[0]
    assert material["processing_status"] == "pending"  # Default value
    assert material["processed_at"] is None
    assert material["error_message"] is None
    assert material["has_embedding"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
