# Supabase Project Setup Guide

This guide walks you through setting up your Supabase project for the learning platform.

## Prerequisites

- A Supabase account (sign up at https://supabase.com if you don't have one)
- Access to your project's `.env` file

## Step 1: Create a New Supabase Project

1. Navigate to https://supabase.com/dashboard
2. Click the **"New Project"** button
3. Fill in the project details:
   - **Name**: Choose a descriptive name (e.g., "learning-platform-prod")
   - **Database Password**: Generate a strong password (save this securely!)
   - **Region**: Select the region closest to your target users for optimal performance
   - **Pricing Plan**: Choose the appropriate plan (Free tier is fine for development)
4. Click **"Create new project"**
5. Wait for project provisioning (typically takes 1-2 minutes)

## Step 2: Retrieve Your API Keys and Credentials

Once your project is ready:

1. In your Supabase dashboard, navigate to **Settings → API**
2. You'll find the following credentials:

### Project URL
- Located under "Project URL"
- Format: `https://[project-ref].supabase.co`
- Copy this value for `SUPABASE_URL`

### API Keys
- **anon/public key**: Safe to use in client-side code
  - Copy this value for `SUPABASE_ANON_KEY`
- **service_role key**: Secret key with admin privileges (NEVER expose in client code)
  - Copy this value for `SUPABASE_SERVICE_ROLE_KEY`

### Database Connection String
1. Navigate to **Settings → Database**
2. Scroll to "Connection string" section
3. Select the **"URI"** tab
4. Copy the connection string (it will have `[YOUR-PASSWORD]` placeholder)
5. Replace `[YOUR-PASSWORD]` with the database password you created in Step 1
6. Copy this value for `DATABASE_URL`

## Step 3: Configure Your Environment Variables

1. Open the `.env` file in your project root
2. Replace the placeholder values with your actual credentials:

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your_actual_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_actual_service_role_key_here
DATABASE_URL=postgresql://postgres:your_password@db.your-project-ref.supabase.co:5432/postgres
```

3. Save the file

## Step 4: Enable Required PostgreSQL Extensions

1. In your Supabase dashboard, navigate to **SQL Editor**
2. Click **"New query"**
3. Copy and paste the following SQL:

```sql
-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable cryptographic functions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Enable vector embeddings for RAG (if available)
CREATE EXTENSION IF NOT EXISTS "vector";

-- Enable text search capabilities
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
```

4. Click **"Run"** to execute the query
5. Verify all extensions are enabled successfully

## Step 5: Configure Authentication Settings (Optional but Recommended)

1. Navigate to **Authentication → Settings**
2. Configure the following:
   - **Enable Email Confirmations**: Toggle ON for production security
   - **Site URL**: Set to your application's URL (e.g., `http://localhost:8080` for development)
   - **JWT Expiry**: Default is 3600 seconds (1 hour) - adjust as needed
3. Save changes

## Step 6: Verify Your Setup

Run the following command to verify your environment is configured correctly:

```bash
pnpm run verify-supabase
```

If you see any errors, double-check your `.env` file values against your Supabase dashboard.

## Security Best Practices

⚠️ **IMPORTANT SECURITY NOTES:**

1. **Never commit `.env` to version control** - It's already in `.gitignore`
2. **Keep `SUPABASE_SERVICE_ROLE_KEY` secret** - Only use on the server-side
3. **Use `SUPABASE_ANON_KEY` for client-side** - It's safe to expose in frontend code
4. **Rotate keys if compromised** - You can regenerate keys in Supabase dashboard
5. **Use different projects for dev/staging/prod** - Isolate environments

## Troubleshooting

### "Invalid API key" errors
- Verify you copied the entire key without extra spaces
- Check that you're using the correct key (anon vs service_role)
- Ensure your project is fully provisioned (not still setting up)

### Connection timeout errors
- Verify your `DATABASE_URL` has the correct password
- Check that your IP isn't blocked by Supabase firewall
- Ensure the project region is accessible from your location

### Extension installation fails
- Some extensions may not be available on all Supabase plans
- The `vector` extension requires a paid plan in some regions
- Contact Supabase support if you need specific extensions

## Next Steps

Once your Supabase project is configured:

1. Proceed to **Task 2**: Install Supabase dependencies
2. Run the database migrations to create your schema
3. Test the authentication flow

For more information, see the [Supabase Documentation](https://supabase.com/docs).
