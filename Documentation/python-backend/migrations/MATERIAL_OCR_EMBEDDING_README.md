# Material OCR and Embedding Migration Guide

## Overview

This migration adds OCR (Optical Character Recognition) and vector embedding capabilities to the materials table, enabling:

- **Automatic text extraction** from uploaded PDFs and images
- **Semantic search** using vector embeddings (find materials by meaning, not just keywords)
- **Processing status tracking** (pending → processing → completed/failed)
- **Error handling** with detailed error messages

## Requirements Addressed

- **Requirement 1.1**: Store materials with processing metadata
- **Requirement 9.1**: Add columns for extracted_text, embedding, processing_status, processed_at, error_message
- **Requirement 9.2**: Use VECTOR(384) data type for embeddings
- **Requirement 9.3**: Create HNSW index for fast similarity search
- **Requirement 9.4**: Create index on processing_status for efficient filtering

## Prerequisites

Before running this migration, ensure:

1. ✅ You have access to your Supabase project dashboard
2. ✅ The `vector` extension is enabled (should already be enabled from previous migrations)
3. ✅ The `materials` table exists
4. ✅ You have appropriate database permissions

## Migration Files

This migration includes three files:

1. **`005_add_material_ocr_embedding.sql`** - Concise migration script for automated tools
2. **`MATERIAL_OCR_EMBEDDING_MIGRATION.sql`** - Comprehensive script with verification queries (recommended for manual execution)
3. **`MATERIAL_OCR_EMBEDDING_README.md`** - This guide

## Execution Methods

### Method 1: Supabase Dashboard (Recommended)

This is the easiest method for manual execution:

1. **Open Supabase Dashboard**
   - Navigate to your project at https://app.supabase.com
   - Go to **SQL Editor** in the left sidebar

2. **Copy the Migration Script**
   - Open `MATERIAL_OCR_EMBEDDING_MIGRATION.sql`
   - Copy the entire contents

3. **Execute the Script**
   - Paste into the SQL Editor
   - Click **Run** button
   - Wait for execution to complete

4. **Verify Success**
   - Scroll down to see the verification query results
   - You should see the new columns listed
   - Check that indexes were created successfully

### Method 2: Python Migration Script

If you have the Python backend set up:

```bash
cd python-backend
python scripts/run_migrations.py
```

This will automatically run all pending migrations in order.

### Method 3: psql Command Line

If you prefer command-line tools:

```bash
# Connect to your Supabase database
psql "postgresql://postgres:[YOUR_PASSWORD]@[YOUR_PROJECT_REF].supabase.co:5432/postgres"

# Run the migration
\i migrations/005_add_material_ocr_embedding.sql
```

## What This Migration Does

### 1. Adds New Columns

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `extracted_text` | TEXT | NULL | Text content extracted from PDFs/images via OCR |
| `embedding` | VECTOR(384) | NULL | 384-dimensional vector for semantic search |
| `processing_status` | TEXT | 'pending' | Status: pending, processing, completed, failed |
| `processed_at` | TIMESTAMPTZ | NULL | Timestamp when processing completed |
| `error_message` | TEXT | NULL | Error details if processing failed |

### 2. Creates Indexes

- **`idx_materials_processing_status`** - B-tree index for filtering by status
  - Enables fast queries: `WHERE processing_status = 'pending'`
  
- **`idx_materials_embedding`** - HNSW index for vector similarity search
  - Enables fast semantic search: `ORDER BY embedding <=> query_vector LIMIT 10`
  - Uses cosine distance for similarity measurement

### 3. Adds Constraints

- **`materials_processing_status_check`** - Ensures status is one of: pending, processing, completed, failed

### 4. Updates Existing Data

- Sets all existing materials to `processing_status = 'pending'`
- This ensures they'll be processed by the background job system

## Verification

After running the migration, verify it was successful:

### Check New Columns

```sql
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
```

Expected result: 5 rows showing the new columns

### Check Indexes

```sql
SELECT 
    indexname, 
    indexdef 
FROM pg_indexes 
WHERE tablename = 'materials' 
    AND indexname IN (
        'idx_materials_processing_status', 
        'idx_materials_embedding'
    );
```

Expected result: 2 rows showing both indexes

### Check Processing Status

```sql
SELECT 
    processing_status, 
    COUNT(*) as count 
FROM materials 
GROUP BY processing_status;
```

Expected result: All existing materials should show `pending` status

## Rollback

If you need to undo this migration, use the rollback script included at the bottom of `MATERIAL_OCR_EMBEDDING_MIGRATION.sql`:

⚠️ **WARNING**: This will delete all OCR and embedding data!

```sql
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
```

## Next Steps

After successfully running this migration:

1. **Deploy Backend Code**
   - Implement the OCR and embedding processing service
   - Deploy the background job system
   - Configure AI provider (Gemini API for Phase 1)

2. **Test Processing**
   - Upload a test PDF or image
   - Verify status changes: pending → processing → completed
   - Check that `extracted_text` and `embedding` are populated

3. **Test Semantic Search**
   - Use the search endpoint to query materials by meaning
   - Verify results are ranked by relevance

4. **Monitor Processing**
   - Check for materials stuck in 'processing' status
   - Review error_message for any failed materials
   - Set up alerts for processing failures

## Troubleshooting

### Error: "extension 'vector' does not exist"

**Solution**: Enable the vector extension first:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Error: "column already exists"

**Solution**: The migration has already been run. Check if columns exist:

```sql
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'materials' AND column_name = 'embedding';
```

### Error: "permission denied"

**Solution**: Ensure you're using a role with sufficient permissions. In Supabase, use the service role key or postgres user.

### Materials Not Processing

**Checklist**:
1. Verify materials have `processing_status = 'pending'`
2. Check that background job system is running
3. Review application logs for errors
4. Verify AI provider credentials are configured

## Schema Diagram

```
materials table (after migration)
├── id (UUID, PK)
├── course_id (UUID, FK → courses)
├── name (TEXT)
├── file_path (TEXT)
├── file_type (TEXT)
├── file_size (BIGINT)
├── extracted_text (TEXT) ← NEW
├── embedding (VECTOR(384)) ← NEW
├── processing_status (TEXT) ← NEW [pending|processing|completed|failed]
├── processed_at (TIMESTAMPTZ) ← NEW
├── error_message (TEXT) ← NEW
├── created_at (TIMESTAMPTZ)
└── updated_at (TIMESTAMPTZ)

Indexes:
├── materials_pkey (PRIMARY KEY on id)
├── idx_materials_course_id (B-tree on course_id)
├── idx_materials_file_path (B-tree on file_path)
├── idx_materials_processing_status (B-tree on processing_status) ← NEW
└── idx_materials_embedding (HNSW on embedding) ← NEW
```

## Support

If you encounter issues:

1. Check the verification queries in the migration script
2. Review Supabase logs in the dashboard
3. Consult the main database schema documentation: `docs/database-schema.md`
4. Check the design document: `.kiro/specs/material-ocr-embedding/design.md`

## Related Documentation

- **Design Document**: `.kiro/specs/material-ocr-embedding/design.md`
- **Requirements**: `.kiro/specs/material-ocr-embedding/requirements.md`
- **Database Schema**: `docs/database-schema.md`
- **API Documentation**: `python-backend/API_ENDPOINTS.md`
