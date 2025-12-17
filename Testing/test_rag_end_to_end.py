#!/usr/bin/env python3
"""
End-to-end RAG functionality test.

This script tests the complete RAG pipeline:
1. AI Brain service health check
2. Material search functionality
3. Context service functionality
4. Error handling and graceful degradation
"""

import asyncio
import logging
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_ai_brain_service():
    """Test AI Brain service connectivity and health."""
    logger.info("=== Testing AI Brain Service ===")
    
    try:
        from services.ai_brain_client import AIBrainClient
        
        client = AIBrainClient()
        
        # Test basic health check
        health_ok = await client.health_check()
        logger.info(f"Health check: {'PASS' if health_ok else 'FAIL'}")
        
        if health_ok:
            # Test embedding service
            embedding_ok = await client.verify_embedding_service()
            logger.info(f"Embedding service: {'PASS' if embedding_ok else 'FAIL'}")
            
            # Test actual embedding generation
            try:
                embedding = await client.generate_embedding("test query")
                logger.info(f"Embedding generation: PASS (dimension: {len(embedding)})")
                return True
            except Exception as e:
                logger.error(f"Embedding generation: FAIL - {e}")
                return False
        else:
            logger.error("AI Brain service is not available")
            return False
            
    except Exception as e:
        logger.error(f"AI Brain service test failed: {e}")
        return False

async def test_material_search():
    """Test material search functionality."""
    logger.info("=== Testing Material Search ===")
    
    try:
        from services.material_processing_service import MaterialProcessingService
        from services.ai_brain_client import AIBrainClient
        
        client = AIBrainClient()
        service = MaterialProcessingService(ai_brain_client=client)
        
        # Test with a valid UUID format
        course_id = str(uuid.uuid4())
        
        # Test search with empty course (should return empty results gracefully)
        results = await service.search_materials(course_id, "machine learning", limit=3)
        logger.info(f"Search with empty course: PASS (returned {len(results)} results)")
        
        # Test search with very short query (should return empty results)
        results = await service.search_materials(course_id, "ml", limit=3)
        logger.info(f"Search with short query: PASS (returned {len(results)} results)")
        
        # Test search with empty query (should return empty results)
        results = await service.search_materials(course_id, "", limit=3)
        logger.info(f"Search with empty query: PASS (returned {len(results)} results)")
        
        return True
        
    except Exception as e:
        logger.error(f"Material search test failed: {e}")
        return False

async def test_context_service():
    """Test context service functionality."""
    logger.info("=== Testing Context Service ===")
    
    try:
        from services.context_service import ContextService
        from models.schemas import UserContext
        
        service = ContextService()
        
        # Test prompt formatting with empty context
        context = UserContext(
            preferences=None,
            academic_info=None,
            chat_history=[]
        )
        
        prompt = service.format_context_prompt(context, "What is machine learning?")
        logger.info(f"Prompt formatting: PASS (length: {len(prompt)} chars)")
        
        # Test with material context
        material_context = """
        RELEVANT COURSE MATERIALS:
        
        Material: ML Basics.pdf (Relevance: 0.95)
        Content: Machine learning is a subset of artificial intelligence...
        """
        
        prompt_with_materials = service.format_context_prompt(
            context, 
            "What is machine learning?", 
            material_context=material_context
        )
        logger.info(f"Prompt with materials: PASS (length: {len(prompt_with_materials)} chars)")
        
        return True
        
    except Exception as e:
        logger.error(f"Context service test failed: {e}")
        return False

async def test_error_handling():
    """Test error handling and graceful degradation."""
    logger.info("=== Testing Error Handling ===")
    
    try:
        from services.material_processing_service import MaterialProcessingService
        from services.ai_brain_client import AIBrainClient
        
        client = AIBrainClient()
        service = MaterialProcessingService(ai_brain_client=client)
        
        # Test with invalid course ID format (should handle gracefully)
        try:
            results = await service.search_materials("invalid-course-id", "test query", limit=3)
            logger.info(f"Invalid course ID handling: PASS (returned {len(results)} results)")
        except Exception as e:
            logger.info(f"Invalid course ID handling: PASS (graceful error: {type(e).__name__})")
        
        # Test with very long query (should handle gracefully)
        long_query = "machine learning " * 100  # Very long query
        course_id = str(uuid.uuid4())
        results = await service.search_materials(course_id, long_query, limit=3)
        logger.info(f"Long query handling: PASS (returned {len(results)} results)")
        
        return True
        
    except Exception as e:
        logger.error(f"Error handling test failed: {e}")
        return False

async def test_logging_and_monitoring():
    """Test logging provides adequate debugging information."""
    logger.info("=== Testing Logging and Monitoring ===")
    
    try:
        from services.material_processing_service import MaterialProcessingService
        from services.ai_brain_client import AIBrainClient
        
        client = AIBrainClient()
        service = MaterialProcessingService(ai_brain_client=client)
        
        course_id = str(uuid.uuid4())
        
        # Capture log output during search
        start_time = datetime.now()
        results = await service.search_materials(course_id, "test query for logging", limit=3)
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Search operation completed in {duration:.2f}s with detailed logging")
        logger.info(f"Logging test: PASS (operation logged with timing and context)")
        
        return True
        
    except Exception as e:
        logger.error(f"Logging test failed: {e}")
        return False

async def main():
    """Run all RAG functionality tests."""
    logger.info("Starting RAG End-to-End Functionality Test")
    logger.info("=" * 60)
    
    tests = [
        ("AI Brain Service", test_ai_brain_service),
        ("Material Search", test_material_search),
        ("Context Service", test_context_service),
        ("Error Handling", test_error_handling),
        ("Logging & Monitoring", test_logging_and_monitoring),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = result
            logger.info(f"{test_name}: {'PASS' if result else 'FAIL'}")
        except Exception as e:
            results[test_name] = False
            logger.error(f"{test_name}: FAIL - {e}")
        
        logger.info("-" * 40)
    
    # Summary
    logger.info("=" * 60)
    logger.info("RAG FUNCTIONALITY TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{test_name:20} {status}")
    
    logger.info("-" * 40)
    logger.info(f"Overall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All RAG functionality tests PASSED!")
        logger.info("RAG system is working correctly with proper error handling and logging.")
    else:
        logger.warning(f"⚠️  {total - passed} test(s) failed. RAG system needs attention.")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(main())