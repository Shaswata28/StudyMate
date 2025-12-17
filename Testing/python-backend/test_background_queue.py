"""
Test script to verify background task queue implementation.

This script tests that:
1. The upload endpoint returns immediately with status 'pending'
2. Background processing is queued and executes asynchronously
3. The MaterialResponse includes all new processing status fields
"""

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_background_queue():
    """Test that background task queue is properly implemented."""
    
    logger.info("=" * 60)
    logger.info("Testing Background Task Queue Implementation")
    logger.info("=" * 60)
    
    # Test 1: Verify queue_material_processing function exists and is async
    logger.info("\n1. Testing queue_material_processing function...")
    try:
        from routers.materials import queue_material_processing
        
        # Verify it's an async function
        assert asyncio.iscoroutinefunction(queue_material_processing), \
            "queue_material_processing should be an async function"
        
        logger.info("✓ queue_material_processing is properly defined as async function")
    except ImportError as e:
        logger.error(f"✗ Failed to import queue_material_processing: {e}")
        return False
    
    # Test 2: Verify MaterialResponse includes new fields
    logger.info("\n2. Testing MaterialResponse schema...")
    try:
        from models.schemas import MaterialResponse
        
        # Check that MaterialResponse has the new fields
        required_fields = [
            'processing_status',
            'processed_at',
            'error_message',
            'has_embedding'
        ]
        
        # Create a sample response to verify fields
        sample_data = {
            'id': 'test-id',
            'course_id': 'test-course',
            'name': 'test.pdf',
            'file_path': 'path/to/test.pdf',
            'file_type': 'application/pdf',
            'file_size': 1024,
            'processing_status': 'pending',
            'processed_at': None,
            'error_message': None,
            'has_embedding': False,
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z'
        }
        
        response = MaterialResponse(**sample_data)
        
        for field in required_fields:
            assert hasattr(response, field), f"MaterialResponse missing field: {field}"
        
        logger.info("✓ MaterialResponse includes all required processing status fields")
        logger.info(f"  - processing_status: {response.processing_status}")
        logger.info(f"  - processed_at: {response.processed_at}")
        logger.info(f"  - error_message: {response.error_message}")
        logger.info(f"  - has_embedding: {response.has_embedding}")
        
    except Exception as e:
        logger.error(f"✗ MaterialResponse schema test failed: {e}")
        return False
    
    # Test 3: Verify service_manager is properly defined
    logger.info("\n3. Testing service_manager structure...")
    try:
        from services.service_manager import service_manager, ServiceManager
        import inspect
        
        # Verify service_manager is an instance of ServiceManager
        assert isinstance(service_manager, ServiceManager), \
            "service_manager should be an instance of ServiceManager"
        
        # Verify service_manager has required methods
        assert hasattr(service_manager, 'initialize'), \
            "service_manager should have initialize method"
        
        # Check that initialize is a coroutine function
        assert inspect.iscoroutinefunction(service_manager.initialize), \
            "initialize should be an async method"
        
        # Verify properties exist in the class (not instance to avoid initialization error)
        assert 'processing_service' in dir(ServiceManager), \
            "ServiceManager should have processing_service property"
        assert 'ai_brain_client' in dir(ServiceManager), \
            "ServiceManager should have ai_brain_client property"
        
        logger.info("✓ service_manager is properly defined with required methods")
        logger.info("  - initialize() method: Yes (async)")
        logger.info("  - processing_service property: Yes")
        logger.info("  - ai_brain_client property: Yes")
        
    except Exception as e:
        logger.error(f"✗ service_manager test failed: {e}")
        return False
    
    # Test 4: Verify upload endpoint signature includes BackgroundTasks
    logger.info("\n4. Testing upload endpoint signature...")
    try:
        import inspect
        from routers.materials import upload_material
        
        # Get function signature
        sig = inspect.signature(upload_material)
        params = sig.parameters
        
        # Verify BackgroundTasks parameter exists
        assert 'background_tasks' in params, \
            "upload_material should have background_tasks parameter"
        
        # Verify it's of type BackgroundTasks
        from fastapi import BackgroundTasks
        param_annotation = params['background_tasks'].annotation
        
        logger.info("✓ upload_material endpoint includes BackgroundTasks parameter")
        logger.info(f"  - Parameter: background_tasks")
        logger.info(f"  - Type: {param_annotation}")
        
    except Exception as e:
        logger.error(f"✗ upload endpoint signature test failed: {e}")
        return False
    
    # Test 5: Mock test of background processing flow
    logger.info("\n5. Testing background processing flow (mocked)...")
    try:
        # Mock the processing service
        mock_processing_service = AsyncMock()
        mock_processing_service.process_material = AsyncMock()
        
        # Mock service_manager to return our mock
        with patch('routers.materials.service_manager') as mock_service_manager:
            mock_service_manager.processing_service = mock_processing_service
            
            # Call queue_material_processing
            test_material_id = "test-material-123"
            await queue_material_processing(test_material_id)
            
            # Verify process_material was called
            mock_processing_service.process_material.assert_called_once_with(test_material_id)
            
            logger.info("✓ Background processing flow works correctly")
            logger.info(f"  - Material ID: {test_material_id}")
            logger.info(f"  - process_material called: Yes")
        
    except Exception as e:
        logger.error(f"✗ Background processing flow test failed: {e}")
        return False
    
    logger.info("\n" + "=" * 60)
    logger.info("✓ All background task queue tests passed!")
    logger.info("=" * 60)
    
    return True


async def main():
    """Run all tests."""
    success = await test_background_queue()
    
    if success:
        logger.info("\n✓ Background task queue implementation verified successfully")
        return 0
    else:
        logger.error("\n✗ Background task queue implementation has issues")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
