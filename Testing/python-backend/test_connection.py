"""
Quick test script to verify Supabase database connection.
Run this to check if your Supabase credentials are working.
"""
import sys
import logging
from services.supabase_client import supabase_admin, get_anon_client
from config import config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_connection():
    """Test Supabase connection and basic operations."""
    
    print("\n" + "="*60)
    print("🔍 SUPABASE CONNECTION TEST")
    print("="*60 + "\n")
    
    # Test 1: Configuration
    print("✓ Configuration loaded successfully")
    print(f"  - Supabase URL: {config.SUPABASE_URL}")
    print(f"  - Anon Key: {config.SUPABASE_ANON_KEY[:20]}...")
    print(f"  - Service Role Key: {config.SUPABASE_SERVICE_ROLE_KEY[:20]}...")
    print()
    
    # Test 2: Admin client initialization
    try:
        print("Testing admin client connection...")
        # Try a simple query to verify connection
        result = supabase_admin.table("academic").select("count", count="exact").limit(0).execute()
        print(f"✓ Admin client connected successfully")
        print(f"  - Academic table exists")
        print()
    except Exception as e:
        print(f"✗ Admin client connection failed: {str(e)}")
        print()
        return False
    
    # Test 3: Anonymous client
    try:
        print("Testing anonymous client...")
        anon_client = get_anon_client()
        print("✓ Anonymous client created successfully")
        print()
    except Exception as e:
        print(f"✗ Anonymous client creation failed: {str(e)}")
        print()
        return False
    
    # Test 4: Check tables exist
    print("Checking database tables...")
    tables_to_check = ["academic", "personalized", "courses", "materials", "chat_history"]
    
    for table in tables_to_check:
        try:
            result = supabase_admin.table(table).select("count", count="exact").limit(0).execute()
            print(f"  ✓ Table '{table}' exists")
        except Exception as e:
            print(f"  ✗ Table '{table}' not found or error: {str(e)}")
    
    print()
    print("="*60)
    print("✅ CONNECTION TEST COMPLETE")
    print("="*60)
    print()
    
    return True

if __name__ == "__main__":
    try:
        success = test_connection()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        sys.exit(1)
