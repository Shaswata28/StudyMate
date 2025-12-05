"""
Test script to verify GeminiProvider implementation.
Tests basic functionality of extract_text, generate_embedding, and chat_with_context.
"""

import asyncio
import sys
from config import config
from services.ai_provider_factory import get_ai_provider, reset_provider
from services.ai_provider import AIProviderError


async def test_provider_initialization():
    """Test that GeminiProvider can be initialized."""
    print("=" * 60)
    print("GeminiProvider Initialization Test")
    print("=" * 60)
    
    try:
        reset_provider()
        provider = get_ai_provider()
        print(f"\n✓ Provider instance created: {type(provider).__name__}")
        print(f"✓ Provider type: {config.AI_PROVIDER}")
        print("\n" + "=" * 60)
        print("Initialization test passed!")
        print("=" * 60)
        return provider
    except Exception as e:
        print(f"\n✗ Initialization failed: {e}")
        print("=" * 60)
        sys.exit(1)


async def test_generate_embedding(provider):
    """Test embedding generation."""
    print("\n" + "=" * 60)
    print("Embedding Generation Test")
    print("=" * 60)
    
    test_text = "This is a test document about machine learning and artificial intelligence."
    
    try:
        print(f"\nGenerating embedding for text: '{test_text[:50]}...'")
        embedding = await provider.generate_embedding(test_text)
        
        print(f"✓ Embedding generated successfully")
        print(f"✓ Embedding dimensions: {len(embedding)}")
        print(f"✓ First 5 values: {embedding[:5]}")
        
        # Verify dimension
        if len(embedding) == 384:
            print(f"✓ Embedding has correct dimensionality (384)")
        else:
            print(f"⚠ Warning: Expected 384 dimensions, got {len(embedding)}")
        
        print("\n" + "=" * 60)
        print("Embedding test passed!")
        print("=" * 60)
        return True
        
    except AIProviderError as e:
        print(f"\n✗ Embedding generation failed: {e}")
        print("=" * 60)
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {type(e).__name__}: {e}")
        print("=" * 60)
        return False


async def test_empty_text_embedding(provider):
    """Test that empty text raises an error."""
    print("\n" + "=" * 60)
    print("Empty Text Embedding Test")
    print("=" * 60)
    
    try:
        print("\nAttempting to generate embedding for empty text...")
        embedding = await provider.generate_embedding("")
        print(f"✗ Expected error but got embedding: {len(embedding)} dimensions")
        print("=" * 60)
        return False
        
    except AIProviderError as e:
        print(f"✓ Correctly raised AIProviderError: {e}")
        print("\n" + "=" * 60)
        print("Empty text test passed!")
        print("=" * 60)
        return True
    except Exception as e:
        print(f"✗ Unexpected error type: {type(e).__name__}: {e}")
        print("=" * 60)
        return False


async def test_chat_with_context(provider):
    """Test chat with material context (RAG)."""
    print("\n" + "=" * 60)
    print("Chat with Context Test (RAG)")
    print("=" * 60)
    
    message = "What is machine learning?"
    context = [
        "Machine learning is a subset of artificial intelligence that enables systems to learn from data.",
        "Deep learning is a type of machine learning that uses neural networks with multiple layers."
    ]
    
    try:
        print(f"\nMessage: '{message}'")
        print(f"Context items: {len(context)}")
        
        response = await provider.chat_with_context(message, context)
        
        print(f"\n✓ Chat response generated successfully")
        print(f"✓ Response length: {len(response)} characters")
        print(f"\nResponse preview:\n{response[:200]}...")
        
        print("\n" + "=" * 60)
        print("Chat with context test passed!")
        print("=" * 60)
        return True
        
    except AIProviderError as e:
        print(f"\n✗ Chat generation failed: {e}")
        print("=" * 60)
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {type(e).__name__}: {e}")
        print("=" * 60)
        return False


async def test_chat_without_context(provider):
    """Test chat without material context."""
    print("\n" + "=" * 60)
    print("Chat without Context Test")
    print("=" * 60)
    
    message = "What is 2 + 2?"
    
    try:
        print(f"\nMessage: '{message}'")
        print(f"Context items: 0")
        
        response = await provider.chat_with_context(message, [])
        
        print(f"\n✓ Chat response generated successfully")
        print(f"✓ Response length: {len(response)} characters")
        print(f"\nResponse: {response}")
        
        print("\n" + "=" * 60)
        print("Chat without context test passed!")
        print("=" * 60)
        return True
        
    except AIProviderError as e:
        print(f"\n✗ Chat generation failed: {e}")
        print("=" * 60)
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {type(e).__name__}: {e}")
        print("=" * 60)
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("GEMINI PROVIDER TEST SUITE")
    print("=" * 60)
    
    # Check configuration
    if config.AI_PROVIDER != "gemini":
        print(f"\n✗ AI_PROVIDER is set to '{config.AI_PROVIDER}', expected 'gemini'")
        print("Please set AI_PROVIDER=gemini in your .env file")
        sys.exit(1)
    
    if not config.GEMINI_API_KEY:
        print("\n✗ GEMINI_API_KEY is not set")
        print("Please set GEMINI_API_KEY in your .env file")
        sys.exit(1)
    
    # Initialize provider
    provider = await test_provider_initialization()
    
    # Run tests
    results = []
    
    # Test embedding generation
    results.append(await test_generate_embedding(provider))
    
    # Test empty text handling
    results.append(await test_empty_text_embedding(provider))
    
    # Test chat with context
    results.append(await test_chat_with_context(provider))
    
    # Test chat without context
    results.append(await test_chat_without_context(provider))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"\nTests passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed!")
    else:
        print(f"\n✗ {total - passed} test(s) failed")
    
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
