# Quick Start: Setting Up Your Database

You're missing the database tables because migrations haven't been run yet. Here's how to fix it:

## 🚀 Quick Setup (3 steps)

### Step 1: Get Your Database Password

1. Go to https://supabase.com/dashboard/project/fupupzbizwmxtcrftdhy
2. Click **Settings** → **Database**
3. Find the **Connection string** section
4. Copy your password from the connection string (it's between `postgres:` and `@db.`)

### Step 2: Add Password to .env

Add this line to `python-backend/.env`:

```env
SUPABASE_DB_PASSWORD=your_password_here
```

### Step 3: Run Setup Script

```bash
cd python-backend
pip install psycopg2-binary
python setup_database.py
```

That's it! The script will:
- ✅ Check your configuration
- ✅ Test database connection
- ✅ Create all tables
- ✅ Set up security policies

## 📋 What Tables Get Created

After setup, you'll have these tables:

- **academic** - User academic profiles (grade, semester, subjects)
- **personalized** - User preferences from questionnaire
- **courses** - User-created courses
- **materials** - Uploaded learning materials
- **chat_history** - AI conversation history

## ✅ Verify It Worked

Check in Supabase Dashboard:
1. Go to **Table Editor**
2. You should see all 5 tables listed

Or run this SQL query in **SQL Editor**:
```sql
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' ORDER BY table_name;
```

## 🔧 Troubleshooting

### "psycopg2-binary is not installed"
```bash
pip install psycopg2-binary
```

### "SUPABASE_DB_PASSWORD not set"
Add it to your `.env` file (see Step 2 above)

### "Connection failed"
- Double-check your password
- Make sure your SUPABASE_URL is correct
- Check your internet connection

### Tables already exist
If you see "relation already exists" errors, the tables are already there! You're good to go.

## 📚 More Information

- **Detailed guide**: See `MIGRATION_GUIDE.md`
- **Migration files**: Check `migrations/*.sql`
- **Rollback**: Run `python scripts/run_migrations.py --rollback` to start fresh

## 🎉 Next Steps

Once tables are created:

1. **Start the backend**:
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
   - Go to `/signup` to create an account
   - Fill in academic profile
   - Complete the questionnaire
   - Start using the app!

---

**Need help?** Check `MIGRATION_GUIDE.md` for detailed troubleshooting.
