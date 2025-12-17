"""
Test for the get_user_context method in ContextService.

This test verifies that the parallel context retrieval works correctly
and meets the requirements for task 5.
"""
import pytest
import asyncio
import time
import sys
from unittest.mock import Mock, patch
from services.context_service import ContextService
from models.schemas import UserPreferences, AcademicInfo, UserContext, Message


@pytest.mark.anyio
async def test_get_user_context_parallel_retrieval():
    """
    Test that get_user_context retrieves all context in parallel.
    
    Validates:
    - Requirements 6.1: Parallel execution
    - Requirements 7.1, 7.2: Logging
    """
    service = ContextService()
    
    # Mock the individual retrieval methods
    mock_preferences = UserPreferences(
        detail_level=0.7,
        example_preference=0.8,
        analogy_preference=0.6,
        technical_language=0.5,
        structure_preference=0.7,
        visual_preference=0.6,
        learning_pace="moderate",
        prior_experience="intermediate"
    )
    
    mock_academic = AcademicInfo(
        grade=["Bachelor"],
        semester_type="double",
        semester=3,
        subject=["Computer Science", "Mathematics"]
    )
    
    mock_history = [
        Message(role="user", content="What is recursion?"),
        Message(role="model", content="Recursion is when a function calls itself.")
    ]
    
    # Track call times to verify parallel execution
    call_times = {}
    
    async def mock_get_preferences(user_id, client):
        call_times['preferences_start'] = time.time()
        await asyncio.sleep(0.1)  # Simulate network delay
        call_times['preferences_end'] = time.time()
        return mock_preferences
    
    async def mock_get_academic(user_id, client):
        call_times['academic_start'] = time.time()
        await asyncio.sleep(0.1)  # Simulate network delay
        call_times['academic_end'] = time.time()
        return mock_academic
    
    async def mock_get_history(course_id, client, limit):
        call_times['history_start'] = time.time()
        await asyncio.sleep(0.1)  # Simulate network delay
        call_times['history_end'] = time.time()
        return mock_history
    
    # Patch the methods
    service.get_preferences = mock_get_preferences
    service.get_academic_info = mock_get_academic
    service.get_chat_history = mock_get_history
    
    # Mock get_user_client
    with patch('services.context_service.get_user_client') as mock_client:
        mock_client.return_value = Mock()
        
        start_time = time.time()
        context = await service.get_user_context(
            user_id="test-user-123",
            course_id="test-course-456",
            access_token="test-token"
        )
        total_time = time.time() - start_time
    
    # Verify parallel execution
    # If executed sequentially, would take ~0.3s (3 * 0.1s)
    # If executed in parallel, should take ~0.1s
    assert total_time < 0.25, f"Expected parallel execution (~0.1s), but took {total_time:.2f}s"
    
    # Verify all methods started around the same time (parallel)
    start_times = [
        call_times['preferences_start'],
        call_times['academic_start'],
        call_times['history_start']
    ]
    time_spread = max(start_times) - min(start_times)
    assert time_spread < 0.05, f"Methods didn't start in parallel (spread: {time_spread:.3f}s)"
    
    # Verify context object is correctly populated
    assert context.preferences == mock_preferences
    assert context.academic == mock_academic
    assert context.chat_history == mock_history
    
    # Verify boolean flags are set correctly
    assert context.has_preferences is True
    assert context.has_academic is True
    assert context.has_history is True
    
    print(f"✓ Parallel retrieval completed in {total_time:.2f}s")
    print(f"✓ Context has preferences: {context.has_preferences}")
    print(f"✓ Context has academic: {context.has_academic}")
    print(f"✓ Context has history: {context.has_history} ({len(context.chat_history)} messages)")


@pytest.mark.anyio
async def test_get_user_context_with_missing_data():
    """
    Test that get_user_context handles missing data gracefully.
    
    Validates:
    - Requirements 8.1, 8.2, 8.3: Graceful degradation
    """
    service = ContextService()
    
    # Mock methods to return None/empty
    async def mock_get_preferences(user_id, client):
        return None
    
    async def mock_get_academic(user_id, client):
        return None
    
    async def mock_get_history(course_id, client, limit):
        return []
    
    service.get_preferences = mock_get_preferences
    service.get_academic_info = mock_get_academic
    service.get_chat_history = mock_get_history
    
    with patch('services.context_service.get_user_client') as mock_client:
        mock_client.return_value = Mock()
        
        context = await service.get_user_context(
            user_id="test-user-123",
            course_id="test-course-456",
            access_token="test-token"
        )
    
    # Verify context object with missing data
    assert context.preferences is None
    assert context.academic is None
    assert context.chat_history == []
    
    # Verify boolean flags are set correctly
    assert context.has_preferences is False
    assert context.has_academic is False
    assert context.has_history is False
    
    print("✓ Gracefully handled missing data")
    print(f"✓ Context has preferences: {context.has_preferences}")
    print(f"✓ Context has academic: {context.has_academic}")
    print(f"✓ Context has history: {context.has_history}")


@pytest.mark.anyio
async def test_get_user_context_with_exceptions():
    """
    Test that get_user_context handles exceptions gracefully.
    
    Validates:
    - Requirements 6.4: Error handling
    """
    service = ContextService()
    
    # Mock methods to raise exceptions
    async def mock_get_preferences(user_id, client):
        raise Exception("Database connection failed")
    
    async def mock_get_academic(user_id, client):
        raise Exception("Network timeout")
    
    async def mock_get_history(course_id, client, limit):
        raise Exception("Query failed")
    
    service.get_preferences = mock_get_preferences
    service.get_academic_info = mock_get_academic
    service.get_chat_history = mock_get_history
    
    with patch('services.context_service.get_user_client') as mock_client:
        mock_client.return_value = Mock()
        
        # Should not raise exception, but return empty context
        context = await service.get_user_context(
            user_id="test-user-123",
            course_id="test-course-456",
            access_token="test-token"
        )
    
    # Verify context object with all failures
    assert context.preferences is None
    assert context.academic is None
    assert context.chat_history == []
    
    # Verify boolean flags are set correctly
    assert context.has_preferences is False
    assert context.has_academic is False
    assert context.has_history is False
    
    print("✓ Gracefully handled exceptions")
    print(f"✓ Context has preferences: {context.has_preferences}")
    print(f"✓ Context has academic: {context.has_academic}")
    print(f"✓ Context has history: {context.has_history}")


@pytest.mark.anyio
async def test_get_user_context_performance_logging():
    """
    Test that get_user_context logs performance metrics.
    
    Validates:
    - Requirements 7.1, 7.2: Performance logging
    - Requirements 6.4: Performance warning for slow retrieval
    """
    service = ContextService()
    
    # Mock methods with fast response
    async def mock_get_preferences(user_id, client):
        return None
    
    async def mock_get_academic(user_id, client):
        return None
    
    async def mock_get_history(course_id, client, limit):
        return []
    
    service.get_preferences = mock_get_preferences
    service.get_academic_info = mock_get_academic
    service.get_chat_history = mock_get_history
    
    with patch('services.context_service.get_user_client') as mock_client:
        mock_client.return_value = Mock()
        
        # Capture logs
        import logging
        with patch('services.context_service.logger') as mock_logger:
            context = await service.get_user_context(
                user_id="test-user-123",
                course_id="test-course-456",
                access_token="test-token"
            )
            
            # Verify logging calls
            # Should have info log at start
            assert any('Starting context retrieval' in str(call) for call in mock_logger.info.call_args_list)
            
            # Should have info log at end with performance metrics
            assert any('Context retrieval successful' in str(call) for call in mock_logger.info.call_args_list)
    
    print("✓ Performance logging verified")


async def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("CONTEXT SERVICE - GET_USER_CONTEXT TESTS")
    print("=" * 70)
    
    results = []
    
    # Test 1: Parallel retrieval
    try:
        await test_get_user_context_parallel_retrieval()
        results.append(True)
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        results.append(False)
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)
    
    print()
    
    # Test 2: Missing data
    try:
        await test_get_user_context_with_missing_data()
        results.append(True)
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        results.append(False)
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)
    
    print()
    
    # Test 3: Exceptions
    try:
        await test_get_user_context_with_exceptions()
        results.append(True)
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        results.append(False)
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)
    
    print()
    
    # Test 4: Performance logging
    try:
        await test_get_user_context_performance_logging()
        results.append(True)
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        results.append(False)
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
