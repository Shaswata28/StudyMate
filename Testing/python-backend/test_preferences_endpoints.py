"""
Test script to verify preferences endpoints are working correctly.

This script tests:
- POST /api/preferences - Create user preferences
- GET /api/preferences - Retrieve user preferences
- PUT /api/preferences - Update user preferences
- Authentication requirement (401 without token)
- Conflict handling (409 for duplicate creation)
- JSONB storage of preferences

Requirements: 9.2, 9.3, 9.4
"""
import requests
import json
import time
from typing import Dict, Any, Optional

BASE_URL = "http://localhost:8000"

# Test user credentials
TEST_EMAIL = f"test_preferences_{int(time.time())}@example.com"
TEST_PASSWORD = "SecurePassword123!"

# Test preferences data
TEST_PREFERENCES = {
    "detail_level": 0.7,
    "example_preference": 0.8,
    "analogy_preference": 0.6,
    "technical_language": 0.5,
    "structure_preference": 0.9,
    "visual_preference": 0.4,
    "learning_pace": "moderate",
    "prior_experience": "intermediate"
}

UPDATED_PREFERENCES = {
    "detail_level": 0.9,
    "example_preference": 0.5,
    "analogy_preference": 0.8,
    "technical_language": 0.7,
    "structure_preference": 0.6,
    "visual_preference": 0.8,
    "learning_pace": "fast",
    "prior_experience": "advanced"
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
    """Create a test user for preferences testing."""
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

def test_create_preferences_without_auth():
    """Test creating preferences without authentication token."""
    print_test_header("Create Preferences - No Authentication")
    
    response = requests.post(
        f"{BASE_URL}/api/preferences",
        json=TEST_PREFERENCES,
        headers={"Content-Type": "application/json"}
    )
    
    # Should return 403 (Forbidden) or 401 (Unauthorized) without token
    success = response.status_code in [401, 403]
    
    print_result(success, "Request without authentication rejected correctly", response)
    return success

def test_create_preferences_with_invalid_token():
    """Test creating preferences with invalid authentication token."""
    print_test_header("Create Preferences - Invalid Token")
    
    response = requests.post(
        f"{BASE_URL}/api/preferences",
        json=TEST_PREFERENCES,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer invalid_token_here"
        }
    )
    
    # Should return 401 (Unauthorized) with invalid token
    success = response.status_code == 401
    
    print_result(success, "Request with invalid token rejected correctly", response)
    return success

def test_create_preferences_success(auth_data: Dict[str, Any]):
    """Test successful creation of preferences."""
    print_test_header("Create Preferences - Success Case")
    
    access_token = auth_data.get("access_token")
    
    response = requests.post(
        f"{BASE_URL}/api/preferences",
        json=TEST_PREFERENCES,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
    )
    
    # Check that response contains the preferences data
    # The backend stores preferences in a 'prefs' JSONB field
    success = response.status_code == 201
    
    if success and response.json():
        data = response.json()
        # Check if prefs field exists and contains our data
        if "prefs" in data:
            prefs = data["prefs"]
            success = (
                prefs.get("detail_level") == TEST_PREFERENCES["detail_level"] and
                prefs.get("learning_pace") == TEST_PREFERENCES["learning_pace"] and
                prefs.get("prior_experience") == TEST_PREFERENCES["prior_experience"]
            )
    
    print_result(success, "Preferences created successfully", response)
    
    if success:
        return response.json()
    return None

def test_create_preferences_duplicate(auth_data: Dict[str, Any]):
    """Test creating preferences when they already exist (conflict)."""
    print_test_header("Create Preferences - Duplicate (Conflict)")
    
    access_token = auth_data.get("access_token")
    
    response = requests.post(
        f"{BASE_URL}/api/preferences",
        json=TEST_PREFERENCES,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
    )
    
    # Should return 409 (Conflict) when preferences already exist
    success = (
        response.status_code == 409 and
        "already exist" in response.json().get("detail", "").lower()
    )
    
    print_result(success, "Duplicate preferences creation rejected correctly", response)
    return success

def test_get_preferences_without_auth():
    """Test retrieving preferences without authentication token."""
    print_test_header("Get Preferences - No Authentication")
    
    response = requests.get(f"{BASE_URL}/api/preferences")
    
    # Should return 403 (Forbidden) or 401 (Unauthorized) without token
    success = response.status_code in [401, 403]
    
    print_result(success, "Request without authentication rejected correctly", response)
    return success

def test_get_preferences_with_invalid_token():
    """Test retrieving preferences with invalid authentication token."""
    print_test_header("Get Preferences - Invalid Token")
    
    response = requests.get(
        f"{BASE_URL}/api/preferences",
        headers={"Authorization": "Bearer invalid_token_here"}
    )
    
    # Should return 401 (Unauthorized) with invalid token
    success = response.status_code == 401
    
    print_result(success, "Request with invalid token rejected correctly", response)
    return success

def test_get_preferences_success(auth_data: Dict[str, Any]):
    """Test successful retrieval of preferences."""
    print_test_header("Get Preferences - Success Case")
    
    access_token = auth_data.get("access_token")
    
    response = requests.get(
        f"{BASE_URL}/api/preferences",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    success = response.status_code == 200
    
    if success and response.json():
        data = response.json()
        # Check if prefs field exists and contains our data
        if "prefs" in data:
            prefs = data["prefs"]
            success = (
                prefs.get("detail_level") == TEST_PREFERENCES["detail_level"] and
                prefs.get("learning_pace") == TEST_PREFERENCES["learning_pace"] and
                prefs.get("prior_experience") == TEST_PREFERENCES["prior_experience"]
            )
    
    print_result(success, "Preferences retrieved successfully", response)
    return success

def test_update_preferences_without_auth():
    """Test updating preferences without authentication token."""
    print_test_header("Update Preferences - No Authentication")
    
    response = requests.put(
        f"{BASE_URL}/api/preferences",
        json=UPDATED_PREFERENCES,
        headers={"Content-Type": "application/json"}
    )
    
    # Should return 403 (Forbidden) or 401 (Unauthorized) without token
    success = response.status_code in [401, 403]
    
    print_result(success, "Request without authentication rejected correctly", response)
    return success

def test_update_preferences_with_invalid_token():
    """Test updating preferences with invalid authentication token."""
    print_test_header("Update Preferences - Invalid Token")
    
    response = requests.put(
        f"{BASE_URL}/api/preferences",
        json=UPDATED_PREFERENCES,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer invalid_token_here"
        }
    )
    
    # Should return 401 (Unauthorized) with invalid token
    success = response.status_code == 401
    
    print_result(success, "Request with invalid token rejected correctly", response)
    return success

def test_update_preferences_success(auth_data: Dict[str, Any]):
    """Test successful update of preferences."""
    print_test_header("Update Preferences - Success Case")
    
    access_token = auth_data.get("access_token")
    
    response = requests.put(
        f"{BASE_URL}/api/preferences",
        json=UPDATED_PREFERENCES,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
    )
    
    success = response.status_code == 200
    
    if success and response.json():
        data = response.json()
        # Check if prefs field exists and contains updated data
        if "prefs" in data:
            prefs = data["prefs"]
            success = (
                prefs.get("detail_level") == UPDATED_PREFERENCES["detail_level"] and
                prefs.get("learning_pace") == UPDATED_PREFERENCES["learning_pace"] and
                prefs.get("prior_experience") == UPDATED_PREFERENCES["prior_experience"]
            )
    
    print_result(success, "Preferences updated successfully", response)
    return success

def test_get_updated_preferences(auth_data: Dict[str, Any]):
    """Test retrieving preferences after update to verify changes persisted."""
    print_test_header("Get Preferences - Verify Update Persisted")
    
    access_token = auth_data.get("access_token")
    
    response = requests.get(
        f"{BASE_URL}/api/preferences",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    success = response.status_code == 200
    
    if success and response.json():
        data = response.json()
        # Check if prefs field exists and contains updated data
        if "prefs" in data:
            prefs = data["prefs"]
            success = (
                prefs.get("detail_level") == UPDATED_PREFERENCES["detail_level"] and
                prefs.get("learning_pace") == UPDATED_PREFERENCES["learning_pace"] and
                prefs.get("prior_experience") == UPDATED_PREFERENCES["prior_experience"]
            )
    
    print_result(success, "Updated preferences retrieved correctly", response)
    return success

def test_jsonb_storage_flexibility(auth_data: Dict[str, Any]):
    """Test that JSONB storage allows flexible preference structure."""
    print_test_header("JSONB Storage - Flexibility Test")
    
    access_token = auth_data.get("access_token")
    
    # Get current preferences
    response = requests.get(
        f"{BASE_URL}/api/preferences",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    success = False
    if response.status_code == 200:
        data = response.json()
        # Verify that all preference fields are stored in JSONB
        if "prefs" in data:
            prefs = data["prefs"]
            # Check that all expected fields are present
            expected_fields = [
                "detail_level", "example_preference", "analogy_preference",
                "technical_language", "structure_preference", "visual_preference",
                "learning_pace", "prior_experience"
            ]
            success = all(field in prefs for field in expected_fields)
    
    print_result(success, "JSONB storage contains all preference fields", response)
    return success

def run_all_tests():
    """Run all preferences endpoint tests."""
    print("\n" + "=" * 70)
    print("PREFERENCES ENDPOINTS TEST SUITE")
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
    results.append(("Create - No Auth", test_create_preferences_without_auth()))
    
    # Test 2: Create with invalid token
    results.append(("Create - Invalid Token", test_create_preferences_with_invalid_token()))
    
    # Test 3: Create success
    prefs_data = test_create_preferences_success(auth_data)
    results.append(("Create - Success", prefs_data is not None))
    
    if not prefs_data:
        print("\n✗ CRITICAL: Failed to create preferences. Cannot continue with other tests.")
        return
    
    # Test 4: Create duplicate (conflict)
    results.append(("Create - Duplicate (409)", test_create_preferences_duplicate(auth_data)))
    
    # Test 5: Get without authentication
    results.append(("Get - No Auth", test_get_preferences_without_auth()))
    
    # Test 6: Get with invalid token
    results.append(("Get - Invalid Token", test_get_preferences_with_invalid_token()))
    
    # Test 7: Get success
    results.append(("Get - Success", test_get_preferences_success(auth_data)))
    
    # Test 8: JSONB storage flexibility
    results.append(("JSONB Storage - Flexibility", test_jsonb_storage_flexibility(auth_data)))
    
    # Test 9: Update without authentication
    results.append(("Update - No Auth", test_update_preferences_without_auth()))
    
    # Test 10: Update with invalid token
    results.append(("Update - Invalid Token", test_update_preferences_with_invalid_token()))
    
    # Test 11: Update success
    results.append(("Update - Success", test_update_preferences_success(auth_data)))
    
    # Test 12: Get updated preferences to verify persistence
    results.append(("Get - Verify Update", test_get_updated_preferences(auth_data)))
    
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
        print("\n🎉 All tests passed! Preferences endpoints are working correctly.")
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
