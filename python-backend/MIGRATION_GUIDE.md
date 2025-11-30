# Database Migration Guide

This guide will help you run the database migrations to create all the necessary tables in your Supabase database.

## Prerequisites

Before running migrations, you need:

1. ✅ Supabase project created (you have this)
2. ✅ Environment variables set in `.env` (you have this)
3. ❌ **Database password** (you need to get this)

## Step 1: Get Your Database Password

Your database password is **different** from your API keys. Here's how to find it:

### Option A: From Supabase Dashboard

1. Go to your Supabase project: https://supabase.com/dashboard/project/fupupzbizwmxtcrftdhy
2. Click on **Settings** (gear icon in the left sidebar)
3. Click on **Database** in the settings menu
4. Scroll down to **Connection string** section
5. Click on **Connection pooling** or **Direct connection**
6. You'll see a connection string like:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.fupupzbizwmxtcrftdhy.supabase.co:5432/postgres
   ```
7. Copy the password part (between `postgres:` and `@db.`)

### Option B: Reset Database Password

If you don't know your password:

1. Go to **Settings** → **Database**
2. Scroll to **Database Password** section
3. Click **Reset Database Password**
4. Copy the new password (you won't be able to see it again!)

## Step 2: Add Password to .env File

Add this line to your `python-backend/.env` file:

```env
# Database password for direct PostgreSQL connection
SUPABASE_DB_PASSWORD=your_database_password_here
```

**Important**: Replace `your_database_password_here` with your actual password!

## Step 3: Install Required Package

The migration script needs `psycopg2-binary` to connect to PostgreSQL:

```bash
cd python-backend
pip install psycopg2-binary
```

Or if you're using a virtual environment:

```bash
cd python-backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install psycopg2-binary
```

## Step 4: Run Migrations

Now you can run the migrations:

```bash
cd python-backend
python scripts/run_migrations.py
```

You should see output like:

```
======================================================================
Starting forward migrations
======================================================================
Connecting to Supabase database...
✓ Database connection established

📄 Processing: 001_enable_extensions.sql
Executing migration: 001_enable_extensions.sql
✓ Migration 001_enable_extensions.sql completed successfully

📄 Processing: 002_create_tables.sql
Executing migration: 002_create_tables.sql
✓ Migration 002_create_tables.sql completed successfully

📄 Processing: 003_create_rls_policies.sql
Executing migration: 003_create_rls_policies.sql
✓ Migration 003_create_rls_policies.sql completed successfully

======================================================================
✅ All migrations completed successfully!
======================================================================
```

## Step 5: Verify Tables Were Created

After running migrations, verify the tables exist:

### Option A: Supabase Dashboard

1. Go to your Supabase project
2. Click on **Table Editor** in the left sidebar
3. You should see these tables:
   - `academic`
   - `personalized`
   - `courses`
   - `materials`
   - `chat_history`

### Option B: SQL Editor

1. Go to **SQL Editor** in Supabase dashboard
2. Run this query:
   ```sql
   SELECT table_name 
   FROM information_schema.tables 
   WHERE table_schema = 'public' 
   ORDER BY table_name;
   ```
3. You should see all your tables listed

## What Gets Created

The migrations create:

### 1. Extensions (001_enable_extensions.sql)
- `uuid-ossp` - UUID generation
- `pgcrypto` - Cryptographic functions
- `vector` - Vector embeddings for AI
- `pg_trgm` - Text search capabilities

### 2. Tables (002_create_tables.sql)
- **academic** - User academic profiles (grade, semester, subjects)
- **personalized** - User preferences from questionnaire (JSONB)
- **courses** - User-created courses
- **materials** - Uploaded learning materials
- **chat_history** - AI conversation history with embeddings

### 3. Row Level Security (003_create_rls_policies.sql)
- Enables RLS on all tables
- Creates policies so users can only access their own data
- Ensures data isolation between users

## Troubleshooting

### Error: "psycopg2-binary is not installed"

**Solution**: Install the package:
```bash
pip install psycopg2-binary
```

### Error: "SUPABASE_DB_PASSWORD environment variable is not set"

**Solution**: Add your database password to `.env` file (see Step 2)

### Error: "Database connection error"

**Possible causes**:
1. Wrong password - Double-check your password
2. Wrong project reference - Verify your SUPABASE_URL is correct
3. Network issue - Check your internet connection
4. Firewall - Ensure port 5432 is not blocked

### Error: "Migration file not found"

**Solution**: Make sure you're running the command from the `python-backend` directory:
```bash
cd python-backend
python scripts/run_migrations.py
```

### Error: "relation already exists"

This means tables already exist. You have two options:

**Option 1**: Skip (tables are already there, you're good!)

**Option 2**: Rollback and re-run:
```bash
python scripts/run_migrations.py --rollback
python scripts/run_migrations.py
```

⚠️ **Warning**: Rollback will delete all data!

## Rollback (Undo Migrations)

If you need to undo the migrations and start fresh:

```bash
python scripts/run_migrations.py --rollback
```

This will:
- Drop all tables
- Drop all policies
- Drop all indexes
- Drop the trigger function

⚠️ **Warning**: This will delete ALL data in these tables!

## Next Steps

After migrations are complete:

1. ✅ Tables are created
2. ✅ RLS policies are active
3. ✅ Ready to use the API

You can now:
- Test user registration via `/api/auth/signup`
- Test login via `/api/auth/login`
- Create academic profiles via `/api/academic`
- Save preferences via `/api/preferences`
- Create courses via `/api/courses`

## Quick Test

Test that everything works:

```bash
# Start the backend
cd python-backend
python main.py

# In another terminal, test signup
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

If you get a response with `access_token`, everything is working! 🎉

## Need Help?

If you encounter issues:

1. Check the error message carefully
2. Verify all environment variables are set
3. Check Supabase dashboard for any errors
4. Look at the migration SQL files to understand what's being created
5. Check Supabase logs in the dashboard

## Files Reference

- **Migration files**: `python-backend/migrations/*.sql`
- **Migration script**: `python-backend/scripts/run_migrations.py`
- **Environment config**: `python-backend/.env`
- **This guide**: `python-backend/MIGRATION_GUIDE.md`
