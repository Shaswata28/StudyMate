-- Migration: Add OCR and Embedding Support to Materials Table
-- Feature: material-ocr-embedding
-- Requirements: 1.1, 9.1, 9.2, 9.3, 9.4
-- Description: Adds columns for extracted text, vector embeddings, and processing status tracking

-- Add new columns to materials table
ALTER TABLE materials 
ADD COLUMN extracted_text TEXT,
ADD COLUMN embedding VECTOR(384),
ADD COLUMN processing_status TEXT DEFAULT 'pending' 
    CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
ADD COLUMN processed_at TIMESTAMPTZ,
ADD COLUMN error_message TEXT;

-- Create index on processing_status for efficient filtering
CREATE INDEX idx_materials_processing_status ON materials(processing_status);

-- Create HNSW index on embedding column for fast vector similarity search
-- HNSW (Hierarchical Navigable Small World) provides approximate nearest neighbor search
-- Using cosine distance operator for semantic similarity
CREATE INDEX idx_materials_embedding ON materials USING hnsw (embedding vector_cosine_ops);

-- Add comment to document the embedding dimension
COMMENT ON COLUMN materials.embedding IS 'Vector embedding (384 dimensions) for semantic search using sentence-transformers models';
COMMENT ON COLUMN materials.extracted_text IS 'Text content extracted from PDF/image using OCR';
COMMENT ON COLUMN materials.processing_status IS 'Processing status: pending (uploaded), processing (in progress), completed (success), failed (error)';
COMMENT ON COLUMN materials.processed_at IS 'Timestamp when OCR and embedding processing completed';
COMMENT ON COLUMN materials.error_message IS 'Error details if processing failed';
