# Update Embedding Dimension Migration Guide

## Overview

This migration updates the `embedding` column in the `materials` table from **VECTOR(384)** to **VECTOR(1024)** to match the output dimension of the `mxbai-embed-large` model used by the AI Brain service.

## ⚠️ Important Notes

**This migration will:**
- ✅ Change the vector dimension from 384 to 1024
- ✅ Recreate the HNSW index for the new dimension
- ⚠️ **Clear all existing embeddings** (they must be regenerated)
- ⚠️ **Reset all materials to `processing_status = 'pending'`**

**After this migration:**
- All materials will need to be reprocessed to generate new 1024-dim embeddings
- The background processing service will automatically reprocess pending materials
- Semantic search will not work until materials are reprocessed

## Prerequisites

- ✅ Backup your database (recommended)
- ✅ Ensure the `vector` extension is enabled
- ✅ Verify you have appropriate database permissions
- ✅ Plan for downtime if you have many materials (they'll need reprocessing)

## Execution Methods

### Method 1: Supabase Dashboard (Recommended)

1. **Open Supabase Dashboard**
   - Navigate to https://app.supabase.com
   - Select your project
   - Go to **SQL Editor**

2. **Run the Migration**
   - Copy the contents of `006_update_embedding_dimension.sql`
   - Paste into the SQL Editor
   - Click **Run**

3. **Verify Success**
   - Check the verification query results at the bottom
   - Confirm embedding column is now VECTOR(1024)
   - Confirm index was recreated
   - Confirm materials are set to 'pending'

### Method 2: psql Command Line

```bash
# Connect to your Supabase database
psql "postgresql://postgres:[PASSWORD]@[PROJECT_REF].supabase.co:5432/postgres"

# Run the migration
\i python-backend/migrations/006_update_embedding_dimension.sql
```

### Method 3: Copy-Paste SQL

If you prefer to run the SQL directly, here's the complete script:

```sql
-- Drop the existing HNSW index
DROP INDEX IF EXISTS idx_materials_embedding;

-- Alter the embedding column to VECTOR(1024)
ALTER TABLE materials 
ALTER COLUMN embedding TYPE VECTOR(1024);

-- Clear existing embeddings and reset to pending
UPDATE materials 
SET 
    embedding = NULL,
    processing_status = 'pending',
    processed_at = NULL,
    error_message = NULL
WHERE embedding IS NOT NULL;

-- Recreate the HNSW index
CREATE INDEX idx_materials_embedding 
ON materials 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

## Verification

After running the migration, verify it was successful:

### 1. Check Column Type

```sql
SELECT 
    column_name, 
    data_type,
    udt_name
FROM information_schema.columns 
WHERE table_name = 'materials' 
    AND column_name = 'embedding';
```

**Expected result:** `udt_name` should show `vector` with dimension 1024

### 2. Check Index

```sql
SELECT 
    indexname, 
    indexdef 
FROM pg_indexes 
WHERE tablename = 'materials' 
    AND indexname = 'idx_materials_embedding';
```

**Expected result:** Index exists with `vector_cosine_ops`

### 3. Check Processing Status

```sql
SELECT 
    processing_status, 
    COUNT(*) as count,
    COUNT(embedding) as has_embedding
FROM materials 
GROUP BY processing_status;
```

**Expected result:** All materials should have `processing_status = 'pending'` and `has_embedding = 0`

## Post-Migration Steps

### 1. Restart Background Processing Service

If your backend is running, restart it to ensure the processing service picks up pending materials:

```bash
# Stop the backend
# Restart the backend
cd python-backend
python main.py
```

### 2. Monitor Reprocessing

Check the processing status periodically:

```sql
SELECT 
    processing_status,
    COUNT(*) as count
FROM materials
GROUP BY processing_status
ORDER BY processing_status;
```

You should see materials transition:
- `pending` → `processing` → `completed`

### 3. Check for Errors

If any materials fail to process:

```sql
SELECT 
    id,
    name,
    error_message,
    processing_status
FROM materials
WHERE processing_status = 'failed'
ORDER BY updated_at DESC;
```

### 4. Verify Embeddings

Once processing completes, verify embeddings are 1024-dimensional:

```sql
SELECT 
    id,
    name,
    array_length(embedding::float[], 1) as embedding_dimension,
    processing_status
FROM materials
WHERE embedding IS NOT NULL
LIMIT 5;
```

**Expected result:** `embedding_dimension = 1024`

## Rollback

⚠️ **Warning:** Rollback will revert to 384 dimensions and clear embeddings again!

If you need to rollback:

```sql
-- Drop the index
DROP INDEX IF EXISTS idx_materials_embedding;

-- Revert to VECTOR(384)
ALTER TABLE materials 
ALTER COLUMN embedding TYPE VECTOR(384);

-- Clear embeddings and reset to pending
UPDATE materials 
SET 
    embedding = NULL,
    processing_status = 'pending',
    processed_at = NULL,
    error_message = NULL
WHERE embedding IS NOT NULL;

-- Recreate index for 384 dimensions
CREATE INDEX idx_materials_embedding 
ON materials 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

## Troubleshooting

### Error: "cannot alter type of a column used by a view or rule"

**Solution:** Drop dependent views first, run migration, then recreate views.

### Error: "index 'idx_materials_embedding' does not exist"

**Solution:** This is fine - the index might not have been created yet. Continue with the migration.

### Materials Not Reprocessing

**Checklist:**
1. ✅ Verify backend service is running
2. ✅ Check AI Brain service is running on port 8001
3. ✅ Verify Ollama has `mxbai-embed-large` model installed
4. ✅ Check backend logs for errors
5. ✅ Manually trigger processing if needed

### Slow Reprocessing

If you have many materials, reprocessing can take time:
- Each material requires OCR + embedding generation
- OCR can take 30-60 seconds per PDF
- Embedding generation is fast (~1-2 seconds)
- Processing happens sequentially in the background

**Estimate:** ~1 minute per material on average

## Impact Assessment

### Small Projects (< 10 materials)
- **Downtime:** ~10 minutes
- **Impact:** Minimal - quick reprocessing

### Medium Projects (10-50 materials)
- **Downtime:** ~30-60 minutes
- **Impact:** Moderate - plan accordingly

### Large Projects (> 50 materials)
- **Downtime:** Several hours
- **Impact:** Significant - consider running during off-hours

## Why This Change?

The `mxbai-embed-large` model outputs **1024-dimensional** embeddings, which provide:
- ✅ Better semantic understanding
- ✅ More accurate similarity search
- ✅ Improved RAG performance
- ✅ Compatibility with the AI Brain service

The previous 384-dimensional embeddings were from a different model and are incompatible.

## Related Files

- **Migration Script:** `python-backend/migrations/006_update_embedding_dimension.sql`
- **Original Migration:** `python-backend/migrations/005_add_material_ocr_embedding.sql`
- **Design Doc:** `.kiro/specs/material-ocr-embedding/design.md`
- **Processing Service:** `python-backend/services/material_processing_service.py`

## Support

If you encounter issues:
1. Check the verification queries in the migration script
2. Review backend logs for processing errors
3. Verify AI Brain service is running: `curl http://localhost:8001/`
4. Check Ollama models: `ollama list`

---

**Migration Status:** Ready to Execute  
**Estimated Time:** 5 minutes + reprocessing time  
**Risk Level:** Medium (requires reprocessing all materials)
