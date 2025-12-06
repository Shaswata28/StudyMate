-- Migration 006: Update embedding dimension from 384 to 1024
-- This migration changes the vector dimension to match mxbai-embed-large output

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

-- Verification queries
-- Check the new column type
SELECT 
    column_name, 
    data_type,
    udt_name
FROM information_schema.columns 
WHERE table_name = 'materials' 
    AND column_name = 'embedding';

-- Check index was recreated
SELECT 
    indexname, 
    indexdef 
FROM pg_indexes 
WHERE tablename = 'materials' 
    AND indexname = 'idx_materials_embedding';

-- Check materials were reset to pending
SELECT 
    processing_status, 
    COUNT(*) as count 
FROM materials 
GROUP BY processing_status;
