# Materials Table Schema Changes - Visual Guide

## Before Migration (Original Schema)

```
┌─────────────────────────────────────────────────────────────┐
│                     materials table                         │
├─────────────────────────────────────────────────────────────┤
│ id                UUID (PK)                                  │
│ course_id         UUID (FK → courses)                       │
│ name              TEXT                                       │
│ file_path         TEXT                                       │
│ file_type         TEXT                                       │
│ file_size         BIGINT                                     │
│ created_at        TIMESTAMPTZ                                │
│ updated_at        TIMESTAMPTZ                                │
└─────────────────────────────────────────────────────────────┘

Indexes:
  • materials_pkey (PRIMARY KEY on id)
  • idx_materials_course_id (B-tree on course_id)
  • idx_materials_file_path (B-tree on file_path)
```

## After Migration (Enhanced Schema)

```
┌─────────────────────────────────────────────────────────────┐
│                     materials table                         │
├─────────────────────────────────────────────────────────────┤
│ id                UUID (PK)                                  │
│ course_id         UUID (FK → courses)                       │
│ name              TEXT                                       │
│ file_path         TEXT                                       │
│ file_type         TEXT                                       │
│ file_size         BIGINT                                     │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 🆕 NEW COLUMNS FOR OCR & EMBEDDING                      │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ extracted_text    TEXT                                  │ │
│ │ embedding         VECTOR(384)                           │ │
│ │ processing_status TEXT (pending/processing/...)         │ │
│ │ processed_at      TIMESTAMPTZ                           │ │
│ │ error_message     TEXT                                  │ │
│ └─────────────────────────────────────────────────────────┘ │
│ created_at        TIMESTAMPTZ                                │
│ updated_at        TIMESTAMPTZ                                │
└─────────────────────────────────────────────────────────────┘

Indexes:
  • materials_pkey (PRIMARY KEY on id)
  • idx_materials_course_id (B-tree on course_id)
  • idx_materials_file_path (B-tree on file_path)
  • 🆕 idx_materials_processing_status (B-tree on processing_status)
  • 🆕 idx_materials_embedding (HNSW on embedding)
```

## Processing Status Flow

```
┌──────────┐
│ UPLOAD   │
│ Material │
└────┬─────┘
     │
     ▼
┌─────────────────┐
│ Status: PENDING │ ← Initial state after upload
│ extracted_text: │   (processing_status = 'pending')
│ NULL            │
│ embedding: NULL │
└────┬────────────┘
     │
     │ Background Job Starts
     ▼
┌──────────────────┐
│ Status:          │ ← Processing in progress
│ PROCESSING       │   (processing_status = 'processing')
│ extracted_text:  │
│ NULL             │
│ embedding: NULL  │
└────┬─────────────┘
     │
     │ OCR + Embedding Generation
     │
     ├─────────────┬──────────────┐
     │ SUCCESS     │ FAILURE      │
     ▼             ▼              │
┌──────────────┐  ┌──────────────┴────┐
│ Status:      │  │ Status: FAILED    │
│ COMPLETED    │  │ extracted_text:   │
│ extracted_   │  │ NULL or partial   │
│ text: "..."  │  │ embedding: NULL   │
│ embedding:   │  │ error_message:    │
│ [0.1, 0.2,   │  │ "OCR failed: ..." │
│  ..., 0.9]   │  │ processed_at:     │
│ processed_at:│  │ 2024-12-03...     │
│ 2024-12-03...│  └───────────────────┘
└──────────────┘
     │
     │ Ready for Semantic Search
     ▼
┌──────────────────────────────────┐
│ Semantic Search Enabled          │
│ • Find by meaning, not keywords  │
│ • RAG-enabled chat               │
│ • Similarity scoring             │
└──────────────────────────────────┘
```

## Column Details

### 🔤 extracted_text (TEXT)

**Purpose**: Stores text content extracted from PDFs and images via OCR

**Example Values**:
```
"Chapter 1: Introduction to Machine Learning
Machine learning is a subset of artificial intelligence..."

"Lecture Notes - Week 3
Topics covered:
1. Neural Networks
2. Backpropagation
3. Gradient Descent"
```

**NULL when**: 
- Processing not yet started
- Processing failed
- File contains no extractable text

---

### 🔢 embedding (VECTOR(384))

**Purpose**: 384-dimensional vector representation for semantic search

**Example Value**:
```
[0.123, -0.456, 0.789, ..., 0.234]  // 384 numbers
```

**How it works**:
- Generated from extracted_text using AI embedding models
- Enables "find similar materials" functionality
- Used for RAG (Retrieval Augmented Generation) in chat

**NULL when**:
- Processing not yet started
- Processing failed
- No text to embed (empty extracted_text)

---

### 📊 processing_status (TEXT)

**Purpose**: Tracks the current state of OCR and embedding processing

**Valid Values**:

| Status | Meaning | Next State |
|--------|---------|------------|
| `pending` | Uploaded, awaiting processing | → `processing` |
| `processing` | OCR/embedding in progress | → `completed` or `failed` |
| `completed` | Successfully processed | (final state) |
| `failed` | Processing error occurred | → `pending` (retry) |

**Constraint**: Must be one of the four values above

---

### ⏰ processed_at (TIMESTAMPTZ)

**Purpose**: Records when processing completed (success or failure)

**Example Values**:
```
2024-12-03 14:30:45.123456+00
2024-12-03 15:22:10.987654+00
```

**NULL when**: Processing not yet complete (pending or processing)

---

### ❌ error_message (TEXT)

**Purpose**: Stores detailed error information if processing fails

**Example Values**:
```
"OCR failed: File is corrupted or unreadable"
"Embedding generation timeout after 300 seconds"
"Gemini API error: Rate limit exceeded"
"Invalid file format: Expected PDF or image"
```

**NULL when**: 
- No error occurred
- Processing not yet attempted
- Processing completed successfully

## Index Performance

### idx_materials_processing_status (B-tree)

**Optimizes queries like**:
```sql
-- Find all pending materials for background processing
SELECT * FROM materials WHERE processing_status = 'pending';

-- Count failed materials
SELECT COUNT(*) FROM materials WHERE processing_status = 'failed';

-- Get completed materials for a course
SELECT * FROM materials 
WHERE course_id = '...' AND processing_status = 'completed';
```

**Performance**: O(log n) lookup time

---

### idx_materials_embedding (HNSW)

**Optimizes queries like**:
```sql
-- Find top 5 most similar materials to a query
SELECT id, name, embedding <=> query_vector AS distance
FROM materials
WHERE course_id = '...' AND embedding IS NOT NULL
ORDER BY embedding <=> query_vector
LIMIT 5;

-- Semantic search with threshold
SELECT * FROM materials
WHERE course_id = '...' 
  AND embedding <=> query_vector < 0.5  -- similarity threshold
ORDER BY embedding <=> query_vector;
```

**Performance**: Approximate nearest neighbor search in O(log n) time

**Distance Operators**:
- `<=>` : Cosine distance (recommended for semantic similarity)
- `<->` : Euclidean distance
- `<#>` : Inner product

## Storage Impact

### Disk Space Estimates

For a material with:
- **extracted_text**: ~10 KB (typical document)
- **embedding**: 384 floats × 4 bytes = 1.5 KB
- **processing_status**: ~10 bytes
- **processed_at**: 8 bytes
- **error_message**: ~100 bytes (when present)

**Total per material**: ~11.6 KB additional storage

**For 1,000 materials**: ~11.6 MB
**For 10,000 materials**: ~116 MB
**For 100,000 materials**: ~1.16 GB

### Index Space

- **B-tree index** (processing_status): ~1-2% of table size
- **HNSW index** (embedding): ~10-20% of embedding column size

## Query Examples

### Check Processing Status

```sql
-- Get processing status summary
SELECT 
    processing_status,
    COUNT(*) as count,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as percentage
FROM materials
GROUP BY processing_status;
```

### Find Materials Ready for Search

```sql
-- Get all materials with embeddings (ready for semantic search)
SELECT id, name, file_type, processed_at
FROM materials
WHERE processing_status = 'completed' 
  AND embedding IS NOT NULL
ORDER BY processed_at DESC;
```

### Semantic Search

```sql
-- Find similar materials (assuming you have a query_embedding)
SELECT 
    m.id,
    m.name,
    m.file_type,
    m.embedding <=> :query_embedding AS similarity_score,
    LEFT(m.extracted_text, 200) AS excerpt
FROM materials m
WHERE m.course_id = :course_id
  AND m.embedding IS NOT NULL
ORDER BY m.embedding <=> :query_embedding
LIMIT 3;
```

### Error Analysis

```sql
-- Find all failed materials with error details
SELECT 
    name,
    file_type,
    error_message,
    processed_at
FROM materials
WHERE processing_status = 'failed'
ORDER BY processed_at DESC;
```

### Processing Queue

```sql
-- Get next batch of materials to process
SELECT id, name, file_path, file_type
FROM materials
WHERE processing_status = 'pending'
ORDER BY created_at ASC
LIMIT 10;
```

## Migration Safety

### Backward Compatibility

✅ **Safe for existing data**:
- All new columns are nullable
- Default value for processing_status is 'pending'
- Existing queries continue to work
- No data loss

✅ **Safe for existing code**:
- Existing API endpoints continue to work
- New columns are optional in responses
- Gradual rollout possible

### Rollback Safety

✅ **Can be rolled back**:
- Rollback script provided
- No foreign key dependencies
- Indexes can be dropped independently

⚠️ **Data loss on rollback**:
- All extracted text will be lost
- All embeddings will be lost
- Processing status history will be lost

## Next Steps After Migration

1. ✅ Run migration in Supabase
2. ⏭️ Implement AI provider abstraction (Task 2)
3. ⏭️ Implement Gemini OCR provider (Task 3)
4. ⏭️ Create background processing service (Task 4)
5. ⏭️ Update upload endpoint to queue processing (Task 6)
6. ⏭️ Implement semantic search endpoint (Task 9)
7. ⏭️ Integrate RAG into chat (Task 10)

---

**Migration File**: `005_add_material_ocr_embedding.sql`  
**Documentation**: `MATERIAL_OCR_EMBEDDING_README.md`  
**Summary**: `MIGRATION_005_SUMMARY.md`
