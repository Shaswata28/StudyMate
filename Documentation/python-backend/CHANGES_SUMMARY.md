# Database Setup Changes Summary

## 🎯 What Changed

### 1. Removed Unnecessary Complexity
- ❌ Removed direct `storage.objects` foreign key reference
- ✅ Added simple file path tracking instead

### 2. Added Storage Bucket Setup
- ✅ Created `course-materials` storage bucket
- ✅ Added storage policies for user isolation
- ✅ Configured file size limits (50MB)
- ✅ Restricted to allowed file types (PDF, DOCX, images, etc.)

### 3. Updated Materials Table
**Before**:
```sql
storage_object_id UUID REFERENCES storage.objects(id)
```

**After**:
```sql
file_path TEXT NOT NULL,      -- e.g., "user-123/course-abc/file.pdf"
file_type TEXT NOT NULL,      -- e.g., "application/pdf"
file_size BIGINT NOT NULL     -- File size in bytes
```

### 4. New Setup Scripts
- ✅ `setup_complete.py` - One-command complete setup
- ✅ `SETUP_NOW.md` - Quick start guide
- ✅ `migrations/001_setup_storage.sql` - Storage bucket creation

## 📁 New File Structure

### Storage Organization
```
course-materials/           ← Storage bucket
  {user_id}/               ← User folder
    {course_id}/           ← Course folder
      lecture-notes.pdf    ← Files
      assignment.docx
```

### Database Structure
```
materials table:
  - id: UUID
  - course_id: UUID (references courses)
  - name: "lecture-notes.pdf"
  - file_path: "user-123/course-abc/lecture-notes.pdf"
  - file_type: "application/pdf"
  - file_size: 1048576 (bytes)
```

## 🔐 Security Features

### Storage Policies
- ✅ Users can only upload to their own folder
- ✅ Users can only read their own files
- ✅ Users can only update/delete their own files
- ✅ Folder structure enforces user isolation

### Database RLS
- ✅ Users can only access their own academic profiles
- ✅ Users can only access their own preferences
- ✅ Users can only access their own courses
- ✅ Users can only access materials from their courses
- ✅ Users can only access chat history from their courses

## 🚀 How to Use

### 1. Run Setup
```bash
cd python-backend
python setup_complete.py --clean
```

### 2. Upload Files (Future Implementation)
```python
# Example: Upload a file
file_path = f"{user_id}/{course_id}/{filename}"

# Upload to Supabase Storage
supabase.storage.from_('course-materials').upload(
    file_path,
    file_data,
    file_options={'content-type': mime_type}
)

# Save metadata to database
material = {
    'course_id': course_id,
    'name': filename,
    'file_path': file_path,
    'file_type': mime_type,
    'file_size': file_size
}
supabase.table('materials').insert(material).execute()
```

### 3. Retrieve Files
```python
# Get material metadata from database
material = supabase.table('materials').select('*').eq('id', material_id).single().execute()

# Download file from storage
file_data = supabase.storage.from_('course-materials').download(material['file_path'])
```

## 📊 Tables Created

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `academic` | User academic info | grade[], semester_type, semester, subject[] |
| `personalized` | User preferences | prefs (JSONB) |
| `courses` | User courses | user_id, name |
| `materials` | File metadata | course_id, file_path, file_type, file_size |
| `chat_history` | AI conversations | course_id, history (JSONB[]), embedding (VECTOR) |

## 🎨 Vector Embeddings

The `chat_history` table includes vector embeddings for RAG:

```sql
embedding VECTOR(384)  -- 384-dimensional vector for semantic search
```

This enables:
- ✅ Semantic search of chat history
- ✅ Context retrieval for AI responses
- ✅ Similar conversation finding
- ✅ HNSW index for fast similarity search

## ✅ Verification Checklist

After running setup, verify:

- [ ] 5 tables exist in Supabase Table Editor
- [ ] `course-materials` bucket exists in Storage
- [ ] Storage policies are active (check Storage → Policies)
- [ ] RLS is enabled on all tables (check Table Editor → Policies)
- [ ] Vector extension is enabled (check Database → Extensions)

## 🔄 Migration Order

The setup runs migrations in this order:

1. **001_setup_storage.sql** - Create storage bucket and policies
2. **001_enable_extensions.sql** - Enable PostgreSQL extensions
3. **002_create_tables.sql** - Create all database tables
4. **003_create_rls_policies.sql** - Set up Row Level Security

## 🐛 Common Issues

### Issue: "vector extension does not exist"
**Solution**: Enable in Supabase dashboard → Database → Extensions → vector

### Issue: "bucket already exists"
**Solution**: This is fine! The bucket is already created.

### Issue: "relation already exists"
**Solution**: Use `--clean` flag to drop and recreate tables.

## 📚 Related Files

- **Setup script**: `setup_complete.py`
- **Quick guide**: `SETUP_NOW.md`
- **Detailed guide**: `MIGRATION_GUIDE.md`
- **Migrations**: `migrations/*.sql`
- **Schemas**: `models/schemas.py`

## 🎉 What's Next

After setup:

1. ✅ Database is ready
2. ✅ Storage is configured
3. ✅ Security is enabled

You can now:
- Implement file upload endpoints
- Implement material management endpoints
- Implement chat history endpoints
- Test the complete flow

---

**Questions?** Check `SETUP_NOW.md` for quick start or `MIGRATION_GUIDE.md` for details.
