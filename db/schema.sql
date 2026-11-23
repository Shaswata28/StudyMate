-- ============================================================================
-- StudyMate v3 - Unified Database Schema
-- Compatible with Supabase Postgres + pgvector
-- ============================================================================

-- Step 1: Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Step 2: Storage bucket setup (for course materials)
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'course-materials',
    'course-materials',
    false,
    52428800, -- 50MB
    ARRAY[
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-powerpoint',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'text/plain',
        'text/markdown',
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/webp'
    ]
)
ON CONFLICT (id) DO NOTHING;

-- Storage policies
CREATE POLICY "Users can upload to own folder"
ON storage.objects FOR INSERT TO authenticated
WITH CHECK (
    bucket_id = 'course-materials' AND
    (storage.foldername(name))[1] = auth.uid()::text
);

CREATE POLICY "Users can read own files"
ON storage.objects FOR SELECT TO authenticated
USING (
    bucket_id = 'course-materials' AND
    (storage.foldername(name))[1] = auth.uid()::text
);

CREATE POLICY "Users can update own files"
ON storage.objects FOR UPDATE TO authenticated
USING (
    bucket_id = 'course-materials' AND
    (storage.foldername(name))[1] = auth.uid()::text
)
WITH CHECK (
    bucket_id = 'course-materials' AND
    (storage.foldername(name))[1] = auth.uid()::text
);

CREATE POLICY "Users can delete own files"
ON storage.objects FOR DELETE TO authenticated
USING (
    bucket_id = 'course-materials' AND
    (storage.foldername(name))[1] = auth.uid()::text
);

-- Step 3: Trigger for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at() 
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ----------------------------------------------------------------------------
-- Table: academic
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS academic (
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
    CONSTRAINT academic_grade_not_empty CHECK (array_length(grade, 1) > 0)
);

CREATE TRIGGER academic_update_trigger 
    BEFORE UPDATE ON academic 
    FOR EACH ROW 
    EXECUTE PROCEDURE update_updated_at();

CREATE INDEX IF NOT EXISTS idx_academic_grade ON academic USING GIN (grade);
CREATE INDEX IF NOT EXISTS idx_academic_subject ON academic USING GIN (subject);

-- ----------------------------------------------------------------------------
-- Table: personalized
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS personalized (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    prefs JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER personalized_update_trigger 
    BEFORE UPDATE ON personalized 
    FOR EACH ROW 
    EXECUTE PROCEDURE update_updated_at();

CREATE INDEX IF NOT EXISTS idx_personalized_prefs ON personalized USING GIN (prefs);

-- ----------------------------------------------------------------------------
-- Table: courses
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS courses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    color TEXT DEFAULT '#FEAE01',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER courses_update_trigger 
    BEFORE UPDATE ON courses 
    FOR EACH ROW 
    EXECUTE PROCEDURE update_updated_at();

CREATE INDEX IF NOT EXISTS idx_courses_user_id ON courses(user_id);

-- ----------------------------------------------------------------------------
-- Table: materials
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS materials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    extracted_text TEXT,
    embedding VECTOR(1024), -- 1024-dim for mxbai-embed-large
    processing_status TEXT DEFAULT 'pending' 
        CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
    processed_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER materials_update_trigger 
    BEFORE UPDATE ON materials 
    FOR EACH ROW 
    EXECUTE PROCEDURE update_updated_at();

CREATE INDEX IF NOT EXISTS idx_materials_course_id ON materials(course_id);
CREATE INDEX IF NOT EXISTS idx_materials_processing_status ON materials(processing_status);
CREATE INDEX IF NOT EXISTS idx_materials_embedding ON materials USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

-- ----------------------------------------------------------------------------
-- Table: chat_history
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS chat_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    history JSONB[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER chat_history_update_trigger 
    BEFORE UPDATE ON chat_history 
    FOR EACH ROW 
    EXECUTE PROCEDURE update_updated_at();

CREATE INDEX IF NOT EXISTS idx_chat_history_course_id ON chat_history(course_id);

-- ----------------------------------------------------------------------------
-- Search Function: search_materials_by_embedding
-- ----------------------------------------------------------------------------
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

-- ----------------------------------------------------------------------------
-- Row Level Security (RLS)
-- ----------------------------------------------------------------------------
ALTER TABLE academic ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users edit own academic data" ON academic FOR ALL USING (auth.uid() = id) WITH CHECK (auth.uid() = id);

ALTER TABLE personalized ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users edit own prefs" ON personalized FOR ALL USING (auth.uid() = id) WITH CHECK (auth.uid() = id);

ALTER TABLE courses ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users own courses" ON courses FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

ALTER TABLE materials ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users own materials" ON materials FOR ALL 
USING (course_id IN (SELECT id FROM courses WHERE user_id = auth.uid()))
WITH CHECK (course_id IN (SELECT id FROM courses WHERE user_id = auth.uid()));

ALTER TABLE chat_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users own chat history" ON chat_history FOR ALL 
USING (course_id IN (SELECT id FROM courses WHERE user_id = auth.uid()))
WITH CHECK (course_id IN (SELECT id FROM courses WHERE user_id = auth.uid()));

GRANT EXECUTE ON FUNCTION search_materials_by_embedding TO authenticated;

