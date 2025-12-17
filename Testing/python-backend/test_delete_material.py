"""
Test script to verify the DELETE /api/materials/{material_id} endpoint
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_BASE_URL = "http://localhost:8000"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

def test_delete_endpoint():
    """Test the delete material endpoint"""
    
    print("=" * 60)
    print("Testing DELETE /api/materials/{material_id} endpoint")
    print("=" * 60)
    
    # You need to provide:
    # 1. A valid access token
    # 2. A valid material ID that exists in your database
    
    access_token = input("Enter your access token: ").strip()
    material_id = input("Enter a material ID to delete: ").strip()
    
    if not access_token or not material_id:
        print("❌ Access token and material ID are required")
        return
    
    # Test DELETE request
    print(f"\n📤 Sending DELETE request to: {API_BASE_URL}/api/materials/{material_id}")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.delete(
            f"{API_BASE_URL}/api/materials/{material_id}",
            headers=headers
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        print(f"📥 Response Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"📥 Response Body: {response_data}")
        except:
            print(f"📥 Response Body (text): {response.text}")
        
        if response.status_code == 200:
            print("\n✅ DELETE request successful!")
        else:
            print(f"\n❌ DELETE request failed with status {response.status_code}")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    test_delete_endpoint()
