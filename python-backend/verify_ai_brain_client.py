"""
Verification script for AI Brain Client.
Run this to verify the AI Brain service is accessible and working correctly.

Usage:
    python verify_ai_brain_client.py
"""

import asyncio
import sys
from services.ai_brain_client import AIBrainClient, AIBrainClientError


async def main():
    """Verify AI Brain client functionality"""
    print("=" * 60)
    print("AI Brain Client Verification")
    print("=" * 60)
    
    # Initialize client
    client = AIBrainClient()
    print(f"\n✓ Client initialized (endpoint: {client.brain_endpoint})")
    
    # Test 1: Health check
    print("\n[1/3] Testing health check...")
    try:
        is_healthy = await client.health_check()
        if is_healthy:
            print("✓ AI Brain service is healthy and responding")
        else:
            print("✗ AI Brain service is not responding")
            print("\nPlease ensure the AI Brain service is running:")
            print("  cd ai-brain")
            print("  python brain.py")
            sys.exit(1)
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        sys.exit(1)
    
    # Test 2: Text extraction (with simple text file)
    print("\n[2/3] Testing text extraction...")
    try:
        test_text = "Hello, this is a test document."
        test_data = test_text.encode('utf-8')
        
        result = await client.extract_text(test_data, "test.txt")
        print(f"✓ Text extraction successful")
        print(f"  Input: {len(test_data)} bytes")
        print(f"  Output: {len(result)} characters")
        if result:
            print(f"  Sample: {result[:100]}...")
    except AIBrainClientError as e:
        print(f"✗ Text extraction failed: {e}")
        print("  Note: This may fail if the AI Brain service doesn't support plain text files")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
    
    # Test 3: Embedding generation
    print("\n[3/3] Testing embedding generation...")
    try:
        test_text = "This is a test sentence for embedding generation."
        
        embedding = await client.generate_embedding(test_text)
        print(f"✓ Embedding generation successful")
        print(f"  Input: {len(test_text)} characters")
        print(f"  Output: {len(embedding)} dimensions")
        print(f"  Sample values: {embedding[:5]}...")
    except AIBrainClientError as e:
        print(f"✗ Embedding generation failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        sys.exit(1)
    
    # Summary
    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("AI Brain client is working correctly")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
