"""
Test script to verify academic profile endpoints are working correctly.

This script tests:
- POST /api/academic - Create academic profile
- GET /api/academic - Retrieve academic profile
- PUT /api/academic - Update academic profile
- Authentication requirement (401 without token)
- Conflict handling (409 for duplicate creation)

Requirements: 2.2, 2.3, 2.4, 5.5
"""
import requests
import json
import time
from typing import Dict, Any, Optional

BASE_URL = "http://localhost:8000"

# Test user credentials
TEST_EMAIL = f"test_academic_{int(time.time())}@example.com"
TEST_PASSWORD = "SecurePassword123!"

# Test academic profile data
TEST_ACADEMIC_PROFILE = {
    "grade": ["Bachelor"],
    "semester_type": "double",
    "semester": 1,
    "subject": ["computer science", "english"]
}

UPDATED_ACADEMIC_PROFILE = {
    "grade": ["Masters"],
    "semester_type": "tri",
    "semester": 2,
    "subject": ["economics", "business administration"]
}

def print_test_header(test_name: str):
    """Print a formatted test header."""
    print("\n" + "=" * 70)
    print(f"TEST: {test_name}")
    print("=" * 70)

def print_result(success: bool, message: str, response: Any = None):
    """Print test result."""
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"{status}: {message}")
    if response and hasattr(response, 'status_code'):
        print(f"  Status Code: {response.status_code}")
        try:
            print(f"  Response: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"  Response: {response.text}")
    # Always show response for failures
    elif not success and response:
        print(f"  Response: {response}")
    print()

def create_test_user() -> Optional[Dict[str, Any]]:
    """Create a test user for academic profile testing."""
    print_test_header("Setup - Create Test User")
    
    response = requests.post(
        f"{BASE_URL}/api/auth/signup",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        headers={"Content-Type": "application/json"}
    )
    
    success = (
        response.status_code == 201 and
        "access_token" in response.json() and
        "user" in response.json()
    )
    
    print_result(success, "Test user created successfully", response)
    
    if success:
        return response.json()
    return None

def test_create_academic_profile_without_auth():
    """Test creating academic profile without authentication token."""
    print_test_header("Create Academic Profile - No Authentication")
    
    response = requests.post(
        f"{BASE_URL}/api/academic",
        json=TEST_ACADEMIC_PROFILE,
        headers={"Content-Type": "application/json"}
    )
    
    # Should return 403 (Forbidden) or 401 (Unauthorized) without token
    success = response.status_code in [401, 403]
    
    print_result(success, "Request without authentication rejected correctly", response)
    return success

def test_create_academic_profile_with_invalid_token():
    """Test creating academic profile with invalid authentication token."""
    print_test_header("Create Academic Profile - Invalid Token")
    
    response = requests.post(
        f"{BASE_URL}/api/academic",
        json=TEST_ACADEMIC_PROFILE,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer invalid_token_here"
        }
    )
    
    # Should return 401 (Unauthorized) with invalid token
    success = response.status_code == 401
    
    print_result(success, "Request with invalid token rejected correctly", response)
    return success

def test_create_academic_profile_success(auth_data: Dict[str, Any]):
    """Test successful creation of academic profile."""
    print_test_header("Create Academic Profile - Success Case")
    
    access_token = auth_data.get("access_token")
    
    response = requests.post(
        f"{BASE_URL}/api/academic",
        json=TEST_ACADEMIC_PROFILE,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
    )
    
    success = (
        response.status_code == 201 and
        "grade" in response.json() and
        "semester_type" in response.json() and
        "semester" in response.json() and
        "subject" in response.json() and
        response.json()["grade"] == TEST_ACADEMIC_PROFILE["grade"] and
        response.json()["semester_type"] == TEST_ACADEMIC_PROFILE["semester_type"] and
        response.json()["semester"] == TEST_ACADEMIC_PROFILE["semester"] and
        response.json()["subject"] == TEST_ACADEMIC_PROFILE["subject"]
    )
    
    print_result(success, "Academic profile created successfully", response)
    
    if success:
        return response.json()
    return None

def test_create_academic_profile_duplicate(auth_data: Dict[str, Any]):
    """Test creating academic profile when one already exists (conflict)."""
    print_test_header("Create Academic Profile - Duplicate (Conflict)")
    
    access_token = auth_data.get("access_token")
    
    response = requests.post(
        f"{BASE_URL}/api/academic",
        json=TEST_ACADEMIC_PROFILE,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
    )
    
    # Should return 409 (Conflict) when profile already exists
    success = (
        response.status_code == 409 and
        "already exists" in response.json().get("detail", "").lower()
    )
    
    print_result(success, "Duplicate profile creation rejected correctly", response)
    return success

def test_get_academic_profile_without_auth():
    """Test retrieving academic profile without authentication token."""
    print_test_header("Get Academic Profile - No Authentication")
    
    response = requests.get(f"{BASE_URL}/api/academic")
    
    # Should return 403 (Forbidden) or 401 (Unauthorized) without token
    success = response.status_code in [401, 403]
    
    print_result(success, "Request without authentication rejected correctly", response)
    return success

def test_get_academic_profile_with_invalid_token():
    """Test retrieving academic profile with invalid authentication token."""
    print_test_header("Get Academic Profile - Invalid Token")
    
    response = requests.get(
        f"{BASE_URL}/api/academic",
        headers={"Authorization": "Bearer invalid_token_here"}
    )
    
    # Should return 401 (Unauthorized) with invalid token
    success = response.status_code == 401
    
    print_result(success, "Request with invalid token rejected correctly", response)
    return success

def test_get_academic_profile_success(auth_data: Dict[str, Any]):
    """Test successful retrieval of academic profile."""
    print_test_header("Get Academic Profile - Success Case")
    
    access_token = auth_data.get("access_token")
    
    response = requests.get(
        f"{BASE_URL}/api/academic",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    success = (
        response.status_code == 200 and
        "grade" in response.json() and
        "semester_type" in response.json() and
        "semester" in response.json() and
        "subject" in response.json() and
        response.json()["grade"] == TEST_ACADEMIC_PROFILE["grade"] and
        response.json()["semester_type"] == TEST_ACADEMIC_PROFILE["semester_type"] and
        response.json()["semester"] == TEST_ACADEMIC_PROFILE["semester"] and
        response.json()["subject"] == TEST_ACADEMIC_PROFILE["subject"]
    )
    
    print_result(success, "Academic profile retrieved successfully", response)
    return success

def test_update_academic_profile_without_auth():
    """Test updating academic profile without authentication token."""
    print_test_header("Update Academic Profile - No Authentication")
    
    response = requests.put(
        f"{BASE_URL}/api/academic",
        json=UPDATED_ACADEMIC_PROFILE,
        headers={"Content-Type": "application/json"}
    )
    
    # Should return 403 (Forbidden) or 401 (Unauthorized) without token
    success = response.status_code in [401, 403]
    
    print_result(success, "Request without authentication rejected correctly", response)
    return success

def test_update_academic_profile_with_invalid_token():
    """Test updating academic profile with invalid authentication token."""
    print_test_header("Update Academic Profile - Invalid Token")
    
    response = requests.put(
        f"{BASE_URL}/api/academic",
        json=UPDATED_ACADEMIC_PROFILE,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer invalid_token_here"
        }
    )
    
    # Should return 401 (Unauthorized) with invalid token
    success = response.status_code == 401
    
    print_result(success, "Request with invalid token rejected correctly", response)
    return success

def test_update_academic_profile_success(auth_data: Dict[str, Any]):
    """Test successful update of academic profile."""
    print_test_header("Update Academic Profile - Success Case")
    
    access_token = auth_data.get("access_token")
    
    response = requests.put(
        f"{BASE_URL}/api/academic",
        json=UPDATED_ACADEMIC_PROFILE,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
    )
    
    success = (
        response.status_code == 200 and
        "grade" in response.json() and
        "semester_type" in response.json() and
        "semester" in response.json() and
        "subject" in response.json() and
        response.json()["grade"] == UPDATED_ACADEMIC_PROFILE["grade"] and
        response.json()["semester_type"] == UPDATED_ACADEMIC_PROFILE["semester_type"] and
        response.json()["semester"] == UPDATED_ACADEMIC_PROFILE["semester"] and
        response.json()["subject"] == UPDATED_ACADEMIC_PROFILE["subject"]
    )
    
    print_result(success, "Academic profile updated successfully", response)
    return success

def test_get_updated_academic_profile(auth_data: Dict[str, Any]):
    """Test retrieving academic profile after update to verify changes persisted."""
    print_test_header("Get Academic Profile - Verify Update Persisted")
    
    access_token = auth_data.get("access_token")
    
    response = requests.get(
        f"{BASE_URL}/api/academic",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    success = (
        response.status_code == 200 and
        response.json()["grade"] == UPDATED_ACADEMIC_PROFILE["grade"] and
        response.json()["semester_type"] == UPDATED_ACADEMIC_PROFILE["semester_type"] and
        response.json()["semester"] == UPDATED_ACADEMIC_PROFILE["semester"] and
        response.json()["subject"] == UPDATED_ACADEMIC_PROFILE["subject"]
    )
    
    print_result(success, "Updated profile retrieved correctly", response)
    return success

def run_all_tests():
    """Run all academic profile endpoint tests."""
    print("\n" + "=" * 70)
    print("ACADEMIC PROFILE ENDPOINTS TEST SUITE")
    print("=" * 70)
    print(f"Testing against: {BASE_URL}")
    print(f"Test email: {TEST_EMAIL}")
    print("=" * 70)
    
    results = []
    
    # Setup: Create test user
    auth_data = create_test_user()
    
    if not auth_data:
        print("\n✗ CRITICAL: Failed to create test user. Cannot continue with tests.")
        return
    
    # Test 1: Create without authentication
    results.append(("Create - No Auth", test_create_academic_profile_without_auth()))
    
    # Test 2: Create with invalid token
    results.append(("Create - Invalid Token", test_create_academic_profile_with_invalid_token()))
    
    # Test 3: Create success
    profile_data = test_create_academic_profile_success(auth_data)
    results.append(("Create - Success", profile_data is not None))
    
    if not profile_data:
        print("\n✗ CRITICAL: Failed to create academic profile. Cannot continue with other tests.")
        return
    
    # Test 4: Create duplicate (conflict)
    results.append(("Create - Duplicate (409)", test_create_academic_profile_duplicate(auth_data)))
    
    # Test 5: Get without authentication
    results.append(("Get - No Auth", test_get_academic_profile_without_auth()))
    
    # Test 6: Get with invalid token
    results.append(("Get - Invalid Token", test_get_academic_profile_with_invalid_token()))
    
    # Test 7: Get success
    results.append(("Get - Success", test_get_academic_profile_success(auth_data)))
    
    # Test 8: Update without authentication
    results.append(("Update - No Auth", test_update_academic_profile_without_auth()))
    
    # Test 9: Update with invalid token
    results.append(("Update - Invalid Token", test_update_academic_profile_with_invalid_token()))
    
    # Test 10: Update success
    results.append(("Update - Success", test_update_academic_profile_success(auth_data)))
    
    # Test 11: Get updated profile to verify persistence
    results.append(("Get - Verify Update", test_get_updated_academic_profile(auth_data)))
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print("=" * 70)
    print(f"Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("=" * 70)
    
    if passed == total:
        print("\n🎉 All tests passed! Academic profile endpoints are working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the failures above.")

if __name__ == "__main__":
    try:
        run_all_tests()
    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Could not connect to the backend server.")
        print(f"Please ensure the server is running at {BASE_URL}")
    except Exception as e:
        print(f"\n✗ ERROR: An unexpected error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
