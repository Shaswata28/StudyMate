-- Migration: Setup Storage Buckets
-- Description: Create Supabase Storage buckets for materials and configure policies
-- Requirements: 6.1, 6.5

-- ============================================================================
-- STORAGE BUCKET: course-materials
-- ============================================================================

-- Create storage bucket for course materials (PDFs, documents, etc.)
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'course-materials',
    'course-materials',
    false, -- Private bucket (requires authentication)
    52428800, -- 50MB file size limit
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

-- ============================================================================
-- STORAGE POLICIES: course-materials bucket
-- ============================================================================

-- Policy: Users can upload files to their own folders
CREATE POLICY "Users can upload to own folder"
ON storage.objects
FOR INSERT
TO authenticated
WITH CHECK (
    bucket_id = 'course-materials' AND
    (storage.foldername(name))[1] = auth.uid()::text
);

-- Policy: Users can read their own files
CREATE POLICY "Users can read own files"
ON storage.objects
FOR SELECT
TO authenticated
USING (
    bucket_id = 'course-materials' AND
    (storage.foldername(name))[1] = auth.uid()::text
);

-- Policy: Users can update their own files
CREATE POLICY "Users can update own files"
ON storage.objects
FOR UPDATE
TO authenticated
USING (
    bucket_id = 'course-materials' AND
    (storage.foldername(name))[1] = auth.uid()::text
)
WITH CHECK (
    bucket_id = 'course-materials' AND
    (storage.foldername(name))[1] = auth.uid()::text
);

-- Policy: Users can delete their own files
CREATE POLICY "Users can delete own files"
ON storage.objects
FOR DELETE
TO authenticated
USING (
    bucket_id = 'course-materials' AND
    (storage.foldername(name))[1] = auth.uid()::text
);

-- ============================================================================
-- NOTES
-- ============================================================================

-- File organization structure:
-- course-materials/
--   {user_id}/
--     {course_id}/
--       {file_name}
--
-- Example: course-materials/123e4567-e89b-12d3-a456-426614174000/course-abc/lecture-notes.pdf

-- The storage policies ensure:
-- 1. Users can only upload to folders matching their user ID
-- 2. Users can only access files in their own folders
-- 3. Files are organized by user and course for easy management
-- 4. File size is limited to 50MB per file
-- 5. Only allowed file types can be uploaded

