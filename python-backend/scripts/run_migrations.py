#!/usr/bin/env python3
"""
Database Migration Script for Supabase

This script executes SQL migration files against the Supabase database using
a direct PostgreSQL connection with the service role credentials.

Usage:
    python scripts/run_migrations.py [--rollback]

Options:
    --rollback    Execute the rollback migration (004_rollback.sql)
    
Requirements:
    - SUPABASE_URL must be set in .env
    - SUPABASE_SERVICE_ROLE_KEY must be set in .env (for connection string construction)
    - Migration files must be in python-backend/migrations/ directory
    - psycopg2-binary package must be installed
"""
import os
import sys
import argparse
from pathlib import Path
import logging
from urllib.parse import urlparse

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import config

# Try to import psycopg2
try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("\n❌ Error: psycopg2-binary is not installed")
    print("Please install it with: pip install psycopg2-binary")
    print("Or add it to requirements.txt and run: pip install -r requirements.txt\n")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def get_migrations_dir() -> Path:
    """Get the path to the migrations directory."""
    script_dir = Path(__file__).parent
    migrations_dir = script_dir.parent / "migrations"
    
    if not migrations_dir.exists():
        logger.error(f"Migrations directory not found: {migrations_dir}")
        sys.exit(1)
    
    return migrations_dir


def read_migration_file(file_path: Path) -> str:
    """
    Read a SQL migration file.
    
    Args:
        file_path: Path to the migration file
        
    Returns:
        str: Contents of the migration file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to read migration file {file_path}: {e}")
        raise


def get_db_connection_string() -> str:
    """
    Construct PostgreSQL connection string from Supabase URL.
    
    Supabase provides a REST API URL, but we need the direct PostgreSQL connection.
    The format is: postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
    
    Returns:
        str: PostgreSQL connection string
    """
    # Parse the Supabase URL to extract project reference
    parsed = urlparse(config.SUPABASE_URL)
    project_ref = parsed.hostname.split('.')[0] if parsed.hostname else None
    
    if not project_ref:
        logger.error("Could not extract project reference from SUPABASE_URL")
        sys.exit(1)
    
    # Note: For direct database connections, you need the database password
    # This is different from the service role key
    # Users should set SUPABASE_DB_PASSWORD in their .env file
    db_password = os.getenv("SUPABASE_DB_PASSWORD")
    
    if not db_password:
        logger.error("SUPABASE_DB_PASSWORD environment variable is not set")
        logger.error("This is your database password from Supabase project settings")
        logger.error("Add it to your .env file: SUPABASE_DB_PASSWORD=your_db_password")
        sys.exit(1)
    
    # Construct the PostgreSQL connection string
    conn_string = f"postgresql://postgres:{db_password}@db.{project_ref}.supabase.co:5432/postgres"
    
    return conn_string


def execute_sql(sql: str, migration_name: str, conn) -> bool:
    """
    Execute SQL against Supabase database.
    
    Args:
        sql: SQL statements to execute
        migration_name: Name of the migration for logging
        conn: psycopg2 database connection
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Executing migration: {migration_name}")
        
        # Create a cursor
        cursor = conn.cursor()
        
        try:
            # Execute the SQL
            cursor.execute(sql)
            
            # Commit the transaction
            conn.commit()
            
            logger.info(f"✓ Migration {migration_name} completed successfully")
            return True
            
        except Exception as e:
            # Rollback on error
            conn.rollback()
            logger.error(f"SQL execution error in {migration_name}: {e}")
            return False
            
        finally:
            cursor.close()
        
    except Exception as e:
        logger.error(f"Error executing migration {migration_name}: {e}")
        logger.exception("Full traceback:")
        return False


def run_forward_migrations() -> bool:
    """
    Execute forward migrations in order.
    
    Returns:
        bool: True if all migrations succeeded, False otherwise
    """
    migrations_dir = get_migrations_dir()
    
    # Define migration files in execution order
    migration_files = [
        "001_enable_extensions.sql",
        "002_create_tables.sql",
        "003_create_rls_policies.sql"
    ]
    
    logger.info("=" * 70)
    logger.info("Starting forward migrations")
    logger.info("=" * 70)
    
    # Get database connection
    conn_string = get_db_connection_string()
    
    try:
        # Connect to database
        logger.info("Connecting to Supabase database...")
        conn = psycopg2.connect(conn_string)
        logger.info("✓ Database connection established")
        
        try:
            for migration_file in migration_files:
                file_path = migrations_dir / migration_file
                
                if not file_path.exists():
                    logger.error(f"Migration file not found: {file_path}")
                    return False
                
                logger.info(f"\n📄 Processing: {migration_file}")
                
                # Read migration SQL
                sql = read_migration_file(file_path)
                
                # Execute migration
                if not execute_sql(sql, migration_file, conn):
                    logger.error(f"\n❌ Migration failed: {migration_file}")
                    logger.error("Stopping migration process.")
                    return False
            
            logger.info("\n" + "=" * 70)
            logger.info("✅ All migrations completed successfully!")
            logger.info("=" * 70)
            return True
            
        finally:
            # Always close the connection
            conn.close()
            logger.info("Database connection closed")
            
    except psycopg2.Error as e:
        logger.error(f"Database connection error: {e}")
        return False


def run_rollback() -> bool:
    """
    Execute rollback migration.
    
    Returns:
        bool: True if rollback succeeded, False otherwise
    """
    migrations_dir = get_migrations_dir()
    rollback_file = migrations_dir / "004_rollback.sql"
    
    if not rollback_file.exists():
        logger.error(f"Rollback file not found: {rollback_file}")
        return False
    
    logger.info("=" * 70)
    logger.info("Starting rollback migration")
    logger.info("=" * 70)
    logger.warning("\n⚠️  WARNING: This will drop all tables and data!")
    
    # Get database connection
    conn_string = get_db_connection_string()
    
    try:
        # Connect to database
        logger.info("Connecting to Supabase database...")
        conn = psycopg2.connect(conn_string)
        logger.info("✓ Database connection established")
        
        try:
            # Read rollback SQL
            sql = read_migration_file(rollback_file)
            
            # Execute rollback
            if not execute_sql(sql, "004_rollback.sql", conn):
                logger.error("\n❌ Rollback failed")
                return False
            
            logger.info("\n" + "=" * 70)
            logger.info("✅ Rollback completed successfully")
            logger.info("=" * 70)
            return True
            
        finally:
            # Always close the connection
            conn.close()
            logger.info("Database connection closed")
            
    except psycopg2.Error as e:
        logger.error(f"Database connection error: {e}")
        return False


def main():
    """Main entry point for the migration script."""
    parser = argparse.ArgumentParser(
        description="Execute Supabase database migrations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run forward migrations
  python scripts/run_migrations.py
  
  # Run rollback migration
  python scripts/run_migrations.py --rollback
        """
    )
    parser.add_argument(
        '--rollback',
        action='store_true',
        help='Execute rollback migration (drops all tables)'
    )
    
    args = parser.parse_args()
    
    # Print configuration info
    logger.info(f"Supabase URL: {config.SUPABASE_URL}")
    
    # Execute migrations
    try:
        if args.rollback:
            success = run_rollback()
        else:
            success = run_forward_migrations()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.warning("\n\n⚠️  Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Unexpected error: {e}")
        logger.exception("Full traceback:")
        sys.exit(1)


if __name__ == "__main__":
    main()
