# 🚀 Run This Now

You've set the database password. Now run this ONE command:

```bash
cd python-backend
python setup_complete.py --clean
```

## What This Does

1. ✅ Removes any unnecessary tables
2. ✅ Creates storage bucket for files
3. ✅ Creates 5 database tables
4. ✅ Sets up security policies
5. ✅ Verifies everything works

## Expected Output

You should see:

```
======================================================================
  Complete Database Setup
======================================================================

Step 1: Checking Environment
──────────────────────────────────────────────────────────────────────
  ✓ All environment variables set

Step 2: Connecting to Database
──────────────────────────────────────────────────────────────────────
  ✓ Connected successfully

Step 3: Checking Existing Tables
──────────────────────────────────────────────────────────────────────
  Found X existing tables:
    - table1
    - table2
  
  🗑️  Cleaning up existing tables...
  ✓ Dropped table: table1
  ✓ Dropped table: table2

Step 4: Setting Up Storage Buckets
──────────────────────────────────────────────────────────────────────
  📄 Creating storage buckets and policies
  ✓ Success

Step 5: Enabling PostgreSQL Extensions
──────────────────────────────────────────────────────────────────────
  📄 Enabling extensions
  ✓ Success

Step 6: Creating Database Tables
──────────────────────────────────────────────────────────────────────
  📄 Creating tables
  ✓ Success

Step 7: Setting Up Row Level Security
──────────────────────────────────────────────────────────────────────
  📄 Creating RLS policies
  ✓ Success

Step 8: Verifying Setup
──────────────────────────────────────────────────────────────────────
  Required tables: 5
  Found: 5

  ✓ Created tables:
    - academic
    - personalized
    - courses
    - materials
    - chat_history

======================================================================
  Setup Complete! 🎉
======================================================================

Your database is ready with:
  ✓ Storage bucket: course-materials
  ✓ 5 tables: academic, personalized, courses, materials, chat_history
  ✓ Row Level Security policies
  ✓ Indexes for performance
```

## If You See Errors

### "vector extension does not exist"

1. Go to https://supabase.com/dashboard/project/fupupzbizwmxtcrftdhy
2. Click **Database** → **Extensions**
3. Search for "vector"
4. Click **Enable**
5. Run the command again

### "permission denied" or "connection failed"

Check your `SUPABASE_DB_PASSWORD` in `.env` file is correct.

## After Setup

Test it works:

```bash
# Start the backend
python main.py

# In another terminal, test signup
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

If you get a response with `access_token`, everything is working! 🎉

---

**Ready?** Copy and run:

```bash
cd python-backend && python setup_complete.py --clean
```
