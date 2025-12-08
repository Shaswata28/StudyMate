"""
Test script for registration flow.
Tests the complete user registration and academic profile creation.
"""
import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
TEST_EMAIL = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
TEST_PASSWORD = "TestPassword123"

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_health_check():
    """Test if the backend is running."""
    print_section("1. Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✓ Backend is running")
            print(f"  Response: {response.json()}")
            return True
        else:
            print(f"✗ Backend returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to backend")
        print(f"  Make sure the backend is running on {BASE_URL}")
        return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def test_signup():
    """Test user registration."""
    print_section("2. User Registration")
    print(f"  Email: {TEST_EMAIL}")
    print(f"  Password: {TEST_PASSWORD}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/signup",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            },
            timeout=10
        )
        
        if response.status_code == 201:
            print("✓ User registered successfully")
            data = response.json()
            print(f"  User ID: {data['user']['id']}")
            print(f"  Email: {data['user']['email']}")
            print(f"  Access Token: {data['access_token'][:20]}...")
            return data['access_token'], data['user']['id']
        else:
            print(f"✗ Registration failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return None, None
            
    except Exception as e:
        print(f"✗ Error during registration: {str(e)}")
        return None, None

def test_academic_profile(access_token, user_id):
    """Test academic profile creation."""
    print_section("3. Academic Profile Creation")
    
    if not access_token:
        print("✗ Skipping - no access token available")
        return False
    
    academic_data = {
        "grade": ["Bachelor"],
        "semester_type": "double",
        "semester": 1,
        "subject": ["computer science"]
    }
    
    print(f"  Grade: {academic_data['grade']}")
    print(f"  Semester Type: {academic_data['semester_type']}")
    print(f"  Semester: {academic_data['semester']}")
    print(f"  Subject: {academic_data['subject']}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/academic",
            json=academic_data,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        
        if response.status_code == 201:
            print("✓ Academic profile created successfully")
            data = response.json()
            print(f"  Profile ID: {data['id']}")
            print(f"  Grade: {data['grade']}")
            print(f"  Semester: {data['semester']}")
            return True
        else:
            print(f"✗ Profile creation failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Error during profile creation: {str(e)}")
        return False

def test_get_academic_profile(access_token):
    """Test retrieving academic profile."""
    print_section("4. Retrieve Academic Profile")
    
    if not access_token:
        print("✗ Skipping - no access token available")
        return False
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/academic",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✓ Academic profile retrieved successfully")
            data = response.json()
            print(f"  Grade: {data['grade']}")
            print(f"  Semester Type: {data['semester_type']}")
            print(f"  Semester: {data['semester']}")
            print(f"  Subject: {data['subject']}")
            return True
        else:
            print(f"✗ Profile retrieval failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Error during profile retrieval: {str(e)}")
        return False

def test_login():
    """Test user login."""
    print_section("5. User Login")
    print(f"  Email: {TEST_EMAIL}")
    print(f"  Password: {TEST_PASSWORD}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            },
            timeout=10
        )
        
        if response.status_code == 200:
            print("✓ User logged in successfully")
            data = response.json()
            print(f"  User ID: {data['user']['id']}")
            print(f"  Email: {data['user']['email']}")
            print(f"  Access Token: {data['access_token'][:20]}...")
            return True
        else:
            print(f"✗ Login failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Error during login: {str(e)}")
        return False

def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("  REGISTRATION FLOW TEST")
    print("=" * 60)
    print(f"  Backend URL: {BASE_URL}")
    print(f"  Test Email: {TEST_EMAIL}")
    print("=" * 60)
    
    # Test 1: Health check
    if not test_health_check():
        print("\n✗ Backend is not running. Please start it first:")
        print("  cd python-backend")
        print("  python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        sys.exit(1)
    
    # Test 2: User registration
    access_token, user_id = test_signup()
    if not access_token:
        print("\n✗ Registration failed. Cannot continue with remaining tests.")
        sys.exit(1)
    
    # Test 3: Academic profile creation
    if not test_academic_profile(access_token, user_id):
        print("\n✗ Academic profile creation failed.")
        sys.exit(1)
    
    # Test 4: Retrieve academic profile
    if not test_get_academic_profile(access_token):
        print("\n✗ Academic profile retrieval failed.")
        sys.exit(1)
    
    # Test 5: Login
    if not test_login():
        print("\n✗ Login failed.")
        sys.exit(1)
    
    # Summary
    print_section("TEST SUMMARY")
    print("✓ All tests passed successfully!")
    print("\nThe registration flow is working correctly:")
    print("  1. Backend health check - OK")
    print("  2. User registration - OK")
    print("  3. Academic profile creation - OK")
    print("  4. Academic profile retrieval - OK")
    print("  5. User login - OK")
    print("\nYou can now test the frontend at http://localhost:8080/signup")
    print("=" * 60)

if __name__ == "__main__":
    main()
