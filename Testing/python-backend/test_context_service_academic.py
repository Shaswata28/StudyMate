"""
Test script to verify ContextService.get_academic_info() method.

This script tests:
- Retrieving existing academic info
- Handling missing academic info (returns None)
- Error handling and logging

Requirements: 3.1, 3.2, 3.3, 8.2
"""
import asyncio
import sys
from services.context_service import ContextService
from services.supabase_client import get_user_client, supabase_admin
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_get_academic_info_with_existing_user():
    """Test retrieving academic info for a user with academic data."""
    print("\n" + "=" * 70)
    print("TEST: Get academic info for user WITH academic data")
    print("=" * 70)
    
    try:
        # Create a test user
        import time
        timestamp = str(int(time.time() * 1000))
        email = f"test.academic.{timestamp}@example.com"
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
        
        # Create academic info for the user
        print("\n2. Creating academic info for user")
        client = get_user_client(access_token)
        academic_data = {
            "id": user_id,
            "grade": ["Bachelor"],
            "semester_type": "double",
            "semester": 3,
            "subject": ["Computer Science", "Mathematics"]
        }
        academic_result = client.table("academic").insert(academic_data).execute()
        
        if not academic_result.data:
            print("❌ Failed to create academic info")
            return False
        
        print(f"✅ Academic info created")
        
        # Test get_academic_info
        print("\n3. Testing ContextService.get_academic_info()")
        context_service = ContextService()
        academic_info = await context_service.get_academic_info(user_id, client)
        
        if academic_info is None:
            print("❌ get_academic_info returned None for existing academic info")
            return False
        
        print(f"✅ Academic info retrieved successfully")
        print(f"   - Grade: {academic_info.grade}")
        print(f"   - Semester type: {academic_info.semester_type}")
        print(f"   - Semester: {academic_info.semester}")
        print(f"   - Subjects: {academic_info.subject}")
        
        # Verify values match
        if academic_info.grade != academic_data["grade"]:
            print(f"❌ Grade mismatch")
            return False
        
        if academic_info.semester_type != academic_data["semester_type"]:
            print(f"❌ Semester type mismatch")
            return False
        
        if academic_info.semester != academic_data["semester"]:
            print(f"❌ Semester mismatch")
            return False
        
        if academic_info.subject != academic_data["subject"]:
            print(f"❌ Subject mismatch")
            return False
        
        print("\n✅ TEST PASSED: get_academic_info works with existing academic data")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_get_academic_info_without_academic_data():
    """Test retrieving academic info for a user without academic data."""
    print("\n" + "=" * 70)
    print("TEST: Get academic info for user WITHOUT academic data")
    print("=" * 70)
    
    try:
        # Create a test user
        import time
        timestamp = str(int(time.time() * 1000))
        email = f"test.academic.nodata.{timestamp}@example.com"
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
        
        # Do NOT create academic info - test missing academic data case
        print("\n2. Skipping academic info creation (testing missing data)")
        
        # Test get_academic_info
        print("\n3. Testing ContextService.get_academic_info()")
        context_service = ContextService()
        client = get_user_client(access_token)
        academic_info = await context_service.get_academic_info(user_id, client)
        
        if academic_info is not None:
            print(f"❌ get_academic_info returned {academic_info} instead of None")
            return False
        
        print(f"✅ get_academic_info correctly returned None for missing academic data")
        
        print("\n✅ TEST PASSED: get_academic_info handles missing academic data")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_get_academic_info_error_handling():
    """Test error handling with invalid data."""
    print("\n" + "=" * 70)
    print("TEST: Get academic info error handling")
    print("=" * 70)
    
    try:
        # Test with invalid user_id
        print("\n1. Testing with invalid user_id")
        context_service = ContextService()
        
        # Use a non-existent user ID
        fake_user_id = "00000000-0000-0000-0000-000000000000"
        
        # Get admin session token
        admin_token = supabase_admin.auth.get_session()
        if admin_token and hasattr(admin_token, 'access_token'):
            client = get_user_client(admin_token.access_token)
        else:
            # Fallback: use admin client directly
            client = supabase_admin
        
        academic_info = await context_service.get_academic_info(fake_user_id, client)
        
        if academic_info is not None:
            print(f"❌ Expected None for non-existent user, got {academic_info}")
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
    print("CONTEXT SERVICE - ACADEMIC INFO RETRIEVAL TESTS")
    print("=" * 70)
    
    results = []
    
    # Test 1: Get academic info with existing user
    results.append(await test_get_academic_info_with_existing_user())
    
    # Test 2: Get academic info without academic data
    results.append(await test_get_academic_info_without_academic_data())
    
    # Test 3: Error handling
    results.append(await test_get_academic_info_error_handling())
    
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
