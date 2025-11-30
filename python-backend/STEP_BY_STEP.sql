-- ============================================================================
-- STEP-BY-STEP DATABASE SETUP
-- ============================================================================
-- Run each section separately in Supabase SQL Editor to see where errors occur
-- ============================================================================

-- ============================================================================
-- SECTION 1: ENABLE EXTENSIONS (Run this first)
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- After running, you should see: "Success. No rows returned"

-- ============================================================================
-- SECTION 2: CREATE TRIGGER FUNCTION (Run this second)
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at() 
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- After running, you should see: "Success. No rows returned"

-- ============================================================================
-- SECTION 3: CREATE TABLES (Run this third)
-- ============================================================================

-- Table 1: academic
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
    CONSTRAINT academic_grade_not_empty CHECK (array_length(grade, 1) > 0)
);

CREATE TRIGGER academic_update_trigger 
    BEFORE UPDATE ON academic 
    FOR EACH ROW 
    EXECUTE PROCEDURE update_updated_at();

CREATE INDEX idx_academic_grade ON academic USING GIN (grade);
CREATE INDEX idx_academic_subject ON academic USING GIN (subject);

-- Table 2: personalized
CREATE TABLE personalized (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    prefs JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER personalized_update_trigger 
    BEFORE UPDATE ON personalized 
    FOR EACH ROW 
    EXECUTE PROCEDURE update_updated_at();

CREATE INDEX idx_personalized_prefs ON personalized USING GIN (prefs);

-- Table 3: courses
CREATE TABLE courses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER courses_update_trigger 
    BEFORE UPDATE ON courses 
    FOR EACH ROW 
    EXECUTE PROCEDURE update_updated_at();

CREATE INDEX idx_courses_user_id ON courses(user_id);

-- Table 4: materials
CREATE TABLE materials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER materials_update_trigger 
    BEFORE UPDATE ON materials 
    FOR EACH ROW 
    EXECUTE PROCEDURE update_updated_at();

CREATE INDEX idx_materials_course_id ON materials(course_id);
CREATE INDEX idx_materials_file_path ON materials(file_path);

-- Table 5: chat_history
CREATE TABLE chat_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    history JSONB[] NOT NULL DEFAULT '{}',
    embedding VECTOR(384),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER chat_history_update_trigger 
    BEFORE UPDATE ON chat_history 
    FOR EACH ROW 
    EXECUTE PROCEDURE update_updated_at();

CREATE INDEX idx_chat_history_course_id ON chat_history(course_id);
CREATE INDEX chat_history_embedding_idx ON chat_history USING hnsw (embedding vector_cosine_ops);

-- After running, check Table Editor - you should see all 5 tables!

-- ============================================================================
-- SECTION 4: ENABLE ROW LEVEL SECURITY (Run this fourth)
-- ============================================================================

-- Academic table RLS
ALTER TABLE academic ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users edit own academic data" 
ON academic FOR ALL 
USING (auth.uid() = id) 
WITH CHECK (auth.uid() = id);

-- Personalized table RLS
ALTER TABLE personalized ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users edit own prefs" 
ON personalized FOR ALL 
USING (auth.uid() = id) 
WITH CHECK (auth.uid() = id);

-- Courses table RLS
ALTER TABLE courses ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users own courses" 
ON courses FOR ALL 
USING (auth.uid() = user_id) 
WITH CHECK (auth.uid() = user_id);

-- Materials table RLS
ALTER TABLE materials ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users own materials" 
ON materials FOR ALL 
USING (
    course_id IN (SELECT id FROM courses WHERE user_id = auth.uid())
) 
WITH CHECK (
    course_id IN (SELECT id FROM courses WHERE user_id = auth.uid())
);

-- Chat history table RLS
ALTER TABLE chat_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users own chat history" 
ON chat_history FOR ALL 
USING (
    course_id IN (SELECT id FROM courses WHERE user_id = auth.uid())
) 
WITH CHECK (
    course_id IN (SELECT id FROM courses WHERE user_id = auth.uid())
);

-- After running, you should see: "Success. No rows returned"

-- ============================================================================
-- DONE! Verify in Table Editor
-- ============================================================================
