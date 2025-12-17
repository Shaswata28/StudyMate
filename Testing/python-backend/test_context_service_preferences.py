"""
Test script to verify ContextService.get_preferences() method.

This script tests:
- Retrieving existing preferences
- Handling missing preferences (returns None)
- Error handling and logging

Requirements: 2.1, 2.2, 2.3, 8.1
"""
import asyncio
import sys
from services.context_service import ContextService
from services.supabase_client import get_user_client, supabase_admin
from constants import DEFAULT_PREFERENCES
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_get_preferences_with_existing_user():
    """Test retrieving preferences for a user with preferences."""
    print("\n" + "=" * 70)
    print("TEST: Get preferences for user WITH preferences")
    print("=" * 70)
    
    try:
        # Create a test user
        email = f"test_context_{asyncio.get_event_loop().time()}@example.com"
        password = "TestPassword123!"
        
        print(f"\n1. Creating test user: {email}")
        signup_response = supabase_admin.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if not signup_response.user:
            print("❌ Failed to create test user")
            return False
        
        user_id = signup_response.user.id
        access_token = signup_response.session.access_token
        print(f"✅ User created: {user_id}")
        
        # Create preferences for the user
        print("\n2. Creating preferences for user")
        client = get_user_client(access_token)
        prefs_result = client.table("personalized").insert({
            "id": user_id,
            "prefs": DEFAULT_PREFERENCES
        }).execute()
        
        if not prefs_result.data:
            print("❌ Failed to create preferences")
            return False
        
        print(f"✅ Preferences created")
        
        # Test get_preferences
        print("\n3. Testing ContextService.get_preferences()")
        context_service = ContextService()
        preferences = await context_service.get_preferences(user_id, client)
        
        if preferences is None:
            print("❌ get_preferences returned None for existing preferences")
            return False
        
        print(f"✅ Preferences retrieved successfully")
        print(f"   - Detail level: {preferences.detail_level}")
        print(f"   - Learning pace: {preferences.learning_pace}")
        print(f"   - Prior experience: {preferences.prior_experience}")
        
        # Verify values match
        if preferences.detail_level != DEFAULT_PREFERENCES["detail_level"]:
            print(f"❌ Detail level mismatch")
            return False
        
        if preferences.learning_pace != DEFAULT_PREFERENCES["learning_pace"]:
            print(f"❌ Learning pace mismatch")
            return False
        
        print("\n✅ TEST PASSED: get_preferences works with existing preferences")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_get_preferences_without_preferences():
    """Test retrieving preferences for a user without preferences."""
    print("\n" + "=" * 70)
    print("TEST: Get preferences for user WITHOUT preferences")
    print("=" * 70)
    
    try:
        # Create a test user
        email = f"test_context_no_prefs_{asyncio.get_event_loop().time()}@example.com"
        password = "TestPassword123!"
        
        print(f"\n1. Creating test user: {email}")
        signup_response = supabase_admin.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if not signup_response.user:
            print("❌ Failed to create test user")
            return False
        
        user_id = signup_response.user.id
        access_token = signup_response.session.access_token
        print(f"✅ User created: {user_id}")
        
        # Do NOT create preferences - test missing preferences case
        print("\n2. Skipping preference creation (testing missing preferences)")
        
        # Test get_preferences
        print("\n3. Testing ContextService.get_preferences()")
        context_service = ContextService()
        client = get_user_client(access_token)
        preferences = await context_service.get_preferences(user_id, client)
        
        if preferences is not None:
            print(f"❌ get_preferences returned {preferences} instead of None")
            return False
        
        print(f"✅ get_preferences correctly returned None for missing preferences")
        
        print("\n✅ TEST PASSED: get_preferences handles missing preferences")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_get_preferences_error_handling():
    """Test error handling with invalid data."""
    print("\n" + "=" * 70)
    print("TEST: Get preferences error handling")
    print("=" * 70)
    
    try:
        # Test with invalid user_id
        print("\n1. Testing with invalid user_id")
        context_service = ContextService()
        
        # Create a client with admin token (for testing)
        from services.supabase_client import supabase_admin
        
        # Use a non-existent user ID
        fake_user_id = "00000000-0000-0000-0000-000000000000"
        
        # Get admin session token
        admin_token = supabase_admin.auth.get_session()
        if admin_token and hasattr(admin_token, 'access_token'):
            client = get_user_client(admin_token.access_token)
        else:
            # Fallback: use admin client directly
            client = supabase_admin
        
        preferences = await context_service.get_preferences(fake_user_id, client)
        
        if preferences is not None:
            print(f"❌ Expected None for non-existent user, got {preferences}")
            return False
        
        print(f"✅ Error handling works correctly (returned None)")
        
        print("\n✅ TEST PASSED: Error handling works correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("CONTEXT SERVICE - PREFERENCE RETRIEVAL TESTS")
    print("=" * 70)
    
    results = []
    
    # Test 1: Get preferences with existing user
    results.append(await test_get_preferences_with_existing_user())
    
    # Test 2: Get preferences without preferences
    results.append(await test_get_preferences_without_preferences())
    
    # Test 3: Error handling
    results.append(await test_get_preferences_error_handling())
    
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
