-- Migration: Rollback Database Schema
-- Description: Safely revert all schema changes by dropping tables, policies, indexes,
--              and functions in reverse dependency order
-- Requirements: 8.5

-- ============================================================================
-- DROP RLS POLICIES
-- ============================================================================

-- Drop policies in any order (no dependencies between policies)
DROP POLICY IF EXISTS "Users own chat history" ON chat_history;
DROP POLICY IF EXISTS "Users own materials" ON materials;
DROP POLICY IF EXISTS "Users own courses" ON courses;
DROP POLICY IF EXISTS "Users edit own prefs" ON personalized;
DROP POLICY IF EXISTS "Users edit own academic data" ON academic;

-- ============================================================================
-- DROP INDEXES
-- ============================================================================

-- Drop custom indexes (primary key indexes are dropped with tables)
-- Vector similarity index
DROP INDEX IF EXISTS chat_history_embedding_idx;

-- Chat history indexes
DROP INDEX IF EXISTS idx_chat_history_course_id;

-- Materials indexes
DROP INDEX IF EXISTS idx_materials_storage_object_id;
DROP INDEX IF EXISTS idx_materials_course_id;

-- Courses indexes
DROP INDEX IF EXISTS idx_courses_user_id;

-- Personalized indexes
DROP INDEX IF EXISTS idx_personalized_prefs;

-- Academic indexes
DROP INDEX IF EXISTS idx_academic_subject;
DROP INDEX IF EXISTS idx_academic_grade;

-- ============================================================================
-- DROP TABLES
-- ============================================================================

-- Drop tables in reverse dependency order (child tables before parent tables)
-- This ensures foreign key constraints don't prevent deletion

-- Drop chat_history (depends on courses)
DROP TABLE IF EXISTS chat_history CASCADE;

-- Drop materials (depends on courses and storage.objects)
DROP TABLE IF EXISTS materials CASCADE;

-- Drop courses (depends on auth.users)
DROP TABLE IF EXISTS courses CASCADE;

-- Drop personalized (depends on auth.users)
DROP TABLE IF EXISTS personalized CASCADE;

-- Drop academic (depends on auth.users)
DROP TABLE IF EXISTS academic CASCADE;

-- Note: We do NOT drop auth.users as it's managed by Supabase Auth

-- ============================================================================
-- DROP FUNCTIONS
-- ============================================================================

-- Drop the trigger function for automatic timestamp updates
DROP FUNCTION IF EXISTS update_updated_at() CASCADE;

-- ============================================================================
-- DROP EXTENSIONS (OPTIONAL)
-- ============================================================================

-- Note: Extensions are typically NOT dropped during rollback as they may be
-- used by other databases or schemas. Uncomment the following lines only if
-- you're certain no other tables or applications depend on these extensions.

-- DROP EXTENSION IF EXISTS "pg_trgm";
-- DROP EXTENSION IF EXISTS "vector";
-- DROP EXTENSION IF EXISTS "pgcrypto";
-- DROP EXTENSION IF EXISTS "uuid-ossp";
