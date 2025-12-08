# Setup Your Database Now

## 🚀 Quick Setup (2 commands)

Since you've already added `SUPABASE_DB_PASSWORD` to your `.env` file, you're ready to go!

### Option 1: Clean Setup (Recommended)

This will remove any unnecessary tables and create a fresh setup:

```bash
cd python-backend
python setup_complete.py --clean
```

### Option 2: Keep Existing Tables

This will only create missing tables:

```bash
cd python-backend
python setup_complete.py
```

## 📋 What Gets Created

### Storage Bucket
- **course-materials** - For PDFs, documents, images
  - 50MB file size limit
  - Organized as: `{user_id}/{course_id}/{filename}`
  - Private (requires authentication)

### Database Tables
1. **academic** - User academic profiles
2. **personalized** - User preferences (JSONB)
3. **courses** - User courses
4. **materials** - File metadata (links to storage)
5. **chat_history** - AI conversations with vector embeddings

### Security
- Row Level Security (RLS) on all tables
- Users can only access their own data
- Storage policies enforce user isolation

## ✅ Verify It Worked

After running setup, check:

1. **In Terminal** - You should see:
   ```
   ✓ Created tables:
     - academic
     - personalized
     - courses
     - materials
     - chat_history
   ```

2. **In Supabase Dashboard**:
   - Go to **Table Editor** → See all 5 tables
   - Go to **Storage** → See `course-materials` bucket

## 🔧 If You See Errors

### "vector extension does not exist"

**Solution**: Enable it in Supabase dashboard:
1. Go to **Database** → **Extensions**
2. Search for "vector"
3. Click **Enable**
4. Run setup again

### "relation already exists"

This means tables already exist. Options:
1. Use `--clean` flag to start fresh
2. Or skip (tables are already there)

### "permission denied"

Check your `SUPABASE_DB_PASSWORD` is correct in `.env`

## 🎯 What Changed from Before

### Removed
- ❌ `storage_object_id` reference (was causing issues)

### Added
- ✅ Storage bucket with proper policies
- ✅ `file_path`, `file_type`, `file_size` fields in materials table
- ✅ Automatic cleanup of unnecessary tables

### Improved
- ✅ Better file organization in storage
- ✅ Clearer migration structure
- ✅ One-command setup

## 📁 File Structure After Setup

```
Storage (course-materials bucket):
  user-123/
    course-abc/
      lecture-notes.pdf
      assignment.docx
    course-xyz/
      chapter1.pdf

Database (materials table):
  id: uuid
  course_id: course-abc
  name: "lecture-notes.pdf"
  file_path: "user-123/course-abc/lecture-notes.pdf"
  file_type: "application/pdf"
  file_size: 1048576
```

## 🚀 Next Steps

After setup completes:

1. **Test the backend**:
   ```bash
   python main.py
   ```

2. **Test authentication**:
   ```bash
   curl -X POST http://localhost:8000/api/auth/signup \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"password123"}'
   ```

3. **Use the frontend**:
   - Navigate to `/signup`
   - Create account
   - Fill academic profile
   - Complete questionnaire
   - Start using the app!

## 📚 Additional Files

- **Detailed guide**: `MIGRATION_GUIDE.md`
- **Storage setup**: `migrations/001_setup_storage.sql`
- **Table creation**: `migrations/002_create_tables.sql`
- **RLS policies**: `migrations/003_create_rls_policies.sql`

---

**Ready?** Run: `python setup_complete.py --clean`
