# Documentation

This directory contains documentation for setting up and using the learning platform.

## Setup Guides

- **[Supabase Setup Guide](./SUPABASE_SETUP.md)** - Complete guide for setting up your Supabase project, configuring environment variables, and enabling required extensions.

## Quick Start

1. Follow the [Supabase Setup Guide](./SUPABASE_SETUP.md) to create and configure your Supabase project
2. Copy `.env.example` to `.env` and fill in your credentials
3. Run `pnpm install` to install dependencies
4. Run `pnpm verify-supabase` to verify your configuration (after installing Supabase dependencies)
5. Run database migrations to create the schema
6. Start the development server with `pnpm dev`

## Environment Variables

The application requires the following environment variables to be set in your `.env` file:

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Your Supabase project URL | Yes |
| `SUPABASE_ANON_KEY` | Supabase anonymous/public key (safe for client-side) | Yes |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key (server-side only, keep secret) | Yes |
| `DATABASE_URL` | PostgreSQL connection string | Yes |

See `.env.example` for the expected format of each variable.

## Security Notes

⚠️ **Important Security Practices:**

- Never commit `.env` to version control
- Keep `SUPABASE_SERVICE_ROLE_KEY` secret - only use server-side
- Use `SUPABASE_ANON_KEY` for client-side operations
- Rotate keys immediately if compromised
- Use separate Supabase projects for development, staging, and production

## Additional Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase JavaScript Client](https://supabase.com/docs/reference/javascript/introduction)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
