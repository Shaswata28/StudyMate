-- Migration: Create Database Tables
-- Description: Create all tables for the learning platform with proper constraints,
--              indexes, and relationships
-- Requirements: 3.1, 3.2, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.5,
--               6.1, 6.2, 6.4, 6.5, 7.1, 7.2, 7.3, 7.4, 7.5

-- ============================================================================
-- TRIGGER FUNCTION: Automatic timestamp update
-- ============================================================================

-- Create trigger function for automatic updated_at timestamp management
-- This function will be used by all tables to automatically update the updated_at field
CREATE OR REPLACE FUNCTION update_updated_at() 
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TABLE: academic
-- ============================================================================

-- Stores normalized academic information for each user
-- One-to-one relationship with auth.users
CREATE TABLE academic (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    grade TEXT[] NOT NULL CHECK (grade <@ ARRAY['Bachelor', 'Masters']),
    semester_type TEXT NOT NULL CHECK (semester_type IN ('double', 'tri')),
    semester INTEGER NOT NULL CHECK (semester BETWEEN 1 AND 12),
    subject TEXT[] NOT NULL DEFAULT '{}' CHECK (
        subject <@ ARRAY[
            'computer science',
            'electrical and electronics engineering',
            'english',
            'business administration',
            'economics'
        ]
    ),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure at least one grade is specified
    CONSTRAINT academic_grade_not_empty CHECK (array_length(grade, 1) > 0)
);

-- Create trigger for automatic timestamp update
CREATE TRIGGER academic_update_trigger 
    BEFORE UPDATE ON academic 
    FOR EACH ROW 
    EXECUTE PROCEDURE update_updated_at();

-- Create indexes for efficient querying
CREATE INDEX idx_academic_grade ON academic USING GIN (grade);
CREATE INDEX idx_academic_subject ON academic USING GIN (subject);

-- Add comment for documentation
COMMENT ON TABLE academic IS 'Stores user academic profiles with grade, semester, and subject information';
COMMENT ON COLUMN academic.subject IS 'Valid subjects: computer science, electrical and electronics engineering, english, business administration, economics';

-- ============================================================================
-- TABLE: personalized
-- ============================================================================

-- Stores flexible JSONB-based personalization preferences
-- One-to-one relationship with auth.users
CREATE TABLE personalized (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    prefs JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create trigger for automatic timestamp update
CREATE TRIGGER personalized_update_trigger 
    BEFORE UPDATE ON personalized 
    FOR EACH ROW 
    EXECUTE PROCEDURE update_updated_at();

-- Create GIN index for efficient JSONB queries
CREATE INDEX idx_personalized_prefs ON personalized USING GIN (prefs);

-- Add comments for documentation
COMMENT ON TABLE personalized IS 'Stores user learning preferences from questionnaire as flexible JSONB';
COMMENT ON COLUMN personalized.prefs IS 'JSONB object containing: detail_level, example_preference, analogy_preference, technical_language, structure_preference, visual_preference (all 0-1), learning_pace (slow/moderate/fast), prior_experience (beginner/intermediate/advanced/expert)';

-- ============================================================================
-- TABLE: courses
-- ============================================================================

-- Organizational containers for learning materials and conversations
-- One-to-many relationship with auth.users (user can have multiple courses)
CREATE TABLE courses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create trigger for automatic timestamp update
CREATE TRIGGER courses_update_trigger 
    BEFORE UPDATE ON courses 
    FOR EACH ROW 
    EXECUTE PROCEDURE update_updated_at();

-- Create index for efficient user course queries
CREATE INDEX idx_courses_user_id ON courses(user_id);

-- Add comments for documentation
COMMENT ON TABLE courses IS 'User-created courses for organizing learning materials and conversations';
COMMENT ON COLUMN courses.name IS 'Course name (e.g., "Biology 101", "Machine Learning")';

-- ============================================================================
-- TABLE: materials
-- ============================================================================

-- Metadata for uploaded learning materials with Supabase Storage integration
-- One-to-many relationship with courses (course can have multiple materials)
CREATE TABLE materials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    file_path TEXT NOT NULL, -- Path in storage bucket: {user_id}/{course_id}/{filename}
    file_type TEXT NOT NULL, -- MIME type (e.g., 'application/pdf')
    file_size BIGINT NOT NULL, -- File size in bytes
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create trigger for automatic timestamp update
CREATE TRIGGER materials_update_trigger 
    BEFORE UPDATE ON materials 
    FOR EACH ROW 
    EXECUTE PROCEDURE update_updated_at();

-- Create indexes for efficient queries
CREATE INDEX idx_materials_course_id ON materials(course_id);
CREATE INDEX idx_materials_file_path ON materials(file_path);

-- Add comments for documentation
COMMENT ON TABLE materials IS 'Metadata for uploaded learning materials (PDFs, documents, images)';
COMMENT ON COLUMN materials.file_path IS 'Storage path format: {user_id}/{course_id}/{filename}';
COMMENT ON COLUMN materials.file_type IS 'MIME type (e.g., application/pdf, image/jpeg)';
COMMENT ON COLUMN materials.file_size IS 'File size in bytes (max 50MB = 52428800 bytes)';

-- ============================================================================
-- TABLE: chat_history
-- ============================================================================

-- Conversational logs stored as JSONB arrays with vector embeddings for RAG
-- One-to-many relationship with courses (course can have multiple chat records)
CREATE TABLE chat_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    history JSONB[] NOT NULL DEFAULT '{}',
    embedding VECTOR(384),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create trigger for automatic timestamp update
CREATE TRIGGER chat_history_update_trigger 
    BEFORE UPDATE ON chat_history 
    FOR EACH ROW 
    EXECUTE PROCEDURE update_updated_at();

-- Create indexes for efficient queries
CREATE INDEX idx_chat_history_course_id ON chat_history(course_id);

-- Create HNSW index for fast vector similarity searches
-- Using cosine distance for semantic similarity
CREATE INDEX chat_history_embedding_idx 
    ON chat_history 
    USING hnsw (embedding vector_cosine_ops);

-- Add comments for documentation
COMMENT ON TABLE chat_history IS 'AI conversation history with vector embeddings for RAG context retrieval';
COMMENT ON COLUMN chat_history.history IS 'JSONB array of message objects: [{"role": "user", "content": "..."}, {"role": "model", "content": "..."}]';
COMMENT ON COLUMN chat_history.embedding IS 'Vector(384) embedding for semantic search and context retrieval';
