"""
Tests for AI Brain Client.
Verifies communication with the local AI Brain service.
"""

import pytest
import httpx
from services.ai_brain_client import AIBrainClient, AIBrainClientError


@pytest.mark.asyncio
async def test_health_check_success():
    """Test health check when AI Brain service is available"""
    client = AIBrainClient()
    
    # This will only pass if AI Brain service is running
    is_healthy = await client.health_check()
    
    # If service is running, should return True
    # If not running, should return False (not raise exception)
    assert isinstance(is_healthy, bool)


@pytest.mark.asyncio
async def test_health_check_unavailable():
    """Test health check when AI Brain service is unavailable"""
    # Use invalid endpoint
    client = AIBrainClient(brain_endpoint="http://localhost:9999")
    
    is_healthy = await client.health_check()
    
    # Should return False, not raise exception
    assert is_healthy is False


@pytest.mark.asyncio
async def test_extract_text_empty_input():
    """Test text extraction with empty file data"""
    client = AIBrainClient()
    
    # This test requires AI Brain service to be running
    # If service is unavailable, it should raise AIBrainClientError
    try:
        result = await client.extract_text(b"", "empty.txt")
        # If service is running, should return a string (possibly empty)
        assert isinstance(result, str)
    except AIBrainClientError as e:
        # If service is not running, this is expected
        assert "unavailable" in str(e).lower() or "timeout" in str(e).lower()


@pytest.mark.asyncio
async def test_generate_embedding_empty_text():
    """Test embedding generation with empty text"""
    client = AIBrainClient()
    
    # Empty text should raise error
    with pytest.raises(AIBrainClientError, match="empty text"):
        await client.generate_embedding("")


@pytest.mark.asyncio
async def test_generate_embedding_whitespace_only():
    """Test embedding generation with whitespace-only text"""
    client = AIBrainClient()
    
    # Whitespace-only text should raise error
    with pytest.raises(AIBrainClientError, match="empty text"):
        await client.generate_embedding("   \n\t  ")


@pytest.mark.asyncio
async def test_client_initialization():
    """Test AI Brain client initialization"""
    # Default initialization
    client1 = AIBrainClient()
    assert client1.brain_endpoint == "http://localhost:8001"
    assert client1.timeout.read == 300.0
    
    # Custom initialization
    client2 = AIBrainClient(
        brain_endpoint="http://example.com:8080",
        timeout=60.0
    )
    assert client2.brain_endpoint == "http://example.com:8080"
    assert client2.timeout.read == 60.0


@pytest.mark.asyncio
async def test_extract_text_service_unavailable():
    """Test text extraction when service is unavailable"""
    client = AIBrainClient(brain_endpoint="http://localhost:9999")
    
    with pytest.raises(AIBrainClientError, match="unavailable"):
        await client.extract_text(b"test data", "test.txt")


@pytest.mark.asyncio
async def test_generate_embedding_service_unavailable():
    """Test embedding generation when service is unavailable"""
    client = AIBrainClient(brain_endpoint="http://localhost:9999")
    
    with pytest.raises(AIBrainClientError, match="unavailable"):
        await client.generate_embedding("test text")


@pytest.mark.asyncio
async def test_endpoint_trailing_slash_handling():
    """Test that trailing slashes in endpoint are handled correctly"""
    client1 = AIBrainClient(brain_endpoint="http://localhost:8001/")
    client2 = AIBrainClient(brain_endpoint="http://localhost:8001")
    
    # Both should normalize to same endpoint
    assert client1.brain_endpoint == client2.brain_endpoint
    assert client1.brain_endpoint == "http://localhost:8001"
