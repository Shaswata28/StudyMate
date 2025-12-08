# Migration 005 - Quick Reference Card

## 🎯 What This Does

Adds OCR and vector embedding support to materials table for semantic search and RAG.

## ⚡ Quick Execute

### Option 1: Supabase Dashboard (Easiest)
1. Open: https://app.supabase.com → Your Project → SQL Editor
2. Copy: `MATERIAL_OCR_EMBEDDING_MIGRATION.sql`
3. Paste & Run
4. Done! ✅

### Option 2: Command Line
```bash
cd python-backend
python scripts/run_migrations.py
```

## 📊 What Gets Added

| Column | Type | Purpose |
|--------|------|---------|
| `extracted_text` | TEXT | OCR text from PDFs/images |
| `embedding` | VECTOR(384) | Semantic search vector |
| `processing_status` | TEXT | pending/processing/completed/failed |
| `processed_at` | TIMESTAMPTZ | When processing finished |
| `error_message` | TEXT | Error details if failed |

## 🔍 Quick Verify

```sql
-- Check columns exist
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'materials' AND column_name = 'embedding';

-- Should return: embedding
```

## 📁 Files Created

- ✅ `005_add_material_ocr_embedding.sql` - Migration script
- ✅ `MATERIAL_OCR_EMBEDDING_MIGRATION.sql` - Full version with verification
- ✅ `MATERIAL_OCR_EMBEDDING_README.md` - Complete guide
- ✅ `MIGRATION_005_SUMMARY.md` - Summary
- ✅ `SCHEMA_CHANGES_DIAGRAM.md` - Visual guide
- ✅ `QUICK_REFERENCE.md` - This file

## 🚨 Troubleshooting

**Error: "extension 'vector' does not exist"**
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

**Error: "column already exists"**
→ Migration already run, you're good!

**Need to rollback?**
→ See rollback script in `MATERIAL_OCR_EMBEDDING_MIGRATION.sql`

## 📋 Requirements Met

- ✅ Requirement 1.1 - Store materials with processing metadata
- ✅ Requirement 9.1 - Add new columns
- ✅ Requirement 9.2 - VECTOR(384) data type
- ✅ Requirement 9.3 - HNSW index for similarity search
- ✅ Requirement 9.4 - Index on processing_status

## ⏭️ Next Task

**Task 2**: Create AI provider abstraction layer

## 📚 Full Documentation

- **Complete Guide**: `MATERIAL_OCR_EMBEDDING_README.md`
- **Visual Diagrams**: `SCHEMA_CHANGES_DIAGRAM.md`
- **Detailed Summary**: `MIGRATION_005_SUMMARY.md`
- **Design Doc**: `.kiro/specs/material-ocr-embedding/design.md`

## 💡 Key Features Enabled

- 🔍 Semantic search (find by meaning)
- 📄 Automatic OCR (extract text from PDFs/images)
- 🤖 RAG support (AI chat with material context)
- 📊 Processing status tracking
- ❌ Error handling and logging

---

**Status**: ✅ Ready to Execute  
**Estimated Time**: < 1 minute  
**Risk Level**: Low (backward compatible)
