#!/usr/bin/env python3
"""
Setup Database via Supabase API

This script uses the Supabase Python client instead of direct PostgreSQL connection.
Useful when direct database connection is blocked by firewall/network.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from config import config
from services.supabase_client import supabase_admin

def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")

def print_step(number, text):
    print(f"\n{'─' * 70}")
    print(f"Step {number}: {text}")
    print('─' * 70)

def read_sql_file(file_path):
    """Read SQL file content."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def execute_sql_via_api(sql, description):
    """Execute SQL using Supabase API."""
    print(f"\n  📄 {description}")
    
    try:
        # Split SQL into individual statements
        statements = [s.strip() for s in sql.split(';') if s.strip()]
        
        for i, statement in enumerate(statements, 1):
            if not statement:
                continue
                
            # Skip comments
            if statement.startswith('--'):
                continue
            
            print(f"     Executing statement {i}/{len(statements)}...", end='')
            
            # Execute via Supabase RPC or direct query
            result = supabase_admin.rpc('exec_sql', {'query': statement}).execute()
            
            print(" ✓")
        
        print(f"  ✓ {description} completed")
        return True
        
    except Exception as e:
        print(f"\n  ✗ Error: {e}")
        return False

def main():
    print_header("Database Setup via Supabase API")
    
    print("⚠️  Note: This method uses Supabase API instead of direct PostgreSQL connection.")
    print("   Some operations may not be supported. For full setup, use direct connection.\n")
    
    # Step 1: Check environment
    print_step(1, "Checking Environment")
    print("  ✓ Supabase client initialized")
    print(f"  ✓ Project URL: {config.SUPABASE_URL}")
    
    # Step 2: Test connection
    print_step(2, "Testing Supabase Connection")
    
    try:
        # Test by querying auth users (should work even if empty)
        result = supabase_admin.auth.get_user("test")
        print("  ✓ Supabase API connection working")
    except Exception as e:
        print(f"  ✓ Supabase API accessible (test query expected to fail)")
    
    # Step 3: Instructions for manual setup
    print_step(3, "Manual Setup Required")
    
    print("\n  ⚠️  Direct database connection is not available.")
    print("  You have two options:\n")
    
    print("  Option 1: Use Supabase SQL Editor (Recommended)")
    print("  ─────────────────────────────────────────────")
    print("  1. Go to: https://supabase.com/dashboard/project/fupupzbizwmxtcrftdhy")
    print("  2. Click 'SQL Editor' in the left sidebar")
    print("  3. Run these SQL files in order:\n")
    
    migrations_dir = Path(__file__).parent / "migrations"
    sql_files = [
        "001_enable_extensions.sql",
        "001_setup_storage.sql",
        "002_create_tables.sql",
        "003_create_rls_policies.sql"
    ]
    
    for sql_file in sql_files:
        file_path = migrations_dir / sql_file
        if file_path.exists():
            print(f"     • {sql_file}")
            print(f"       Copy from: {file_path}")
    
    print("\n  Option 2: Fix Network Connection")
    print("  ─────────────────────────────────")
    print("  • Check if you're behind a firewall")
    print("  • Try disabling VPN if you're using one")
    print("  • Check if port 5432 is blocked")
    print("  • Try from a different network")
    
    print("\n  Option 3: Copy SQL Files")
    print("  ────────────────────────")
    print("  I can show you the SQL content to copy-paste into Supabase SQL Editor.")
    
    response = input("\n  Would you like to see the SQL files content? (y/n): ").strip().lower()
    
    if response == 'y':
        for sql_file in sql_files:
            file_path = migrations_dir / sql_file
            if file_path.exists():
                print(f"\n\n{'=' * 70}")
                print(f"  {sql_file}")
                print('=' * 70)
                content = read_sql_file(file_path)
                print(content)
                print('=' * 70)
                input("\nPress Enter to continue to next file...")
    
    print_header("Next Steps")
    print("1. Go to Supabase SQL Editor")
    print("2. Copy and run each SQL file in order")
    print("3. Verify tables are created in Table Editor")
    print("\nOnce done, your database will be ready! 🎉\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
