"""
Test script to verify all authentication endpoints are working correctly.

This script tests:
- POST /api/auth/signup - User registration
- POST /api/auth/login - User login
- POST /api/auth/logout - User logout
- GET /api/auth/session - Get current session
- POST /api/auth/refresh - Refresh access token
- Error handling for duplicate emails, invalid credentials, and missing fields
"""
import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

# Test user credentials
TEST_EMAIL = f"test_user_{int(time.time())}@example.com"
TEST_PASSWORD = "SecurePassword123!"
INVALID_PASSWORD = "wrongpassword"

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
    print()

def test_signup_success():
    """Test successful user signup."""
    print_test_header("Signup - Success Case")
    
    response = requests.post(
        f"{BASE_URL}/api/auth/signup",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        headers={"Content-Type": "application/json"}
    )
    
    success = (
        response.status_code == 201 and
        "access_token" in response.json() and
        "refresh_token" in response.json() and
        "user" in response.json()
    )
    
    print_result(success, "User signup successful", response)
    
    if success:
        return response.json()
    return None

def test_signup_duplicate_email():
    """Test signup with duplicate email."""
    print_test_header("Signup - Duplicate Email")
    
    response = requests.post(
        f"{BASE_URL}/api/auth/signup",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        headers={"Content-Type": "application/json"}
    )
    
    success = (
        response.status_code == 400 and
        "already exists" in response.json().get("detail", "").lower()
    )
    
    print_result(success, "Duplicate email rejected correctly", response)
    return success

def test_signup_missing_fields():
    """Test signup with missing required fields."""
    print_test_header("Signup - Missing Fields")
    
    # Test missing email
    response1 = requests.post(
        f"{BASE_URL}/api/auth/signup",
        json={"password": TEST_PASSWORD},
        headers={"Content-Type": "application/json"}
    )
    
    success1 = response1.status_code == 422  # Validation error
    print_result(success1, "Missing email field rejected", response1)
    
    # Test missing password
    response2 = requests.post(
        f"{BASE_URL}/api/auth/signup",
        json={"email": TEST_EMAIL},
        headers={"Content-Type": "application/json"}
    )
    
    success2 = response2.status_code == 422  # Validation error
    print_result(success2, "Missing password field rejected", response2)
    
    return success1 and success2

def test_login_success(auth_data: Dict[str, Any]):
    """Test successful user login."""
    print_test_header("Login - Success Case")
    
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        headers={"Content-Type": "application/json"}
    )
    
    success = (
        response.status_code == 200 and
        "access_token" in response.json() and
        "refresh_token" in response.json() and
        "user" in response.json()
    )
    
    print_result(success, "User login successful", response)
    
    if success:
        return response.json()
    return None

def test_login_invalid_credentials():
    """Test login with invalid credentials."""
    print_test_header("Login - Invalid Credentials")
    
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": INVALID_PASSWORD},
        headers={"Content-Type": "application/json"}
    )
    
    success = (
        response.status_code == 401 and
        "invalid" in response.json().get("detail", "").lower()
    )
    
    print_result(success, "Invalid credentials rejected correctly", response)
    return success

def test_session_with_valid_token(auth_data: Dict[str, Any]):
    """Test getting session with valid token."""
    print_test_header("Session - Valid Token")
    
    access_token = auth_data.get("access_token")
    
    response = requests.get(
        f"{BASE_URL}/api/auth/session",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    success = (
        response.status_code == 200 and
        "user" in response.json() and
        "session" in response.json()
    )
    
    print_result(success, "Session retrieved successfully", response)
    return success

def test_session_without_token():
    """Test getting session without token."""
    print_test_header("Session - No Token")
    
    response = requests.get(f"{BASE_URL}/api/auth/session")
    
    success = response.status_code == 403  # Forbidden without auth
    
    print_result(success, "Session request without token rejected", response)
    return success

def test_session_with_invalid_token():
    """Test getting session with invalid token."""
    print_test_header("Session - Invalid Token")
    
    response = requests.get(
        f"{BASE_URL}/api/auth/session",
        headers={"Authorization": "Bearer invalid_token_here"}
    )
    
    success = response.status_code == 401  # Unauthorized
    
    print_result(success, "Session request with invalid token rejected", response)
    return success

def test_refresh_token_success(auth_data: Dict[str, Any]):
    """Test refreshing access token."""
    print_test_header("Refresh Token - Success Case")
    
    refresh_token = auth_data.get("refresh_token")
    
    response = requests.post(
        f"{BASE_URL}/api/auth/refresh",
        json={"refresh_token": refresh_token},
        headers={"Content-Type": "application/json"}
    )
    
    success = (
        response.status_code == 200 and
        "access_token" in response.json() and
        "refresh_token" in response.json()
    )
    
    print_result(success, "Token refresh successful", response)
    
    if success:
        return response.json()
    return None

def test_refresh_token_invalid():
    """Test refreshing with invalid token."""
    print_test_header("Refresh Token - Invalid Token")
    
    response = requests.post(
        f"{BASE_URL}/api/auth/refresh",
        json={"refresh_token": "invalid_refresh_token"},
        headers={"Content-Type": "application/json"}
    )
    
    success = response.status_code == 401
    
    print_result(success, "Invalid refresh token rejected", response)
    return success

def test_logout_success(auth_data: Dict[str, Any]):
    """Test user logout."""
    print_test_header("Logout - Success Case")
    
    access_token = auth_data.get("access_token")
    
    response = requests.post(
        f"{BASE_URL}/api/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    success = (
        response.status_code == 200 and
        "message" in response.json()
    )
    
    print_result(success, "User logout successful", response)
    return success

def test_logout_without_token():
    """Test logout without token."""
    print_test_header("Logout - No Token")
    
    response = requests.post(f"{BASE_URL}/api/auth/logout")
    
    success = response.status_code == 403  # Forbidden without auth
    
    print_result(success, "Logout without token rejected", response)
    return success

def run_all_tests():
    """Run all authentication endpoint tests."""
    print("\n" + "=" * 70)
    print("AUTHENTICATION ENDPOINTS TEST SUITE")
    print("=" * 70)
    print(f"Testing against: {BASE_URL}")
    print(f"Test email: {TEST_EMAIL}")
    print("=" * 70)
    
    results = []
    
    # Test 1: Signup success
    auth_data = test_signup_success()
    results.append(("Signup - Success", auth_data is not None))
    
    if not auth_data:
        print("\n✗ CRITICAL: Signup failed. Cannot continue with other tests.")
        return
    
    # Test 2: Duplicate email
    results.append(("Signup - Duplicate Email", test_signup_duplicate_email()))
    
    # Test 3: Missing fields
    results.append(("Signup - Missing Fields", test_signup_missing_fields()))
    
    # Test 4: Login success
    login_data = test_login_success(auth_data)
    results.append(("Login - Success", login_data is not None))
    
    if not login_data:
        print("\n✗ WARNING: Login failed. Using signup tokens for remaining tests.")
        login_data = auth_data
    
    # Test 5: Invalid credentials
    results.append(("Login - Invalid Credentials", test_login_invalid_credentials()))
    
    # Test 6: Session with valid token
    results.append(("Session - Valid Token", test_session_with_valid_token(login_data)))
    
    # Test 7: Session without token
    results.append(("Session - No Token", test_session_without_token()))
    
    # Test 8: Session with invalid token
    results.append(("Session - Invalid Token", test_session_with_invalid_token()))
    
    # Test 9: Refresh token success
    refreshed_data = test_refresh_token_success(login_data)
    results.append(("Refresh Token - Success", refreshed_data is not None))
    
    # Test 10: Invalid refresh token
    results.append(("Refresh Token - Invalid", test_refresh_token_invalid()))
    
    # Test 11: Logout success (use refreshed token if available)
    logout_data = refreshed_data if refreshed_data else login_data
    results.append(("Logout - Success", test_logout_success(logout_data)))
    
    # Test 12: Logout without token
    results.append(("Logout - No Token", test_logout_without_token()))
    
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
        print("\n🎉 All tests passed! Authentication endpoints are working correctly.")
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
