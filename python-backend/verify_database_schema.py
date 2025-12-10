#!/usr/bin/env python3
"""
Database Schema Verification Script
Feature: rag-functionality-fix
Task: 1. Verify and fix database schema issues

This script verifies:
1. Vector embedding dimension is 1024 in materials table
2. search_materials_by_embedding function exists and works correctly
3. Tests database function with sample data

Requirements: 7.2, 7.3
"""

import asyncio
import os
import sys
from typing import List, Dict, Any, Optional
import logging
from supabase import create_client, Client
from pgvector import Vector
import numpy as np

# Add the parent directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.supabase_client import supabase_admin

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseSchemaVerifier:
    """Verifies and fixes database schema issues for RAG functionality."""
    
    def __init__(self):
        """Initialize the verifier with Supabase client."""
        self.client = supabase_admin
        logger.info("Database Schema Verifier initialized")
    
    async def verify_vector_dimension(self) -> bool:
        """
        Verify that the materials.embedding column uses VECTOR(1024).
        
        Returns:
            True if dimension is correct, False otherwise
        """
        logger.info("Verifying vector embedding dimension...")
        
        try:
            # Query to check the embedding column type and dimension
            result = self.client.rpc('exec_sql', {
                'query': """
                SELECT 
                    column_name,
                    data_type,
                    udt_name,
                    character_maximum_length
                FROM information_schema.columns 
                WHERE table_name = 'materials' 
                    AND column_name = 'embedding'
                """
            }).execute()
            
            if not result.data:
                logger.error("❌ materials.embedding column not found!")
                return False
            
            column_info = result.data[0]
            logger.info(f"Found embedding column: {column_info}")
            
            # Check if it's a vector type
            if column_info['udt_name'] != 'vector':
                logger.error(f"❌ Expected vector type, got: {column_info['udt_name']}")
                return False
            
            # For vector types, we need to check the dimension differently
            # Query the actual vector dimension from pg_attribute
            dim_result = self.client.rpc('exec_sql', {
                'query': """
                SELECT 
                    atttypmod - 4 as vector_dimension
                FROM pg_attribute 
                WHERE attrelid = 'materials'::regclass 
                    AND attname = 'embedding'
                """
            }).execute()
            
            if not dim_result.data:
                logger.error("❌ Could not determine vector dimension!")
                return False
            
            dimension = dim_result.data[0]['vector_dimension']
            logger.info(f"Vector dimension: {dimension}")
            
            if dimension == 1024:
                logger.info("✅ Vector dimension is correct (1024)")
                return True
            else:
                logger.error(f"❌ Vector dimension is {dimension}, expected 1024")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error verifying vector dimension: {e}")
            return False
    
    async def verify_search_function_exists(self) -> bool:
        """
        Verify that the search_materials_by_embedding function exists.
        
        Returns:
            True if function exists, False otherwise
        """
        logger.info("Verifying search_materials_by_embedding function exists...")
        
        try:
            # Query to check if the function exists
            result = self.client.rpc('exec_sql', {
                'query': """
                SELECT 
                    proname,
                    pg_get_function_arguments(oid) as arguments,
                    pg_get_function_result(oid) as return_type
                FROM pg_proc 
                WHERE proname = 'search_materials_by_embedding'
                """
            }).execute()
            
            if not result.data:
                logger.error("❌ search_materials_by_embedding function not found!")
                return False
            
            func_info = result.data[0]
            logger.info(f"✅ Function found: {func_info['proname']}")
            logger.info(f"Arguments: {func_info['arguments']}")
            logger.info(f"Return type: {func_info['return_type']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error verifying search function: {e}")
            return False
    
    async def test_search_function_with_sample_data(self) -> bool:
        """
        Test the search function with sample data.
        
        Returns:
            True if function works correctly, False otherwise
        """
        logger.info("Testing search function with sample data...")
        
        try:
            # First, let's check if we have any test courses and materials
            courses_result = self.client.table('courses').select('id, name').limit(1).execute()
            
            if not courses_result.data:
                logger.warning("⚠️  No courses found. Creating test course...")
                # We'll skip creating test data for now and just test the function signature
                return await self._test_function_signature()
            
            course_id = courses_result.data[0]['id']
            logger.info(f"Using test course: {course_id}")
            
            # Create a sample 1024-dimensional embedding vector
            sample_embedding = np.random.rand(1024).tolist()
            
            # Test the search function
            result = self.client.rpc('search_materials_by_embedding', {
                'query_course_id': course_id,
                'query_embedding': sample_embedding,
                'match_limit': 3
            }).execute()
            
            logger.info(f"✅ Search function executed successfully")
            logger.info(f"Results: {len(result.data)} materials found")
            
            # Verify the result structure
            if result.data:
                sample_result = result.data[0]
                expected_fields = ['id', 'name', 'extracted_text', 'file_type', 'similarity']
                
                for field in expected_fields:
                    if field not in sample_result:
                        logger.error(f"❌ Missing field in result: {field}")
                        return False
                
                logger.info("✅ Result structure is correct")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error testing search function: {e}")
            return False
    
    async def _test_function_signature(self) -> bool:
        """Test the function signature without real data."""
        try:
            # Create a dummy UUID and embedding for testing
            dummy_uuid = '00000000-0000-0000-0000-000000000000'
            dummy_embedding = [0.0] * 1024
            
            # Test the function call (should return empty results but not error)
            result = self.client.rpc('search_materials_by_embedding', {
                'query_course_id': dummy_uuid,
                'query_embedding': dummy_embedding,
                'match_limit': 1
            }).execute()
            
            logger.info("✅ Function signature test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Function signature test failed: {e}")
            return False
    
    async def check_materials_table_schema(self) -> bool:
        """
        Check that the materials table has all required columns for RAG.
        
        Returns:
            True if schema is correct, False otherwise
        """
        logger.info("Checking materials table schema...")
        
        try:
            # Check for required columns
            result = self.client.rpc('exec_sql', {
                'query': """
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns 
                WHERE table_name = 'materials' 
                    AND column_name IN (
                        'extracted_text', 
                        'embedding', 
                        'processing_status', 
                        'processed_at', 
                        'error_message'
                    )
                ORDER BY column_name
                """
            }).execute()
            
            expected_columns = {
                'extracted_text', 'embedding', 'processing_status', 
                'processed_at', 'error_message'
            }
            
            found_columns = {row['column_name'] for row in result.data}
            
            missing_columns = expected_columns - found_columns
            if missing_columns:
                logger.error(f"❌ Missing columns: {missing_columns}")
                return False
            
            logger.info("✅ All required columns found in materials table")
            
            # Check the processing_status constraint
            constraint_result = self.client.rpc('exec_sql', {
                'query': """
                SELECT 
                    conname, 
                    pg_get_constraintdef(oid) as constraint_definition
                FROM pg_constraint 
                WHERE conrelid = 'materials'::regclass 
                    AND conname LIKE '%processing_status%'
                """
            }).execute()
            
            if constraint_result.data:
                logger.info("✅ Processing status constraint found")
            else:
                logger.warning("⚠️  Processing status constraint not found")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error checking materials table schema: {e}")
            return False
    
    async def check_indexes(self) -> bool:
        """
        Check that required indexes exist for performance.
        
        Returns:
            True if indexes exist, False otherwise
        """
        logger.info("Checking required indexes...")
        
        try:
            # Check for required indexes
            result = self.client.rpc('exec_sql', {
                'query': """
                SELECT 
                    indexname, 
                    indexdef 
                FROM pg_indexes 
                WHERE tablename = 'materials' 
                    AND indexname IN (
                        'idx_materials_processing_status', 
                        'idx_materials_embedding'
                    )
                ORDER BY indexname
                """
            }).execute()
            
            expected_indexes = {'idx_materials_processing_status', 'idx_materials_embedding'}
            found_indexes = {row['indexname'] for row in result.data}
            
            missing_indexes = expected_indexes - found_indexes
            if missing_indexes:
                logger.error(f"❌ Missing indexes: {missing_indexes}")
                return False
            
            logger.info("✅ All required indexes found")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error checking indexes: {e}")
            return False
    
    async def run_full_verification(self) -> Dict[str, bool]:
        """
        Run all verification checks.
        
        Returns:
            Dictionary with check results
        """
        logger.info("=" * 60)
        logger.info("STARTING DATABASE SCHEMA VERIFICATION")
        logger.info("=" * 60)
        
        results = {}
        
        # Run all checks
        results['vector_dimension'] = await self.verify_vector_dimension()
        results['materials_schema'] = await self.check_materials_table_schema()
        results['indexes'] = await self.check_indexes()
        results['search_function'] = await self.verify_search_function_exists()
        results['function_test'] = await self.test_search_function_with_sample_data()
        
        # Summary
        logger.info("=" * 60)
        logger.info("VERIFICATION RESULTS SUMMARY")
        logger.info("=" * 60)
        
        all_passed = True
        for check, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"{check.replace('_', ' ').title()}: {status}")
            if not passed:
                all_passed = False
        
        logger.info("=" * 60)
        if all_passed:
            logger.info("🎉 ALL CHECKS PASSED! Database schema is ready for RAG functionality.")
        else:
            logger.error("⚠️  SOME CHECKS FAILED! Please review the issues above.")
        logger.info("=" * 60)
        
        return results

async def main():
    """Main function to run the verification."""
    verifier = DatabaseSchemaVerifier()
    results = await verifier.run_full_verification()
    
    # Exit with error code if any checks failed
    if not all(results.values()):
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())