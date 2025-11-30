-- Migration: Create Row Level Security (RLS) Policies
-- Description: Enable RLS on all tables and create policies to ensure users can only
--              access their own data, providing data isolation and security
-- Requirements: 1.3, 8.4

-- ============================================================================
-- TABLE: academic
-- ============================================================================

-- Enable Row Level Security on academic table
ALTER TABLE academic ENABLE ROW LEVEL SECURITY;

-- Policy: Users can read, insert, update, and delete their own academic data
-- Uses auth.uid() to get the authenticated user's ID from JWT token
CREATE POLICY "Users edit own academic data" 
ON academic 
FOR ALL 
USING (auth.uid() = id) 
WITH CHECK (auth.uid() = id);

-- ============================================================================
-- TABLE: personalized
-- ============================================================================

-- Enable Row Level Security on personalized table
ALTER TABLE personalized ENABLE ROW LEVEL SECURITY;

-- Policy: Users can read, insert, update, and delete their own preferences
-- Uses auth.uid() to get the authenticated user's ID from JWT token
CREATE POLICY "Users edit own prefs" 
ON personalized 
FOR ALL 
USING (auth.uid() = id) 
WITH CHECK (auth.uid() = id);

-- ============================================================================
-- TABLE: courses
-- ============================================================================

-- Enable Row Level Security on courses table
ALTER TABLE courses ENABLE ROW LEVEL SECURITY;

-- Policy: Users can read, insert, update, and delete their own courses
-- Uses auth.uid() to match against user_id foreign key
CREATE POLICY "Users own courses" 
ON courses 
FOR ALL 
USING (auth.uid() = user_id) 
WITH CHECK (auth.uid() = user_id);

-- ============================================================================
-- TABLE: materials
-- ============================================================================

-- Enable Row Level Security on materials table
ALTER TABLE materials ENABLE ROW LEVEL SECURITY;

-- Policy: Users can access materials only for courses they own
-- Uses subquery to verify course ownership through user_id
CREATE POLICY "Users own materials" 
ON materials 
FOR ALL 
USING (
    course_id IN (
        SELECT id FROM courses WHERE user_id = auth.uid()
    )
) 
WITH CHECK (
    course_id IN (
        SELECT id FROM courses WHERE user_id = auth.uid()
    )
);

-- ============================================================================
-- TABLE: chat_history
-- ============================================================================

-- Enable Row Level Security on chat_history table
ALTER TABLE chat_history ENABLE ROW LEVEL SECURITY;

-- Policy: Users can access chat history only for courses they own
-- Uses subquery to verify course ownership through user_id
CREATE POLICY "Users own chat history" 
ON chat_history 
FOR ALL 
USING (
    course_id IN (
        SELECT id FROM courses WHERE user_id = auth.uid()
    )
) 
WITH CHECK (
    course_id IN (
        SELECT id FROM courses WHERE user_id = auth.uid()
    )
);
