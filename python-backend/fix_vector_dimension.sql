-- ============================================================================
-- FIX VECTOR DIMENSION TO 1024
-- ============================================================================
-- Feature: rag-functionality-fix
-- Task: 1. Verify and fix database schema issues
-- Requirements: 7.2, 7.3
--
-- This script updates the materials.embedding column from VECTOR(384) to VECTOR(1024)
-- and ensures the search function uses the correct dimension.
--
-- EXECUTION INSTRUCTIONS:
-- 1. Open Supabase Dashboard → SQL Editor
-- 2. Copy and paste this entire script
-- 3. Click "Run" to execute
-- ============================================================================

-- Step 1: Drop the existing HNSW index (required before altering column type)
DROP INDEX IF EXISTS idx_materials_embedding;

-- Step 2: Alter the embedding column to use VECTOR(1024)
-- Note: This will clear existing embeddings (they need to be regenerated)
ALTER TABLE materials 
ALTER COLUMN embedding TYPE VECTOR(1024);

-- Step 3: Clear existing embeddings and reset processing status
-- Existing 384-dim embeddings are incompatible with 1024-dim model
UPDATE materials 
SET 
    embedding = NULL,
    processing_status = 'pending',
    processed_at = NULL,
    error_message = NULL
WHERE embedding IS NOT NULL;

-- Step 4: Recreate the HNSW index with new dimension
CREATE INDEX idx_materials_embedding 
ON materials 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Step 5: Update/Create the search function with correct dimension
CREATE OR REPLACE FUNCTION search_materials_by_embedding(
    query_course_id UUID,
    query_embedding VECTOR(1024),
    match_limit INT DEFAULT 3
)
RETURNS TABLE (
    id UUID,
    name TEXT,
    extracted_text TEXT,
    file_type TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        m.id,
        m.name,
        m.extracted_text,
        m.file_type,
        1 - (m.embedding <=> query_embedding) AS similarity
    FROM materials m
    WHERE 
        m.course_id = query_course_id
        AND m.processing_status = 'completed'
        AND m.embedding IS NOT NULL
    ORDER BY m.embedding <=> query_embedding
    LIMIT match_limit;
END;
$$;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION search_materials_by_embedding TO authenticated;

-- Add comment
COMMENT ON FUNCTION search_materials_by_embedding IS 
'Performs semantic search on materials using vector similarity. Returns materials ranked by cosine similarity to the query embedding. Uses 1024-dimensional vectors.';

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Check the new column type and dimension
SELECT 
    column_name, 
    data_type,
    udt_name
FROM information_schema.columns 
WHERE table_name = 'materials' 
    AND column_name = 'embedding';

-- Check vector dimension from pg_attribute
SELECT 
    atttypmod - 4 as vector_dimension
FROM pg_attribute 
WHERE attrelid = 'materials'::regclass 
    AND attname = 'embedding';

-- Check index was recreated
SELECT 
    indexname, 
    indexdef 
FROM pg_indexes 
WHERE tablename = 'materials' 
    AND indexname = 'idx_materials_embedding';

-- Check function exists with correct signature
SELECT 
    proname,
    pg_get_function_arguments(oid) as arguments,
    pg_get_function_result(oid) as return_type
FROM pg_proc 
WHERE proname = 'search_materials_by_embedding';

-- Check materials were reset to pending
SELECT 
    processing_status, 
    COUNT(*) as count 
FROM materials 
GROUP BY processing_status;

-- ============================================================================
-- EXPECTED RESULTS:
-- ============================================================================
-- 1. Vector dimension should be 1024
-- 2. Index should be recreated
-- 3. Function should accept VECTOR(1024) parameter
-- 4. All materials should be in 'pending' status for reprocessing
-- ============================================================================