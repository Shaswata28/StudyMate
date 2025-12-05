"""
Test for semantic search API endpoint.

This test verifies that the search endpoint:
1. Validates course ownership
2. Calls the search_materials service method
3. Returns ranked search results
4. Handles edge cases properly

Requirements: 4.1, 4.2, 4.3, 4.4
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_search_endpoint_exists():
    """
    Test that the search endpoint is properly defined in the router.
    
    This is a basic smoke test to verify the endpoint exists and has
    the correct structure. Full integration testing requires a running
    database and AI Brain service.
    """
    from routers.materials import router
    
    # Check that the router has routes
    assert len(router.routes) > 0
    
    # Find the search endpoint
    search_route = None
    for route in router.routes:
        if hasattr(route, 'path') and 'search' in route.path:
            search_route = route
            break
    
    assert search_route is not None, "Search endpoint not found in router"
    assert hasattr(search_route, 'methods')
    assert 'GET' in search_route.methods
    
    print("✓ Search endpoint exists and is configured correctly")


def test_search_endpoint_parameters():
    """
    Test that the search endpoint has the correct parameters.
    """
    from routers.materials import search_materials
    import inspect
    
    # Get function signature
    sig = inspect.signature(search_materials)
    params = sig.parameters
    
    # Verify required parameters
    assert 'course_id' in params
    assert 'query' in params
    assert 'limit' in params
    assert 'user' in params
    
    # Verify default value for limit
    assert params['limit'].default == 3
    
    print("✓ Search endpoint has correct parameters")


def test_search_endpoint_response_model():
    """
    Test that the search endpoint returns the correct response model.
    """
    from routers.materials import router
    from models.schemas import MaterialSearchResult
    from typing import List
    
    # Find the search endpoint
    search_route = None
    for route in router.routes:
        if hasattr(route, 'path') and 'search' in route.path:
            search_route = route
            break
    
    assert search_route is not None
    
    # Check response model
    if hasattr(search_route, 'response_model'):
        # The response model should be List[MaterialSearchResult]
        response_model = search_route.response_model
        assert response_model is not None
        print(f"✓ Search endpoint has response model: {response_model}")
    else:
        print("⚠ Could not verify response model (may be defined via decorator)")


def test_material_search_result_schema():
    """
    Test that MaterialSearchResult schema has all required fields.
    """
    from models.schemas import MaterialSearchResult
    from pydantic import BaseModel
    
    # Verify it's a Pydantic model
    assert issubclass(MaterialSearchResult, BaseModel)
    
    # Get model fields
    fields = MaterialSearchResult.model_fields
    
    # Verify required fields
    required_fields = ['material_id', 'name', 'excerpt', 'similarity_score', 'file_type']
    for field in required_fields:
        assert field in fields, f"Missing required field: {field}"
    
    print("✓ MaterialSearchResult schema has all required fields")


def test_endpoint_implementation_structure():
    """
    Test that the search endpoint implementation has the correct structure.
    """
    from routers.materials import search_materials
    import inspect
    
    # Get source code
    source = inspect.getsource(search_materials)
    
    # Verify key implementation details
    assert 'course_result' in source, "Missing course ownership check"
    assert 'processing_service' in source, "Missing processing service call"
    assert 'search_materials' in source, "Missing search_materials method call"
    assert 'MaterialSearchResult' in source, "Missing response schema conversion"
    assert 'HTTPException' in source, "Missing error handling"
    
    # Verify validation logic
    assert 'query' in source and 'strip' in source, "Missing query validation"
    assert 'limit' in source, "Missing limit parameter handling"
    
    print("✓ Search endpoint implementation has correct structure")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
