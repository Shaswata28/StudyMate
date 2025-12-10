-- ============================================================================
-- TEST SEARCH FUNCTION WITH SAMPLE DATA
-- ============================================================================
-- Feature: rag-functionality-fix
-- Task: 1. Verify and fix database schema issues
-- Requirements: 7.2, 7.3
--
-- This script tests the search_materials_by_embedding function with sample data
--
-- EXECUTION INSTRUCTIONS:
-- 1. Run fix_vector_dimension.sql first
-- 2. Open Supabase Dashboard → SQL Editor
-- 3. Copy and paste this script
-- 4. Click "Run" to execute
-- ============================================================================

-- Test 1: Verify function exists and has correct signature
SELECT 
    proname as function_name,
    pg_get_function_arguments(oid) as arguments,
    pg_get_function_result(oid) as return_type
FROM pg_proc 
WHERE proname = 'search_materials_by_embedding';

-- Test 2: Test function with dummy data (should return empty results)
SELECT * FROM search_materials_by_embedding(
    '00000000-0000-0000-0000-000000000000'::UUID,  -- dummy course_id
    ARRAY[0.1, 0.2, 0.3]::VECTOR(1024),            -- dummy 1024-dim vector (truncated for display)
    3                                                -- limit
);

-- Test 3: Check if we have any courses to test with
SELECT 
    id as course_id,
    name as course_name,
    (SELECT COUNT(*) FROM materials WHERE course_id = courses.id) as material_count
FROM courses 
LIMIT 5;

-- Test 4: Check materials table structure
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'materials' 
    AND column_name IN (
        'id', 'course_id', 'name', 'extracted_text', 
        'embedding', 'processing_status', 'file_type'
    )
ORDER BY ordinal_position;

-- Test 5: Check current materials processing status
SELECT 
    processing_status,
    COUNT(*) as count,
    COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as with_embedding
FROM materials 
GROUP BY processing_status
ORDER BY processing_status;

-- Test 6: Verify vector dimension is correct
SELECT 
    'materials.embedding dimension' as check_name,
    atttypmod - 4 as vector_dimension,
    CASE 
        WHEN atttypmod - 4 = 1024 THEN '✅ CORRECT'
        ELSE '❌ INCORRECT - Expected 1024'
    END as status
FROM pg_attribute 
WHERE attrelid = 'materials'::regclass 
    AND attname = 'embedding';

-- Test 7: Check if vector index exists
SELECT 
    indexname,
    indexdef,
    CASE 
        WHEN indexdef LIKE '%vector_cosine_ops%' THEN '✅ CORRECT INDEX TYPE'
        ELSE '❌ INCORRECT INDEX TYPE'
    END as status
FROM pg_indexes 
WHERE tablename = 'materials' 
    AND indexname = 'idx_materials_embedding';

-- ============================================================================
-- EXPECTED RESULTS:
-- ============================================================================
-- Test 1: Should show function with VECTOR(1024) parameter
-- Test 2: Should return empty table (no error)
-- Test 3: Should show available courses (if any)
-- Test 4: Should show all required columns
-- Test 5: Should show materials in 'pending' status
-- Test 6: Should show dimension = 1024 with ✅ CORRECT status
-- Test 7: Should show index exists with vector_cosine_ops
-- ============================================================================