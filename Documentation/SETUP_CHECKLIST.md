# Supabase Setup Checklist

Use this checklist to track your progress setting up the Supabase database for the learning platform.

## ✅ Task 1: Supabase Project Setup

### Step 1: Create Supabase Project
- [ ] Go to https://supabase.com/dashboard
- [ ] Click "New Project"
- [ ] Enter project name
- [ ] Generate and save strong database password
- [ ] Select appropriate region
- [ ] Wait for project provisioning (~2 minutes)

### Step 2: Retrieve Credentials
- [ ] Navigate to Settings → API in Supabase dashboard
- [ ] Copy Project URL
- [ ] Copy anon/public key
- [ ] Copy service_role key
- [ ] Navigate to Settings → Database
- [ ] Copy connection string (URI format)
- [ ] Replace `[YOUR-PASSWORD]` with your database password

### Step 3: Configure Environment
- [ ] Open `.env` file in project root
- [ ] Set `SUPABASE_URL` with your project URL
- [ ] Set `SUPABASE_ANON_KEY` with your anon key
- [ ] Set `SUPABASE_SERVICE_ROLE_KEY` with your service role key
- [ ] Set `DATABASE_URL` with your connection string (password included)
- [ ] Save the file
- [ ] Verify `.env` is in `.gitignore` (already done ✓)

### Step 4: Enable PostgreSQL Extensions
- [ ] Open SQL Editor in Supabase dashboard
- [ ] Run the following SQL:
  ```sql
  CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
  CREATE EXTENSION IF NOT EXISTS "pgcrypto";
  CREATE EXTENSION IF NOT EXISTS "vector";
  CREATE EXTENSION IF NOT EXISTS "pg_trgm";
  ```
- [ ] Verify all extensions enabled successfully

### Step 5: Configure Authentication (Optional)
- [ ] Navigate to Authentication → Settings
- [ ] Enable email confirmations (recommended for production)
- [ ] Set site URL (e.g., `http://localhost:8080` for dev)
- [ ] Configure JWT expiry if needed
- [ ] Save changes

## 📋 Next Steps

After completing Task 1, proceed to:

- **Task 2**: Install Supabase dependencies (`@supabase/supabase-js`)
- **Task 3**: Create Supabase client modules
- **Task 4**: Create database migration scripts
- **Task 5**: Run migrations to create schema

## 🔍 Verification

After installing Supabase dependencies (Task 2), run:

```bash
pnpm verify-supabase
```

This will verify that all environment variables are correctly configured and that the connection to Supabase is working.

## 📚 Additional Resources

- [Detailed Setup Guide](./docs/SUPABASE_SETUP.md)
- [Supabase Documentation](https://supabase.com/docs)
- [Environment Variables Reference](./docs/README.md)

## ⚠️ Security Reminders

- ✓ `.env` is excluded from version control
- ✓ Never share your `SUPABASE_SERVICE_ROLE_KEY`
- ✓ Use different projects for dev/staging/production
- ✓ Rotate keys immediately if compromised
