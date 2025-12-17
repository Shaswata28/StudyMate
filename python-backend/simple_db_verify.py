#!/usr/bin/env python3
"""
Simple Database Schema Verification Script
Feature: rag-functionality-fix
Task: 1. Verify and fix database schema issues

This script verifies:
1. Vector embedding dimension is 1024 in materials table
2. search_materials_by_embedding function exists and works correctly
3. Tests database function with sample data

Requirements: 7.2, 7.3
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional

# Add the parent directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main function to run the verification."""
    logger.info("=" * 60)
    logger.info("STARTING DATABASE SCHEMA VERIFICATION")
    logger.info("=" * 60)
    
    try:
        from services.supabase_client import supabase_admin
        client = supabase_admin
        logger.info("✅ Supabase client initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Supabase client: {e}")
        return False
    
    results = {}
    
    # Test 1: Check vector dimension
    logger.info("\n1. Checking vector embedding dimension...")
    try:
        result = client.rpc('exec_sql', {
            'query': """
            SELECT 
                atttypmod - 4 as vector_dimension
            FROM pg_attribute 
            WHERE attrelid = 'materials'::regclass 
                AND attname = 'embedding'
            """
        }).execute()
        
        if result.data and len(result.data) > 0:
            dimension = result.data[0]['vector_dimension']
            if dimension == 1024:
                logger.info(f"✅ Vector dimension is correct: {dimension}")
                results['vector_dimension'] = True
            else:
                logger.error(f"❌ Vector dimension is {dimension}, expected 1024")
                results['vector_dimension'] = False
        else:
            logger.error("❌ Could not determine vector dimension")
            results['vector_dimension'] = False
            
    except Exception as e:
        logger.error(f"❌ Error checking vector dimension: {e}")
        results['vector_dimension'] = False
    
    # Test 2: Check materials table schema
    logger.info("\n2. Checking materials table schema...")
    try:
        result = client.rpc('exec_sql', {
            'query': """
            SELECT 
                column_name,
                data_type,
                is_nullable
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
        
        if not missing_columns:
            logger.info("✅ All required columns found in materials table")
            results['materials_schema'] = True
        else:
            logger.error(f"❌ Missing columns: {missing_columns}")
            results['materials_schema'] = False
            
    except Exception as e:
        logger.error(f"❌ Error checking materials table schema: {e}")
        results['materials_schema'] = False
    
    # Test 3: Check search function exists
    logger.info("\n3. Checking search_materials_by_embedding function...")
    try:
        result = client.rpc('exec_sql', {
            'query': """
            SELECT 
                proname,
                pg_get_function_arguments(oid) as arguments
            FROM pg_proc 
            WHERE proname = 'search_materials_by_embedding'
            """
        }).execute()
        
        if result.data and len(result.data) > 0:
            func_info = result.data[0]
            logger.info(f"✅ Function found: {func_info['proname']}")
            logger.info(f"Arguments: {func_info['arguments']}")
            results['search_function'] = True
        else:
            logger.error("❌ search_materials_by_embedding function not found!")
            results['search_function'] = False
            
    except Exception as e:
        logger.error(f"❌ Error checking search function: {e}")
        results['search_function'] = False
    
    # Test 4: Test function with dummy data
    logger.info("\n4. Testing search function with dummy data...")
    try:
        # Create a dummy UUID and embedding for testing
        dummy_uuid = '00000000-0000-0000-0000-000000000000'
        dummy_embedding = [0.0] * 1024
        
        # Test the function call (should return empty results but not error)
        result = client.rpc('search_materials_by_embedding', {
            'query_course_id': dummy_uuid,
            'query_embedding': dummy_embedding,
            'match_limit': 1
        }).execute()
        
        logger.info("✅ Function signature test passed")
        logger.info(f"Results: {len(result.data)} materials found (expected 0 for dummy data)")
        results['function_test'] = True
        
    except Exception as e:
        logger.error(f"❌ Function signature test failed: {e}")
        results['function_test'] = False
    
    # Test 5: Check indexes
    logger.info("\n5. Checking required indexes...")
    try:
        result = client.rpc('exec_sql', {
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
        
        if not missing_indexes:
            logger.info("✅ All required indexes found")
            results['indexes'] = True
        else:
            logger.error(f"❌ Missing indexes: {missing_indexes}")
            results['indexes'] = False
            
    except Exception as e:
        logger.error(f"❌ Error checking indexes: {e}")
        results['indexes'] = False
    
    # Summary
    logger.info("\n" + "=" * 60)
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
        
        # Provide fix suggestions
        logger.info("\n📋 SUGGESTED FIXES:")
        if not results.get('vector_dimension', True):
            logger.info("- Run migration 006_update_embedding_dimension.sql to fix vector dimension")
        if not results.get('materials_schema', True):
            logger.info("- Run migration 005_add_material_ocr_embedding.sql to add missing columns")
        if not results.get('search_function', True):
            logger.info("- Run migration 006_add_vector_search_function.sql to create search function")
        if not results.get('indexes', True):
            logger.info("- Check and recreate missing indexes")
    
    logger.info("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)