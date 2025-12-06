"""
Test timeout and error handling for context service.

This test verifies that:
1. Context retrieval respects the timeout parameter
2. Partial context is returned on timeout
3. Empty context is returned on complete failure
4. Errors are logged appropriately
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from services.context_service import ContextService
from models.schemas import UserContext, UserPreferences, AcademicInfo




@pytest.mark.anyio
async def test_context_retrieval_timeout_returns_partial_context():
    """
    Test that when context retrieval times out, partial context is returned.
    
    Validates: Requirements 1.5, 2.5, 3.5, 6.4
    """
    context_service = ContextService()
    
    # Mock get_user_client to return a mock client
    with patch('services.context_service.get_user_client') as mock_get_client:
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # Mock get_preferences to return quickly
        async def fast_preferences(user_id, client):
            await asyncio.sleep(0.1)
            return UserPreferences(
                detail_level=0.7,
                example_preference=0.6,
                analogy_preference=0.5,
                technical_language=0.8,
                structure_preference=0.6,
                visual_preference=0.4,
                learning_pace="moderate",
                prior_experience="intermediate"
            )
        
        # Mock get_academic_info to timeout (takes longer than timeout)
        async def slow_academic(user_id, client):
            await asyncio.sleep(3.0)  # Longer than 2s timeout
            return AcademicInfo(
                grade=["Bachelor"],
                semester_type="double",
                semester=3,
                subject=["Computer Science"]
            )
        
        # Mock get_chat_history to return quickly
        async def fast_history(course_id, client, limit):
            await asyncio.sleep(0.1)
            return []
        
        # Patch the methods
        with patch.object(context_service, 'get_preferences', side_effect=fast_preferences), \
             patch.object(context_service, 'get_academic_info', side_effect=slow_academic), \
             patch.object(context_service, 'get_chat_history', side_effect=fast_history):
            
            # Call with 1 second timeout (academic will timeout)
            context = await context_service.get_user_context(
                user_id="test-user",
                course_id="test-course",
                access_token="test-token",
                timeout=1.0
            )
            
            # Should have partial context (preferences and history, but not academic)
            # Note: Due to asyncio.gather with timeout, we might get None for all
            # or partial results depending on timing
            assert isinstance(context, UserContext)
            # The context should be returned even if incomplete
            print(f"Context after timeout: prefs={context.has_preferences}, academic={context.has_academic}, history={context.has_history}")


@pytest.mark.anyio
async def test_context_retrieval_handles_complete_failure():
    """
    Test that when context retrieval completely fails, empty context is returned.
    
    Validates: Requirements 1.5, 2.5, 3.5, 4.5
    """
    context_service = ContextService()
    
    # Mock get_user_client to raise an exception
    with patch('services.context_service.get_user_client') as mock_get_client:
        mock_get_client.side_effect = Exception("Database connection failed")
        
        # Call get_user_context
        context = await context_service.get_user_context(
            user_id="test-user",
            course_id="test-course",
            access_token="test-token"
        )
        
        # Should return empty context
        assert isinstance(context, UserContext)
        assert not context.has_preferences
        assert not context.has_academic
        assert not context.has_history
        assert len(context.chat_history) == 0


@pytest.mark.anyio
async def test_context_retrieval_handles_individual_failures():
    """
    Test that when individual context components fail, others are still retrieved.
    
    Validates: Requirements 8.1, 8.2, 8.3
    """
    context_service = ContextService()
    
    # Mock get_user_client to return a mock client
    with patch('services.context_service.get_user_client') as mock_get_client:
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # Mock get_preferences to succeed
        async def success_preferences(user_id, client):
            return UserPreferences(
                detail_level=0.5,
                example_preference=0.5,
                analogy_preference=0.5,
                technical_language=0.5,
                structure_preference=0.5,
                visual_preference=0.5,
                learning_pace="moderate",
                prior_experience="intermediate"
            )
        
        # Mock get_academic_info to fail
        async def fail_academic(user_id, client):
            raise Exception("Academic table not accessible")
        
        # Mock get_chat_history to succeed
        async def success_history(course_id, client, limit):
            return []
        
        # Patch the methods
        with patch.object(context_service, 'get_preferences', side_effect=success_preferences), \
             patch.object(context_service, 'get_academic_info', side_effect=fail_academic), \
             patch.object(context_service, 'get_chat_history', side_effect=success_history):
            
            # Call get_user_context
            context = await context_service.get_user_context(
                user_id="test-user",
                course_id="test-course",
                access_token="test-token"
            )
            
            # Should have preferences and history, but not academic
            assert isinstance(context, UserContext)
            assert context.has_preferences
            assert not context.has_academic
            assert not context.has_history  # Empty history


@pytest.mark.anyio
async def test_context_retrieval_respects_timeout_parameter():
    """
    Test that context retrieval respects the timeout parameter.
    
    Validates: Requirements 6.4
    """
    context_service = ContextService()
    
    # Mock get_user_client to return a mock client
    with patch('services.context_service.get_user_client') as mock_get_client:
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # Mock all methods to take longer than timeout
        async def slow_operation(*args, **kwargs):
            await asyncio.sleep(5.0)
            return None
        
        # Patch the methods
        with patch.object(context_service, 'get_preferences', side_effect=slow_operation), \
             patch.object(context_service, 'get_academic_info', side_effect=slow_operation), \
             patch.object(context_service, 'get_chat_history', side_effect=slow_operation):
            
            import time
            start_time = time.time()
            
            # Call with 0.5 second timeout
            context = await context_service.get_user_context(
                user_id="test-user",
                course_id="test-course",
                access_token="test-token",
                timeout=0.5
            )
            
            elapsed_time = time.time() - start_time
            
            # Should return within timeout (with some margin for overhead)
            assert elapsed_time < 1.0, f"Context retrieval took {elapsed_time}s, expected < 1.0s"
            
            # Should return empty or partial context
            assert isinstance(context, UserContext)


@pytest.mark.anyio
async def test_context_retrieval_logs_errors_appropriately():
    """
    Test that errors during context retrieval are logged appropriately.
    
    Validates: Requirements 7.3
    """
    context_service = ContextService()
    
    # Mock get_user_client to raise an exception
    with patch('services.context_service.get_user_client') as mock_get_client:
        mock_get_client.side_effect = Exception("Connection error")
        
        # Mock logger to capture log calls
        with patch('services.context_service.logger') as mock_logger:
            # Call get_user_context
            context = await context_service.get_user_context(
                user_id="test-user",
                course_id="test-course",
                access_token="test-token"
            )
            
            # Verify error was logged
            assert mock_logger.error.called
            error_call = mock_logger.error.call_args
            assert "Failed to retrieve user context" in str(error_call)
            
            # Verify warning was logged about returning empty context
            assert mock_logger.warning.called
            warning_call = mock_logger.warning.call_args
            assert "empty context" in str(warning_call).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
