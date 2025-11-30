#!/usr/bin/env python3
"""
Quick Database Setup Script

This script helps you set up your Supabase database by:
1. Checking if all required environment variables are set
2. Testing the database connection
3. Running migrations

Usage:
    python setup_database.py
"""
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")

def print_step(number, text):
    """Print a step number and description."""
    print(f"\n{'─' * 70}")
    print(f"Step {number}: {text}")
    print('─' * 70)

def check_env_variables():
    """Check if all required environment variables are set."""
    print_step(1, "Checking Environment Variables")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = {
        'SUPABASE_URL': 'Your Supabase project URL',
        'SUPABASE_ANON_KEY': 'Your Supabase anonymous key',
        'SUPABASE_SERVICE_ROLE_KEY': 'Your Supabase service role key',
        'SUPABASE_DB_PASSWORD': 'Your database password (for migrations)',
    }
    
    missing = []
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'KEY' in var or 'PASSWORD' in var:
                display_value = value[:10] + '...' if len(value) > 10 else '***'
            else:
                display_value = value
            print(f"  ✓ {var}: {display_value}")
        else:
            print(f"  ✗ {var}: NOT SET")
            missing.append((var, description))
    
    if missing:
        print("\n❌ Missing environment variables:")
        for var, description in missing:
            print(f"  - {var}: {description}")
        
        if 'SUPABASE_DB_PASSWORD' in [v for v, _ in missing]:
            print("\n📖 To get your database password:")
            print("  1. Go to https://supabase.com/dashboard")
            print("  2. Select your project")
            print("  3. Go to Settings → Database")
            print("  4. Find 'Connection string' section")
            print("  5. Copy the password from the connection string")
            print("  6. Add to .env: SUPABASE_DB_PASSWORD=your_password")
        
        return False
    
    print("\n✅ All environment variables are set!")
    return True

def test_database_connection():
    """Test connection to Supabase database."""
    print_step(2, "Testing Database Connection")
    
    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2-binary is not installed")
        print("\nInstall it with:")
        print("  pip install psycopg2-binary")
        return False
    
    from config import config
    from urllib.parse import urlparse
    
    # Parse project reference from URL
    parsed = urlparse(config.SUPABASE_URL)
    project_ref = parsed.hostname.split('.')[0] if parsed.hostname else None
    
    if not project_ref:
        print("❌ Could not extract project reference from SUPABASE_URL")
        return False
    
    db_password = os.getenv("SUPABASE_DB_PASSWORD")
    if not db_password:
        print("❌ SUPABASE_DB_PASSWORD not set")
        return False
    
    # Construct connection string
    conn_string = f"postgresql://postgres:{db_password}@db.{project_ref}.supabase.co:5432/postgres"
    
    try:
        print(f"  Connecting to: db.{project_ref}.supabase.co...")
        conn = psycopg2.connect(conn_string)
        
        # Test query
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        print(f"  ✓ Connection successful!")
        print(f"  Database: PostgreSQL {version.split()[1]}")
        return True
        
    except psycopg2.Error as e:
        print(f"  ❌ Connection failed: {e}")
        print("\n  Possible issues:")
        print("  - Wrong database password")
        print("  - Network/firewall blocking port 5432")
        print("  - Incorrect SUPABASE_URL")
        return False

def check_existing_tables():
    """Check if tables already exist."""
    print_step(3, "Checking Existing Tables")
    
    try:
        import psycopg2
        from config import config
        from urllib.parse import urlparse
        
        parsed = urlparse(config.SUPABASE_URL)
        project_ref = parsed.hostname.split('.')[0]
        db_password = os.getenv("SUPABASE_DB_PASSWORD")
        
        conn_string = f"postgresql://postgres:{db_password}@db.{project_ref}.supabase.co:5432/postgres"
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()
        
        # Check for our tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('academic', 'personalized', 'courses', 'materials', 'chat_history')
            ORDER BY table_name;
        """)
        
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        if existing_tables:
            print(f"  Found {len(existing_tables)} existing tables:")
            for table in existing_tables:
                print(f"    - {table}")
            print("\n  ⚠️  Tables already exist. Migrations may fail if run again.")
            print("  Options:")
            print("    1. Skip migrations (tables are already set up)")
            print("    2. Run rollback first: python scripts/run_migrations.py --rollback")
            return True
        else:
            print("  No tables found. Ready to run migrations.")
            return False
            
    except Exception as e:
        print(f"  ⚠️  Could not check tables: {e}")
        return False

def run_migrations():
    """Run database migrations."""
    print_step(4, "Running Migrations")
    
    print("  Starting migration process...")
    print("  This will create all database tables and policies.\n")
    
    # Import and run migrations
    from scripts.run_migrations import run_forward_migrations
    
    success = run_forward_migrations()
    
    if success:
        print("\n✅ Migrations completed successfully!")
        return True
    else:
        print("\n❌ Migrations failed. Check the error messages above.")
        return False

def main():
    """Main setup flow."""
    print_header("Supabase Database Setup")
    
    print("This script will help you set up your Supabase database.")
    print("It will check your configuration and run migrations.")
    
    # Step 1: Check environment variables
    if not check_env_variables():
        print("\n❌ Setup cannot continue. Please fix the issues above.")
        sys.exit(1)
    
    # Step 2: Test database connection
    if not test_database_connection():
        print("\n❌ Setup cannot continue. Please fix the connection issues.")
        sys.exit(1)
    
    # Step 3: Check existing tables
    tables_exist = check_existing_tables()
    
    if tables_exist:
        response = input("\n  Do you want to continue anyway? (y/N): ").strip().lower()
        if response != 'y':
            print("\n  Setup cancelled. Your existing tables are unchanged.")
            sys.exit(0)
    
    # Step 4: Run migrations
    print("\n  Ready to run migrations.")
    response = input("  Continue? (Y/n): ").strip().lower()
    
    if response == 'n':
        print("\n  Setup cancelled.")
        sys.exit(0)
    
    if run_migrations():
        print_header("Setup Complete! 🎉")
        print("Your Supabase database is ready to use.")
        print("\nNext steps:")
        print("  1. Start the backend: python main.py")
        print("  2. Test signup: curl -X POST http://localhost:8000/api/auth/signup \\")
        print("                       -H 'Content-Type: application/json' \\")
        print("                       -d '{\"email\":\"test@example.com\",\"password\":\"password123\"}'")
        print("\nFor more information, see MIGRATION_GUIDE.md")
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        print("For help, see MIGRATION_GUIDE.md")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
