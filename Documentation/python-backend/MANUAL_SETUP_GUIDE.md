# Manual Setup Guide - Run SQL in Supabase

This is the easiest way to set up your database!

## 🚀 Quick Steps

### 1. Open Supabase SQL Editor

Go to: https://supabase.com/dashboard/project/fupupzbizwmxtcrftdhy/editor

### 2. Copy the SQL

Open the file: `python-backend/COMPLETE_SETUP.sql`

Copy the entire contents (Ctrl+A, Ctrl+C)

### 3. Paste and Run

1. Paste the SQL into the Supabase SQL Editor
2. Click the **"Run"** button (or press Ctrl+Enter)
3. Wait for it to complete (~5-10 seconds)

### 4. Verify

Check that you see:
- ✅ Success message
- ✅ No errors

Then go to **Table Editor** and verify you see these 5 tables:
- academic
- personalized
- courses
- materials
- chat_history

---

## 📋 What Gets Created

### Tables (5)
1. **academic** - User academic profiles
2. **personalized** - User preferences (JSONB)
3. **courses** - User courses
4. **materials** - File metadata
5. **chat_history** - AI conversations

### Storage Bucket (1)
- **course-materials** - For PDFs, documents, images (50MB limit)

### Security
- Row Level Security (RLS) on all tables
- Users can only access their own data
- Storage policies enforce user isolation

### Performance
- Indexes on all foreign keys
- GIN indexes for arrays and JSONB
- HNSW index for vector similarity search

---

## ⚠️ If You See Errors

### "extension vector does not exist"

**Solution**: Enable the vector extension first
1. Go to **Database** → **Extensions**
2. Search for "vector"
3. Click **Enable**
4. Run the SQL again

### "bucket already exists"

**Solution**: This is fine! The bucket is already created.
- The SQL uses `ON CONFLICT DO NOTHING` so it won't fail

### "relation already exists"

**Solution**: Tables already exist
- You can either:
  - Skip (tables are already there)
  - Or drop them first (see below)

---

## 🗑️ To Start Fresh (Optional)

If you want to drop all tables and start over, run this FIRST:

```sql
-- Drop tables in reverse order (to handle foreign keys)
DROP TABLE IF EXISTS chat_history CASCADE;
DROP TABLE IF EXISTS materials CASCADE;
DROP TABLE IF EXISTS courses CASCADE;
DROP TABLE IF EXISTS personalized CASCADE;
DROP TABLE IF EXISTS academic CASCADE;

-- Drop trigger function
DROP FUNCTION IF EXISTS update_updated_at() CASCADE;

-- Drop storage policies
DROP POLICY IF EXISTS "Users can upload to own folder" ON storage.objects;
DROP POLICY IF EXISTS "Users can read own files" ON storage.objects;
DROP POLICY IF EXISTS "Users can update own files" ON storage.objects;
DROP POLICY IF EXISTS "Users can delete own files" ON storage.objects;

-- Note: Storage bucket will remain (that's fine)
```

Then run the `COMPLETE_SETUP.sql` again.

---

## ✅ Verify Setup

### Check Tables

Run this query in SQL Editor:

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
```

You should see:
- academic
- chat_history
- courses
- materials
- personalized

### Check Storage Bucket

1. Go to **Storage** in Supabase dashboard
2. You should see `course-materials` bucket

### Check RLS Policies

Run this query:

```sql
SELECT schemaname, tablename, policyname 
FROM pg_policies 
WHERE schemaname = 'public'
ORDER BY tablename, policyname;
```

You should see policies for all 5 tables.

---

## 🧪 Test the Setup

### 1. Test Signup

```bash
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

### 2. Test Academic Profile

```bash
# Use the access_token from signup
curl -X POST http://localhost:8000/api/academic \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "grade": ["Bachelor"],
    "semester_type": "double",
    "semester": 3,
    "subject": ["computer science"]
  }'
```

### 3. Check in Database

Go to **Table Editor** → **academic** table
- You should see your profile!

---

## 📚 Files Reference

| File | Purpose |
|------|---------|
| `COMPLETE_SETUP.sql` | **Run this in Supabase SQL Editor** |
| `MANUAL_SETUP_GUIDE.md` | This guide |
| `migrations/001_enable_extensions.sql` | Extensions only |
| `migrations/001_setup_storage.sql` | Storage only |
| `migrations/002_create_tables.sql` | Tables only |
| `migrations/003_create_rls_policies.sql` | RLS only |

---

## 🎯 Summary

**To set up your database:**

1. Open: https://supabase.com/dashboard/project/fupupzbizwmxtcrftdhy/editor
2. Copy: `python-backend/COMPLETE_SETUP.sql`
3. Paste and Run
4. Verify in Table Editor

**That's it!** 🎉

---

## 💡 Why This Method?

- ✅ No Python dependencies needed
- ✅ No connection issues
- ✅ Works directly in Supabase
- ✅ Can see results immediately
- ✅ Easy to debug if errors occur

---

**Ready?** Open the SQL Editor and paste `COMPLETE_SETUP.sql`!
