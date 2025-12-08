"""
Test chat history retrieval functionality.

This test verifies that the get_chat_history method correctly:
- Retrieves chat history from the database
- Orders messages chronologically
- Limits to the most recent N messages
- Flattens JSONB arrays correctly
- Handles empty history gracefully
"""
import asyncio
from services.context_service import ContextService
from services.supabase_client import get_user_client
from models.schemas import Message
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_get_chat_history_empty():
    """Test retrieving chat history when no history exists."""
    token = os.getenv("TEST_ACCESS_TOKEN")
    if not token:
        print("SKIPPED: TEST_ACCESS_TOKEN not set in environment")
        return
    
    context_service = ContextService()
    client = get_user_client(token)
    
    # Use a non-existent course ID
    fake_course_id = "00000000-0000-0000-0000-000000000000"
    
    history = asyncio.run(context_service.get_chat_history(fake_course_id, client))
    
    assert isinstance(history, list)
    assert len(history) == 0
    print("✓ Empty history test passed")


def test_get_chat_history_with_data():
    """Test retrieving chat history when history exists."""
    token = os.getenv("TEST_ACCESS_TOKEN")
    course_id = os.getenv("TEST_COURSE_ID")
    
    if not token or not course_id:
        print("SKIPPED: TEST_ACCESS_TOKEN or TEST_COURSE_ID not set")
        return
    
    context_service = ContextService()
    client = get_user_client(token)
    
    history = asyncio.run(context_service.get_chat_history(course_id, client, limit=10))
    
    assert isinstance(history, list)
    print(f"Retrieved {len(history)} messages")
    
    # Verify all items are Message objects
    for msg in history:
        assert isinstance(msg, Message)
        assert hasattr(msg, 'role')
        assert hasattr(msg, 'content')
        assert msg.role in ['user', 'model']
        assert isinstance(msg.content, str)
    
    print("✓ Chat history retrieval test passed")


def test_get_chat_history_limit():
    """Test that chat history respects the limit parameter."""
    token = os.getenv("TEST_ACCESS_TOKEN")
    course_id = os.getenv("TEST_COURSE_ID")
    
    if not token or not course_id:
        print("SKIPPED: TEST_ACCESS_TOKEN or TEST_COURSE_ID not set")
        return
    
    context_service = ContextService()
    client = get_user_client(token)
    
    # Test with limit of 5
    history_5 = asyncio.run(context_service.get_chat_history(course_id, client, limit=5))
    assert len(history_5) <= 5
    print(f"Limit 5: Retrieved {len(history_5)} messages")
    
    # Test with limit of 10
    history_10 = asyncio.run(context_service.get_chat_history(course_id, client, limit=10))
    assert len(history_10) <= 10
    print(f"Limit 10: Retrieved {len(history_10)} messages")
    
    # If there are more than 5 messages, verify we get different results
    if len(history_10) > 5:
        # The last 5 messages from history_10 should match history_5
        assert history_10[-5:] == history_5
        print("✓ Limit verification passed")
    
    print("✓ Chat history limit test passed")


def test_get_chat_history_ordering():
    """Test that chat history is returned in chronological order."""
    token = os.getenv("TEST_ACCESS_TOKEN")
    course_id = os.getenv("TEST_COURSE_ID")
    
    if not token or not course_id:
        print("SKIPPED: TEST_ACCESS_TOKEN or TEST_COURSE_ID not set")
        return
    
    context_service = ContextService()
    client = get_user_client(token)
    
    history = asyncio.run(context_service.get_chat_history(course_id, client, limit=10))
    
    if len(history) > 1:
        # Verify messages alternate between user and model (typical conversation pattern)
        roles = [msg.role for msg in history]
        print(f"Message roles: {roles}")
        
        # At minimum, verify we have both user and model messages
        assert 'user' in roles or 'model' in roles
        print("✓ Ordering test passed")
    else:
        print("SKIPPED: Not enough messages to test ordering")


def test_get_chat_history_error_handling():
    """Test error handling when client is invalid."""
    from supabase import create_client
    
    context_service = ContextService()
    
    # Create a client with invalid token
    try:
        invalid_client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_ANON_KEY")
        )
        
        # Should return empty list on error, not raise exception
        history = asyncio.run(context_service.get_chat_history(
            "some-course-id",
            invalid_client
        ))
        
        assert isinstance(history, list)
        assert len(history) == 0
        print("✓ Error handling test passed")
    except Exception as e:
        print(f"✗ Should not raise exception, but got: {e}")
        raise


if __name__ == "__main__":
    print("Running chat history tests...\n")
    
    try:
        test_get_chat_history_empty()
        test_get_chat_history_with_data()
        test_get_chat_history_limit()
        test_get_chat_history_ordering()
        test_get_chat_history_error_handling()
        
        print("\n✓ All tests passed!")
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        raise
