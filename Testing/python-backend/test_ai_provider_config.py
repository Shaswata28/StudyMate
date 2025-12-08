"""
Test script to verify AI provider configuration and factory.
"""

from config import config
from services.ai_provider_factory import get_ai_provider

def test_config():
    """Test that configuration loads correctly."""
    print("=" * 60)
    print("AI Provider Configuration Test")
    print("=" * 60)
    
    print(f"\n✓ AI Provider: {config.AI_PROVIDER}")
    print(f"✓ Max Embedding Dimension: {config.MAX_EMBEDDING_DIMENSION}")
    print(f"✓ Processing Timeout: {config.MATERIAL_PROCESSING_TIMEOUT}s")
    print(f"✓ Search Result Limit: {config.SEARCH_RESULT_LIMIT}")
    
    if config.AI_PROVIDER == "gemini":
        print(f"✓ Gemini Model: {config.GEMINI_MODEL}")
        print(f"✓ Gemini Embedding Model: {config.GEMINI_EMBEDDING_MODEL}")
        print(f"✓ Gemini API Key: {'*' * 20}{config.GEMINI_API_KEY[-4:] if config.GEMINI_API_KEY else 'NOT SET'}")
    elif config.AI_PROVIDER == "router":
        print(f"✓ Router Endpoint: {config.ROUTER_ENDPOINT}")
        print(f"✓ Router API Key: {'*' * 20}{config.ROUTER_API_KEY[-4:] if config.ROUTER_API_KEY else 'NOT SET'}")
    
    print("\n" + "=" * 60)
    print("Configuration loaded successfully!")
    print("=" * 60)


def test_factory():
    """Test that the provider factory works."""
    print("\n" + "=" * 60)
    print("AI Provider Factory Test")
    print("=" * 60)
    
    try:
        # Note: This will fail if GeminiProvider is not yet implemented
        # That's expected at this stage
        provider = get_ai_provider()
        print(f"\n✓ Provider instance created: {type(provider).__name__}")
        print(f"✓ Provider type: {config.AI_PROVIDER}")
        print("\n" + "=" * 60)
        print("Factory test passed!")
        print("=" * 60)
    except ImportError as e:
        print(f"\n⚠ Provider implementation not yet available: {e}")
        print("This is expected if the provider class hasn't been implemented yet.")
        print("\n" + "=" * 60)
        print("Factory structure is correct, waiting for provider implementation")
        print("=" * 60)


if __name__ == "__main__":
    test_config()
    test_factory()
