-- Migration: Enable Required PostgreSQL Extensions
-- Description: Enable extensions needed for UUID generation, cryptographic functions,
--              vector embeddings, and text search capabilities
-- Requirements: 1.4

-- Enable UUID generation extension
-- Provides uuid_generate_v4() function for automatic UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable cryptographic functions extension
-- Provides encryption and hashing functions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Enable pgvector extension for vector embeddings
-- Provides VECTOR data type and similarity search operations for RAG
-- Note: This extension must be enabled in Supabase dashboard first
-- Go to Database → Extensions → Search for "vector" → Enable
CREATE EXTENSION IF NOT EXISTS "vector";

-- Enable trigram extension for text search
-- Provides similarity and pattern matching capabilities for future search features
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
