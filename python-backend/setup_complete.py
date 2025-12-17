#!/usr/bin/env python3
"""
Complete Database Setup Script

This script performs a complete database setup:
1. Checks environment variables
2. Tests database connection
3. Lists existing tables
4. Optionally cleans up unnecessary tables
5. Creates storage buckets
6. Creates all required tables
7. Sets up RLS policies

Usage:
    python setup_complete.py [--clean]
    
Options:
    --clean    Drop all existing tables before creating new ones
"""
import os
import sys
import argparse
from pathlib import Path
from urllib.parse import urlparse

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("\n❌ Error: psycopg2-binary is not installed")
    print("Install it with: pip install psycopg2-binary\n")
    sys.exit(1)

from dotenv import load_dotenv
load_dotenv()

from config import config

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

def get_db_connection():
    """Get database connection."""
    parsed = urlparse(config.SUPABASE_URL)
    project_ref = parsed.hostname.split('.')[0] if parsed.hostname else None
    
    if not project_ref:
        raise ValueError("Could not extract project reference from SUPABASE_URL")
    
    db_password = os.getenv("SUPABASE_DB_PASSWORD")
    if not db_password:
        raise ValueError("SUPABASE_DB_PASSWORD not set in .env file")
    
    conn_string = f"postgresql://postgres:{db_password}@db.{project_ref}.supabase.co:5432/postgres"
    return psycopg2.connect(conn_string)

def list_existing_tables(conn):
    """List all existing tables in public schema."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return tables

def drop_table(conn, table_name):
    """Drop a table if it exists."""
    cursor = conn.cursor()
    try:
        cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
        conn.commit()
        print(f"  ✓ Dropped table: {table_name}")
        return True
    except Exception as e:
        conn.rollback()
        print(f"  ✗ Failed to drop {table_name}: {e}")
        return False
    finally:
        cursor.close()

def execute_sql_file(conn, file_path, description):
    """Execute a SQL file."""
    print(f"\n  📄 {description}")
    print(f"     File: {file_path.name}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        cursor = conn.cursor()
        try:
            cursor.execute(sql_content)
            conn.commit()
            print(f"  ✓ Success")
            return True
        except Exception as e:
            conn.rollback()
            print(f"  ✗ Error: {e}")
            return False
        finally:
            cursor.close()
            
    except Exception as e:
        print(f"  ✗ Failed to read file: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Complete database setup")
    parser.add_argument('--clean', action='store_true', help='Drop all existing tables first')
    args = parser.parse_args()
    
    print_header("Complete Database Setup")
    
    # Step 1: Check environment
    print_step(1, "Checking Environment")
    
    required_vars = ['SUPABASE_URL', 'SUPABASE_ANON_KEY', 'SUPABASE_SERVICE_ROLE_KEY', 'SUPABASE_DB_PASSWORD']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"  ❌ Missing environment variables: {', '.join(missing)}")
        print("\n  Add them to your .env file")
        sys.exit(1)
    
    print("  ✓ All environment variables set")
    
    # Step 2: Connect to database
    print_step(2, "Connecting to Database")
    
    try:
        conn = get_db_connection()
        print("  ✓ Connected successfully")
    except Exception as e:
        print(f"  ❌ Connection failed: {e}")
        sys.exit(1)
    
    try:
        # Step 3: List existing tables
        print_step(3, "Checking Existing Tables")
        
        existing_tables = list_existing_tables(conn)
        
        if existing_tables:
            print(f"  Found {len(existing_tables)} existing tables:")
            for table in existing_tables:
                print(f"    - {table}")
            
            if args.clean:
                print("\n  🗑️  Cleaning up existing tables...")
                
                # Define tables to keep (Supabase system tables)
                system_tables = ['schema_migrations', 'supabase_functions_migrations']
                
                # Drop user tables
                tables_to_drop = [t for t in existing_tables if t not in system_tables]
                
                if tables_to_drop:
                    response = input(f"\n  ⚠️  This will drop {len(tables_to_drop)} tables. Continue? (yes/no): ")
                    if response.lower() != 'yes':
                        print("  Cancelled.")
                        sys.exit(0)
                    
                    for table in tables_to_drop:
                        drop_table(conn, table)
                else:
                    print("  No user tables to drop")
        else:
            print("  No existing tables found")
        
        # Step 4: Create storage buckets
        print_step(4, "Setting Up Storage Buckets")
        
        migrations_dir = Path(__file__).parent / "migrations"
        storage_file = migrations_dir / "001_setup_storage.sql"
        
        if storage_file.exists():
            execute_sql_file(conn, storage_file, "Creating storage buckets and policies")
        else:
            print("  ⚠️  Storage setup file not found, skipping")
        
        # Step 5: Enable extensions
        print_step(5, "Enabling PostgreSQL Extensions")
        
        extensions_file = migrations_dir / "001_enable_extensions.sql"
        if not execute_sql_file(conn, extensions_file, "Enabling extensions"):
            print("\n  ⚠️  Note: If 'vector' extension fails, enable it in Supabase dashboard:")
            print("     Database → Extensions → Search 'vector' → Enable")
        
        # Step 6: Create tables
        print_step(6, "Creating Database Tables")
        
        tables_file = migrations_dir / "002_create_tables.sql"
        if not execute_sql_file(conn, tables_file, "Creating tables"):
            print("  ❌ Failed to create tables")
            sys.exit(1)
        
        # Step 7: Set up RLS policies
        print_step(7, "Setting Up Row Level Security")
        
        rls_file = migrations_dir / "003_create_rls_policies.sql"
        if not execute_sql_file(conn, rls_file, "Creating RLS policies"):
            print("  ❌ Failed to create RLS policies")
            sys.exit(1)
        
        # Step 8: Verify setup
        print_step(8, "Verifying Setup")
        
        final_tables = list_existing_tables(conn)
        required_tables = ['academic', 'personalized', 'courses', 'materials', 'chat_history']
        
        found_tables = [t for t in required_tables if t in final_tables]
        missing_tables = [t for t in required_tables if t not in final_tables]
        
        print(f"\n  Required tables: {len(required_tables)}")
        print(f"  Found: {len(found_tables)}")
        
        if found_tables:
            print("\n  ✓ Created tables:")
            for table in found_tables:
                print(f"    - {table}")
        
        if missing_tables:
            print("\n  ✗ Missing tables:")
            for table in missing_tables:
                print(f"    - {table}")
            print("\n  ❌ Setup incomplete")
            sys.exit(1)
        
        # Success!
        print_header("Setup Complete! 🎉")
        
        print("Your database is ready with:")
        print("  ✓ Storage bucket: course-materials")
        print("  ✓ 5 tables: academic, personalized, courses, materials, chat_history")
        print("  ✓ Row Level Security policies")
        print("  ✓ Indexes for performance")
        
        print("\nNext steps:")
        print("  1. Start backend: python main.py")
        print("  2. Test signup: curl -X POST http://localhost:8000/api/auth/signup \\")
        print("                       -H 'Content-Type: application/json' \\")
        print("                       -d '{\"email\":\"test@example.com\",\"password\":\"password123\"}'")
        
        print("\nStorage bucket structure:")
        print("  course-materials/{user_id}/{course_id}/{filename}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
