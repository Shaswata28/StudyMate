-- ============================================================================
-- MATERIAL OCR AND EMBEDDING MIGRATION
-- ============================================================================
-- Feature: material-ocr-embedding
-- Requirements: 1.1, 9.1, 9.2, 9.3, 9.4
-- 
-- DESCRIPTION:
-- This migration adds OCR (Optical Character Recognition) and vector embedding
-- support to the materials table. It enables:
-- - Automatic text extraction from PDFs and images
-- - Semantic search using vector embeddings
-- - Processing status tracking
-- - Error handling and logging
--
-- PREREQUISITES:
-- 1. The 'vector' extension must be enabled (should already be enabled)
-- 2. The materials table must exist
--
-- EXECUTION INSTRUCTIONS:
-- 1. Open Supabase Dashboard → SQL Editor
-- 2. Copy and paste this entire script
-- 3. Click "Run" to execute
-- 4. Verify success by checking the materials table schema
--
-- ROLLBACK:
-- If you need to undo this migration, see the rollback script at the bottom
-- ============================================================================

-- Verify vector extension is enabled (should already be enabled from previous migrations)
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- STEP 1: Add New Columns to Materials Table
-- ============================================================================

-- Add extracted_text column to store OCR results
ALTER TABLE materials 
ADD COLUMN IF NOT EXISTS extracted_text TEXT;

-- Add embedding column to store 384-dimensional vector embeddings
ALTER TABLE materials 
ADD COLUMN IF NOT EXISTS embedding VECTOR(384);

-- Add processing_status column with constraint to track processing state
ALTER TABLE materials 
ADD COLUMN IF NOT EXISTS processing_status TEXT DEFAULT 'pending';

-- Add constraint for processing_status if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'materials_processing_status_check'
    ) THEN
        ALTER TABLE materials 
        ADD CONSTRAINT materials_processing_status_check 
        CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed'));
    END IF;
END $$;

-- Add processed_at timestamp column
ALTER TABLE materials 
ADD COLUMN IF NOT EXISTS processed_at TIMESTAMPTZ;

-- Add error_message column for storing processing errors
ALTER TABLE materials 
ADD COLUMN IF NOT EXISTS error_message TEXT;

-- ============================================================================
-- STEP 2: Create Indexes for Performance
-- ============================================================================

-- Create index on processing_status for efficient filtering
-- This allows fast queries like: WHERE processing_status = 'pending'
CREATE INDEX IF NOT EXISTS idx_materials_processing_status 
ON materials(processing_status);

-- Create HNSW index on embedding column for fast vector similarity search
-- HNSW (Hierarchical Navigable Small World) provides approximate nearest neighbor search
-- Using cosine distance operator for semantic similarity
-- This enables fast queries like: ORDER BY embedding <=> query_vector LIMIT 10
CREATE INDEX IF NOT EXISTS idx_materials_embedding 
ON materials USING hnsw (embedding vector_cosine_ops);

-- ============================================================================
-- STEP 3: Add Column Comments for Documentation
-- ============================================================================

COMMENT ON COLUMN materials.embedding IS 
'Vector embedding (384 dimensions) for semantic search using sentence-transformers models. Generated from extracted_text using AI embedding models.';

COMMENT ON COLUMN materials.extracted_text IS 
'Text content extracted from PDF/image files using OCR (Optical Character Recognition). Used as input for embedding generation.';

COMMENT ON COLUMN materials.processing_status IS 
'Processing status tracking: pending (uploaded, awaiting processing), processing (OCR/embedding in progress), completed (successfully processed), failed (error occurred)';

COMMENT ON COLUMN materials.processed_at IS 
'Timestamp when OCR and embedding processing completed successfully. NULL if processing not yet complete.';

COMMENT ON COLUMN materials.error_message IS 
'Detailed error message if processing failed. NULL if no error or processing not yet attempted.';

-- ============================================================================
-- STEP 4: Update Existing Materials to Pending Status
-- ============================================================================

-- Set existing materials to 'pending' status if they don't have a status yet
-- This ensures all existing materials will be processed by the background job
UPDATE materials 
SET processing_status = 'pending' 
WHERE processing_status IS NULL;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify the new columns exist
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
ORDER BY ordinal_position;

-- Verify the indexes were created
SELECT 
    indexname, 
    indexdef 
FROM pg_indexes 
WHERE tablename = 'materials' 
    AND indexname IN (
        'idx_materials_processing_status', 
        'idx_materials_embedding'
    );

-- Check the constraint on processing_status
SELECT 
    conname, 
    pg_get_constraintdef(oid) as constraint_definition
FROM pg_constraint 
WHERE conrelid = 'materials'::regclass 
    AND conname = 'materials_processing_status_check';

-- Count materials by processing status
SELECT 
    processing_status, 
    COUNT(*) as count 
FROM materials 
GROUP BY processing_status;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- If you see results from the verification queries above, the migration was successful!
-- Next steps:
-- 1. Deploy the backend code with OCR and embedding processing
-- 2. Background jobs will automatically process pending materials
-- 3. Use semantic search endpoints to query materials by meaning

-- ============================================================================
-- ROLLBACK SCRIPT (Use only if you need to undo this migration)
-- ============================================================================

/*
-- WARNING: This will delete all OCR and embedding data!
-- Only run this if you need to completely undo the migration

-- Drop indexes
DROP INDEX IF EXISTS idx_materials_embedding;
DROP INDEX IF EXISTS idx_materials_processing_status;

-- Drop constraint
ALTER TABLE materials DROP CONSTRAINT IF EXISTS materials_processing_status_check;

-- Drop columns
ALTER TABLE materials DROP COLUMN IF EXISTS error_message;
ALTER TABLE materials DROP COLUMN IF EXISTS processed_at;
ALTER TABLE materials DROP COLUMN IF EXISTS processing_status;
ALTER TABLE materials DROP COLUMN IF EXISTS embedding;
ALTER TABLE materials DROP COLUMN IF EXISTS extracted_text;

-- Verify rollback
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'materials' 
ORDER BY ordinal_position;
*/
