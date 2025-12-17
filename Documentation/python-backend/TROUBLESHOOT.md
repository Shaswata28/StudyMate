# Troubleshooting: Tables Not Created

You saw the storage bucket but no tables. Let's debug this step by step.

## 🔍 Possible Issues

### Issue 1: Vector Extension Not Enabled

The `vector` extension might not be enabled, causing the script to fail silently.

**Solution**:
1. Go to **Database** → **Extensions** in Supabase
2. Search for "vector"
3. Click **Enable**
4. Run the SQL again

### Issue 2: Script Failed Partway Through

The script might have failed after creating the storage bucket but before creating tables.

**Solution**: Run the SQL in sections (see below)

### Issue 3: Tables Created in Wrong Schema

Tables might be in a different schema (not `public`).

**Check**: Run this query in SQL Editor:
```sql
SELECT schemaname, tablename 
FROM pg_tables 
WHERE tablename IN ('academic', 'personalized', 'courses', 'materials', 'chat_history')
ORDER BY schemaname, tablename;
```

---

## 🚀 Step-by-Step Solution

Use the file: `python-backend/STEP_BY_STEP.sql`

### Step 1: Enable Extensions

Copy and run **SECTION 1** only:

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
```

**Expected**: "Success. No rows returned"

**If you see an error about "vector"**:
- Go to Database → Extensions
- Enable "vector" manually
- Run again

### Step 2: Create Trigger Function

Copy and run **SECTION 2** only:

```sql
CREATE OR REPLACE FUNCTION update_updated_at() 
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

**Expected**: "Success. No rows returned"

### Step 3: Create Tables

Copy and run **SECTION 3** only (all 5 tables)

**Expected**: "Success. No rows returned"

**Then check Table Editor** - you should see all 5 tables!

### Step 4: Enable RLS

Copy and run **SECTION 4** only (all RLS policies)

**Expected**: "Success. No rows returned"

---

## ✅ Verify Tables Exist

Run this query:

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('academic', 'personalized', 'courses', 'materials', 'chat_history')
ORDER BY table_name;
```

**Expected output**:
```
academic
chat_history
courses
materials
personalized
```

If you see all 5, you're done! ✅

---

## 🐛 Common Errors

### Error: "extension vector does not exist"

**Solution**: Enable in Database → Extensions → vector

### Error: "relation already exists"

**Solution**: Tables already exist! Check Table Editor.

### Error: "syntax error near $"

**Solution**: Make sure you copied the entire function including `$$`

### Error: "permission denied"

**Solution**: You might not have the right permissions. Contact Supabase support.

---

## 🗑️ If You Need to Start Over

Run this to drop everything:

```sql
DROP TABLE IF EXISTS chat_history CASCADE;
DROP TABLE IF EXISTS materials CASCADE;
DROP TABLE IF EXISTS courses CASCADE;
DROP TABLE IF EXISTS personalized CASCADE;
DROP TABLE IF EXISTS academic CASCADE;
DROP FUNCTION IF EXISTS update_updated_at() CASCADE;
```

Then run the setup SQL again.

---

## 📞 Still Having Issues?

1. **Check the SQL Editor output** - Look for error messages
2. **Check Extensions** - Make sure "vector" is enabled
3. **Check Logs** - Go to Database → Logs in Supabase
4. **Try one table at a time** - Run each CREATE TABLE separately

---

## 💡 Alternative: Simplest Possible Setup

If all else fails, run just the tables without any fancy features:

```sql
-- Minimal setup (no vector, no complex constraints)

CREATE TABLE academic (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    grade TEXT[] NOT NULL,
    semester_type TEXT NOT NULL,
    semester INTEGER NOT NULL,
    subject TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE personalized (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    prefs JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE courses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE materials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE chat_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    history JSONB[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

This creates the basic tables without vector embeddings or complex constraints.

---

**Next**: Try running `STEP_BY_STEP.sql` section by section and let me know which section fails!
