-- Migration 006: Add vector search RPC function
-- This function enables efficient semantic search using pgvector

-- Create function for semantic search by embedding
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
'Performs semantic search on materials using vector similarity. Returns materials ranked by cosine similarity to the query embedding.';
