# Implementation Plan

## ✅ Completed Tasks

- [x] 1. Set up Supabase project and environment configuration
  - ✅ Created `.env` template with all required variables
  - ✅ Created `.env.example` as safe reference template
  - ✅ Updated `.gitignore` to exclude sensitive files
  - ✅ Created comprehensive setup documentation (`docs/SUPABASE_SETUP.md`)
  - ✅ Created interactive setup checklist (`SETUP_CHECKLIST.md`)
  - ✅ Created verification script (`server/scripts/verify-supabase.ts`)
  - ✅ Added `verify-supabase` npm script to package.json
  - _Requirements: 1.1, 1.2_
  - **⚠️ User Action Required**: Follow `SETUP_CHECKLIST.md` to create Supabase project and fill in credentials in `.env` file

## 📋 Remaining Tasks

- [x] 2. Install Supabase dependencies and create client module







  - [x] 2.1 Install supabase-py package





    - Add `supabase>=2.0.0` to `python-backend/requirements.txt`
    - Run `pip install -r python-backend/requirements.txt` (or in venv)


    - _Requirements: 1.2_
  
  - [x] 2.2 Create python-backend/services/supabase_client.py





    - Initialize Supabase client with service role key for admin operations
    - Create `get_user_client()` function for RLS-enforced operations
    - Export client instances
    - Load environment variables from existing config.py


    - _Requirements: 1.2_
  
  - [x] 2.3 Update python-backend/config.py to include Supabase configuration



    - Add SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY
    - Add validation for required Supabase environment variables
    - _Requirements: 1.2_

- [ ] 3. Create database migration SQL scripts
  - [ ] 3.1 Create python-backend/migrations/001_enable_extensions.sql
    - Enable uuid-ossp extension for UUID generation
    - Enable pgcrypto extension for cryptographic functions
    - Enable vector extension (pgvector) for embeddings
    - Enable pg_trgm extension for text search capabilities
    - _Requirements: 1.4_
  
  - [ ] 3.2 Create python-backend/migrations/002_create_tables.sql with all table definitions
    - Create update_updated_at() trigger function for automatic timestamp management
    - Create academic table with array fields and CHECK constraints
    - Create personalized table with JSONB preferences and GIN index
    - Create courses table for user-owned course containers
    - Create materials table with Supabase Storage integration
    - Create chat_history table with JSONB array and vector embeddings with HNSW index
    - _Requirements: 3.1, 3.2, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.5, 6.1, 6.2, 6.4, 6.5, 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [ ] 3.3 Create python-backend/migrations/003_create_rls_policies.sql
    - Enable RLS on all tables (academic, personalized, courses, materials, chat_history)
    - Create policy "Users edit own academic data" for academic table
    - Create policy "Users edit own prefs" for personalized table
    - Create policy "Users own courses" for courses table
    - Create policy "Users own materials" for materials table (via course ownership)
    - Create policy "Users own chat history" for chat_history table (via course ownership)
    - _Requirements: 1.3, 8.4_
  
  - [ ] 3.4 Create python-backend/migrations/004_rollback.sql
    - Include DROP TABLE statements in reverse dependency order
    - Include DROP POLICY statements for all RLS policies
    - Include DROP INDEX statements for all custom indexes
    - Include DROP FUNCTION for update_updated_at trigger
    - _Requirements: 8.5_

- [ ] 4. Create migration execution script
  - Create python-backend/scripts/run_migrations.py to execute SQL migrations
  - Read SQL files from migrations directory
  - Execute against Supabase database using service role connection
  - Log migration status and errors
  - Add instructions to README for running migrations
  - _Requirements: 8.1_

- [ ] 5. Create Python models for database schema
  - Create python-backend/models/database.py with Pydantic models
  - Define models for academic, personalized, courses, materials, chat_history tables
  - Export models for use in routers and services
  - Ensure models match SQL schema definitions
  - _Requirements: 8.2_

- [ ] 6. Create authentication utilities and dependencies
  - [ ] 6.1 Create python-backend/services/auth_service.py with auth utilities
    - Function to verify JWT tokens using Supabase
    - Function to get user from JWT token
    - FastAPI dependency for protected routes (get_current_user)
    - _Requirements: 2.2, 2.4_
  
  - [ ] 6.2 Create python-backend/middleware/auth_middleware.py
    - Middleware to extract and validate JWT tokens from Authorization header
    - Attach user info to request state
    - _Requirements: 2.2, 2.4_

- [ ] 7. Create API routes for authentication
  - [ ] 7.1 Create python-backend/routers/auth.py with authentication endpoints
    - POST /api/auth/signup - User registration endpoint
    - POST /api/auth/login - User login endpoint
    - POST /api/auth/logout - User logout endpoint
    - GET /api/auth/session - Get current session endpoint
    - POST /api/auth/refresh - Refresh access token endpoint
    - _Requirements: 2.1, 2.2, 2.3_
  
  - [ ] 7.2 Register auth routes in python-backend/main.py
    - Import and include auth router
    - _Requirements: 2.1_

- [ ] 8. Create API routes for database operations
  - [ ] 8.1 Create python-backend/routers/academic.py for academic profile operations
    - GET /api/academic - Get user's academic profile
    - POST /api/academic - Create academic profile
    - PUT /api/academic - Update academic profile
    - _Requirements: 3.1, 3.3, 3.4_
  
  - [ ] 8.2 Create python-backend/routers/preferences.py for personalized preferences
    - GET /api/preferences - Get user's preferences
    - POST /api/preferences - Create preferences
    - PUT /api/preferences - Update preferences
    - _Requirements: 4.1, 4.2, 4.3_
  
  - [ ] 8.3 Create python-backend/routers/courses.py for course management
    - GET /api/courses - List user's courses
    - POST /api/courses - Create new course
    - GET /api/courses/{id} - Get course details
    - PUT /api/courses/{id} - Update course
    - DELETE /api/courses/{id} - Delete course
    - _Requirements: 5.1, 5.3, 5.4, 5.5_
  
  - [ ] 8.4 Create python-backend/routers/materials.py for materials management
    - GET /api/courses/{course_id}/materials - List course materials
    - POST /api/courses/{course_id}/materials - Upload material
    - GET /api/materials/{id} - Get material details
    - DELETE /api/materials/{id} - Delete material
    - _Requirements: 6.1, 6.4, 6.5_
  
  - [ ] 8.5 Update python-backend/routers/chat.py for chat history operations
    - Update existing chat router to integrate with Supabase
    - GET /api/courses/{course_id}/chat - Get chat history from Supabase
    - POST /api/courses/{course_id}/chat - Save chat message to Supabase
    - Keep existing Gemini integration
    - _Requirements: 7.1, 7.2, 7.4_
  
  - [ ] 8.6 Register all API routes in python-backend/main.py
    - Import and include all routers (academic, preferences, courses, materials)
    - Chat router already registered
    - _Requirements: 8.1_

- [ ]* 9. Write property-based tests for database schema correctness
  - [ ]* 9.1 Set up testing infrastructure
    - Hypothesis already installed in requirements.txt
    - Create python-backend/tests/ directory structure
    - Create test database configuration (use separate Supabase project or local PostgreSQL)
    - Create test utilities for database setup/teardown in python-backend/tests/conftest.py
  
  - [ ]* 9.2 Write property test for referential integrity cascade behavior
    - **Property 1: Referential integrity cascade behavior**
    - **Validates: Requirements 3.5, 4.5, 5.2, 6.2, 7.3**
    - Test that deleting a user cascades to all dependent records
    - Use property testing to generate user data with related records
  
  - [ ]* 9.3 Write property test for ownership-based query filtering
    - **Property 2: Ownership-based query filtering**
    - **Validates: Requirements 3.3, 5.3, 6.4**
    - Test that users can only query their own records
    - Use property testing to generate multiple users with data
  
  - [ ]* 9.4 Write property test for JSONB round-trip preservation
    - **Property 3: JSONB round-trip preservation**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
    - Test storing and retrieving various JSON structures
    - Use property testing to generate diverse JSON objects
  
  - [ ]* 9.5 Write property test for unique constraint enforcement
    - **Property 4: Unique constraint enforcement**
    - **Validates: Requirements 3.2, 4.5**
    - Test that duplicate user records fail with constraint violation
    - Use property testing to generate user data
  
  - [ ]* 9.6 Write property test for RLS policy coverage
    - **Property 5: Row Level Security policy coverage**
    - **Validates: Requirements 1.3, 8.4**
    - Test that all tables have RLS enabled and policies defined
    - Verify users cannot access other users' data
  
  - [ ]* 9.7 Write property test for authentication token generation
    - **Property 6: Authentication token generation**
    - **Validates: Requirements 2.2**
    - Test that valid credentials return valid JWT tokens
    - Use property testing to generate email/password combinations
  
  - [ ]* 9.8 Write property test for invalid credential rejection
    - **Property 7: Invalid credential rejection**
    - **Validates: Requirements 2.3**
    - Test that invalid credentials are rejected
    - Use property testing to generate invalid credentials
  
  - [ ]* 9.9 Write property test for expired token rejection
    - **Property 8: Expired token rejection**
    - **Validates: Requirements 2.4**
    - Test that expired tokens are rejected
    - Generate tokens with past expiration times
  
  - [ ]* 9.10 Write property test for cascade deletion propagation
    - **Property 9: Cascade deletion propagation**
    - **Validates: Requirements 5.4**
    - Test that deleting a course cascades to materials and chat_history
    - Use property testing to generate courses with related data
  
  - [ ]* 9.11 Write property test for chat message chronological ordering
    - **Property 10: Chat message chronological ordering**
    - **Validates: Requirements 7.4**
    - Test that chat messages are returned in chronological order
    - Use property testing to generate messages with random timestamps
  
  - [ ]* 9.12 Write property test for academic profile data persistence
    - **Property 12: Academic profile data persistence**
    - **Validates: Requirements 3.1, 3.4**
    - Test that academic profile updates persist correctly
    - Use property testing to generate academic profile data
  
  - [ ]* 9.13 Write property test for course metadata completeness
    - **Property 13: Course metadata completeness**
    - **Validates: Requirements 5.1, 5.5**
    - Test that course records include all required fields
    - Use property testing to generate course data
  
  - [ ]* 9.14 Write property test for material metadata completeness
    - **Property 14: Material metadata completeness**
    - **Validates: Requirements 6.1, 6.5**
    - Test that material records capture all required metadata
    - Use property testing to generate material data

- [ ]* 10. Write unit tests for API endpoints
  - [ ]* 10.1 Write unit tests for authentication endpoints in python-backend/tests/test_auth.py
    - Test user registration with valid email/password
    - Test registration with duplicate email fails
    - Test user login with correct credentials
    - Test login failure with incorrect password
    - Test session retrieval
    - Use pytest and FastAPI TestClient
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_
  
  - [ ]* 10.2 Write unit tests for academic profile endpoints in python-backend/tests/test_academic.py
    - Test creating academic profile with valid data
    - Test updating academic profile fields
    - Test constraint violations (invalid grade, semester out of range)
    - _Requirements: 3.1, 3.2, 3.3, 3.4_
  
  - [ ]* 10.3 Write unit tests for preferences endpoints in python-backend/tests/test_preferences.py
    - Test creating preferences with JSONB data
    - Test updating JSONB preferences with different structures
    - Test querying specific JSONB fields
    - _Requirements: 4.1, 4.2, 4.3, 4.4_
  
  - [ ]* 10.4 Write unit tests for courses endpoints in python-backend/tests/test_courses.py
    - Test creating course with required fields
    - Test querying user's courses
    - Test updating course name
    - Test deleting course and cascade behavior
    - _Requirements: 5.1, 5.3, 5.4, 5.5_
  
  - [ ]* 10.5 Write unit tests for materials endpoints in python-backend/tests/test_materials.py
    - Test creating material with storage reference
    - Test querying course materials
    - Test cascade delete when course is deleted
    - _Requirements: 6.1, 6.2, 6.4, 6.5_
  
  - [ ]* 10.6 Write unit tests for chat endpoints in python-backend/tests/test_chat.py
    - Test creating chat with messages
    - Test appending messages to history
    - Test querying chat history in chronological order
    - _Requirements: 7.1, 7.2, 7.4, 7.5_
  
  - [ ]* 10.7 Write unit tests for RLS policy enforcement in python-backend/tests/test_rls.py
    - Test user can read their own data
    - Test user cannot read other user's data
    - Test user can update their own data
    - Test user cannot update other user's data
    - _Requirements: 1.3, 8.4_

- [ ] 11. Create database schema documentation
  - Create docs/database-schema.md with comprehensive documentation
  - Document all tables with field descriptions and data types
  - Document all relationships and foreign keys with ERD diagram
  - Document all indexes and their purposes
  - Document all RLS policies and security model
  - Include example queries for common operations
  - _Requirements: 8.2_

- [ ] 12. Final checkpoint - Verify complete database setup
  - Run all migrations against Supabase database
  - Verify all tables are created with correct schema
  - Verify all RLS policies are active
  - Verify all indexes are created
  - Test authentication flow end-to-end via API
  - Test data isolation between users via API
  - Ensure all tests pass, ask the user if questions arise
