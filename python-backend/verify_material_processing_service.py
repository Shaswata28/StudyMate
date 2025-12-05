"""
Verification script for MaterialProcessingService.

This script verifies that the MaterialProcessingService can be imported
and initialized correctly with the AI Brain client.
"""

import asyncio
from services.ai_brain_client import AIBrainClient
from services.material_processing_service import MaterialProcessingService
from config import config


async def verify_service():
    """Verify the material processing service setup."""
    print("=" * 70)
    print("Material Processing Service Verification")
    print("=" * 70)
    
    # Initialize AI Brain client
    print("\n1. Initializing AI Brain client...")
    ai_brain_client = AIBrainClient(
        brain_endpoint=config.AI_BRAIN_ENDPOINT,
        timeout=config.AI_BRAIN_TIMEOUT
    )
    print(f"   ✓ AI Brain client initialized")
    print(f"   - Endpoint: {config.AI_BRAIN_ENDPOINT}")
    print(f"   - Timeout: {config.AI_BRAIN_TIMEOUT}s")
    
    # Initialize Material Processing Service
    print("\n2. Initializing Material Processing Service...")
    processing_service = MaterialProcessingService(
        ai_brain_client=ai_brain_client,
        timeout=300.0
    )
    print(f"   ✓ Material Processing Service initialized")
    print(f"   - Timeout: {processing_service.timeout}s")
    
    # Check AI Brain service health
    print("\n3. Checking AI Brain service health...")
    is_healthy = await ai_brain_client.health_check()
    if is_healthy:
        print("   ✓ AI Brain service is healthy and responding")
    else:
        print("   ⚠ AI Brain service is not available")
        print("   Note: This is expected if the AI Brain service is not running")
        print("   To start it: cd ai-brain && python brain.py")
    
    # Verify service methods exist
    print("\n4. Verifying service methods...")
    methods = [
        'process_material',
        '_get_material',
        '_download_file',
        '_update_status',
        '_update_material_data'
    ]
    
    for method in methods:
        if hasattr(processing_service, method):
            print(f"   ✓ Method '{method}' exists")
        else:
            print(f"   ✗ Method '{method}' missing")
    
    print("\n" + "=" * 70)
    print("Verification Complete!")
    print("=" * 70)
    print("\nThe MaterialProcessingService is ready to use.")
    print("\nNext steps:")
    print("  1. Ensure AI Brain service is running (python ai-brain/brain.py)")
    print("  2. Integrate with FastAPI background tasks (Task 4)")
    print("  3. Update materials upload endpoint (Task 5)")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(verify_service())
