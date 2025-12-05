# Configuration Guide

This document provides comprehensive information about all configuration options for the StudyMate FastAPI backend, with special focus on the AI Brain service integration for material OCR and embedding generation.

## Table of Contents

1. [Overview](#overview)
2. [Environment Variables](#environment-variables)
3. [AI Brain Service Configuration](#ai-brain-service-configuration)
4. [Configuration Validation](#configuration-validation)
5. [Startup Health Checks](#startup-health-checks)
6. [Troubleshooting](#troubleshooting)

## Overview

The backend uses environment variables for configuration, loaded from a `.env` file in the `python-backend/` directory. All configuration is managed through the `config.py` module, which validates required settings on startup.

## Environment Variables

### Required Variables

These variables MUST be set for the application to start:

#### Supabase Configuration

```bash
# Your Supabase project URL
# Format: https://[project-ref].supabase.co
# Get from: https://app.supabase.com/project/[your-project]/settings/api
SUPABASE_URL=https://your-project-ref.supabase.co

# Public anonymous key (safe for client-side use)
# Used for operations with Row Level Security (RLS) enforcement
SUPABASE_ANON_KEY=your_anon_key_here

# Service role key (KEEP SECRET!)
# Used for admin operations that bypass RLS
# Never expose this key to the client side!
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# Database password (KEEP SECRET!)
# Required for running database migrations
# Get from: https://app.supabase.com/project/[your-project]/settings/database
SUPABASE_DB_PASSWORD=your_database_password_here
```

### Optional Variables

These variables have sensible defaults but can be customized:

#### Rate Limiting

```bash
# Maximum number of requests allowed per time window (per IP address)
# Default: 15
RATE_LIMIT_REQUESTS=15

# Time window in seconds for rate limiting
# Default: 60
RATE_LIMIT_WINDOW=60
```

#### CORS Configuration

```bash
# Comma-separated list of allowed origins for CORS
# Development: http://localhost:8080
# Production: Add your production frontend URL
# Default: http://localhost:8080
ALLOWED_ORIGINS=http://localhost:8080,https://studymate.com
```

#### AI Brain Service

```bash
# URL of the AI Brain service
# The AI Brain service orchestrates local Ollama models for OCR and embeddings
# Default: http://localhost:8001
AI_BRAIN_ENDPOINT=http://localhost:8001

# Request timeout in seconds for AI Brain operations
# OCR processing can take several minutes for large PDFs
# Default: 300.0 (5 minutes)
AI_BRAIN_TIMEOUT=300.0
```

#### Retry Configuration

```bash
# Maximum number of retry attempts for failed operations
# Applies to transient failures (network issues, temporary service unavailability)
# Default: 3
MAX_RETRY_ATTEMPTS=3

# Initial delay in seconds before first retry
# Default: 2.0
RETRY_DELAY_SECONDS=2.0

# Multiplier for exponential backoff between retries
# Each retry delay = RETRY_DELAY_SECONDS * (RETRY_BACKOFF_MULTIPLIER ^ (attempt - 1))
# Example with defaults: 2s, 4s, 8s
# Default: 2.0
RETRY_BACKOFF_MULTIPLIER=2.0
```

## AI Brain Service Configuration

The AI Brain service is a critical component for material processing. It provides:

- **OCR (Optical Character Recognition)**: Extracts text from PDFs and images using the qwen3-vl:2b model
- **Embedding Generation**: Creates semantic vector embeddings using the mxbai-embed-large model

### Configuration Details

#### AI_BRAIN_ENDPOINT

**Purpose**: Specifies the base URL of the AI Brain service

**Default**: `http://localhost:8001`

**Format**: Must be a valid HTTP/HTTPS URL without trailing slash

**Examples**:
```bash
# Local development (default)
AI_BRAIN_ENDPOINT=http://localhost:8001

# Remote AI Brain service
AI_BRAIN_ENDPOINT=http://ai-brain-server:8001

# HTTPS endpoint
AI_BRAIN_ENDPOINT=https://ai-brain.example.com
```

**When to Change**:
- Running AI Brain service on a different port
- Using a remote AI Brain service
- Deploying in containerized environments (Docker, Kubernetes)

#### AI_BRAIN_TIMEOUT

**Purpose**: Sets the maximum time to wait for AI Brain operations to complete

**Default**: `300.0` (5 minutes)

**Unit**: Seconds (float)

**Considerations**:
- **OCR Processing**: Large PDFs can take 2-5 minutes to process
- **Embedding Generation**: Usually completes in seconds
- **Network Latency**: Add buffer for network delays if using remote service

**Examples**:
```bash
# Default - suitable for most use cases
AI_BRAIN_TIMEOUT=300.0

# Shorter timeout for faster failure detection (development)
AI_BRAIN_TIMEOUT=60.0

# Longer timeout for very large documents
AI_BRAIN_TIMEOUT=600.0
```

**Timeout Behavior**:
- If timeout is exceeded, the operation fails
- Material status is set to 'failed'
- Error message indicates timeout
- User can retry the operation

### Retry Configuration for AI Brain

The system implements exponential backoff retry logic for transient failures:

**Retry Scenarios**:
- ✅ Connection errors (AI Brain service temporarily unavailable)
- ✅ HTTP 5xx errors (server errors)
- ✅ Timeout errors (for embedding generation only)
- ❌ HTTP 4xx errors (client errors - no retry)
- ❌ OCR timeout errors (likely file too large - no retry)

**Retry Calculation**:
```
Attempt 1: RETRY_DELAY_SECONDS * (RETRY_BACKOFF_MULTIPLIER ^ 0) = 2.0s
Attempt 2: RETRY_DELAY_SECONDS * (RETRY_BACKOFF_MULTIPLIER ^ 1) = 4.0s
Attempt 3: RETRY_DELAY_SECONDS * (RETRY_BACKOFF_MULTIPLIER ^ 2) = 8.0s
```

**Configuration Examples**:
```bash
# Aggressive retries (faster, more attempts)
MAX_RETRY_ATTEMPTS=5
RETRY_DELAY_SECONDS=1.0
RETRY_BACKOFF_MULTIPLIER=1.5

# Conservative retries (slower, fewer attempts)
MAX_RETRY_ATTEMPTS=2
RETRY_DELAY_SECONDS=5.0
RETRY_BACKOFF_MULTIPLIER=3.0

# No retries (fail fast)
MAX_RETRY_ATTEMPTS=1
```

## Configuration Validation

The `Config` class in `config.py` validates all configuration on startup:

### Validation Rules

1. **SUPABASE_URL**:
   - Must be set
   - Must start with `https://`
   - Application exits if invalid

2. **SUPABASE_ANON_KEY**:
   - Must be set
   - Must not be empty
   - Application exits if invalid

3. **SUPABASE_SERVICE_ROLE_KEY**:
   - Must be set
   - Must not be empty
   - Application exits if invalid

4. **AI_BRAIN_ENDPOINT**:
   - Optional (has default)
   - Trailing slashes are automatically removed
   - No validation of URL format (checked at runtime)

5. **Numeric Values**:
   - Must be valid numbers
   - Application exits if invalid format

### Validation Failure

If validation fails, the application will:
1. Log detailed error messages
2. Print errors to stderr
3. Exit with status code 1

**Example Error Output**:
```
❌ FATAL ERROR: Configuration validation failed:
  - SUPABASE_URL environment variable is not set
  - SUPABASE_ANON_KEY is empty

Please check your .env file and ensure all required variables are set.
```

## Startup Health Checks

The application performs health checks during startup to verify service availability:

### AI Brain Service Health Check

**When**: During application startup (in `startup_event`)

**What**: Sends GET request to `{AI_BRAIN_ENDPOINT}/`

**Success Criteria**: HTTP 200 response

**Behavior**:
- ✅ **Success**: Logs "AI Brain service connection verified"
- ⚠️ **Failure**: Logs warning but continues startup
  - Material processing will fail until service is available
  - Application remains functional for other operations

**Log Output**:
```
INFO: Initializing services...
INFO: AI Brain service connection verified
INFO: ✓ Services initialized successfully
```

**Failure Output**:
```
WARNING: AI Brain service not available at http://localhost:8001.
         Material processing will fail until service is started.
INFO: ✓ Services initialized successfully
```

### Service Manager Initialization

The `ServiceManager` initializes all services during startup:

1. **AI Brain Client**: Creates client instance with configured endpoint and timeout
2. **Health Check**: Verifies AI Brain service is accessible
3. **Material Processing Service**: Initializes processing service with AI Brain client

**Startup Sequence**:
```
1. Load configuration from .env
2. Validate required configuration
3. Initialize ServiceManager
4. Create AI Brain client
5. Perform health check
6. Initialize Material Processing Service
7. Start AI Brain Service (brain_manager)
8. Application ready
```

## Troubleshooting

### AI Brain Service Not Available

**Symptom**: Warning during startup: "AI Brain service not available"

**Causes**:
- AI Brain service not running
- Wrong `AI_BRAIN_ENDPOINT` configuration
- Network connectivity issues
- Firewall blocking connection

**Solutions**:
1. **Start AI Brain Service**:
   ```bash
   cd ai-brain
   source venv/bin/activate
   python brain.py
   ```

2. **Verify Service is Running**:
   ```bash
   curl http://localhost:8001/
   ```
   Should return: `{"message": "AI Brain Service is running"}`

3. **Check Configuration**:
   ```bash
   # In python-backend/.env
   AI_BRAIN_ENDPOINT=http://localhost:8001
   ```

4. **Check Logs**:
   - AI Brain service logs: Check terminal where `brain.py` is running
   - Backend logs: Check FastAPI startup logs

### Material Processing Failures

**Symptom**: All materials stuck in 'pending' or 'failed' status

**Causes**:
- AI Brain service unavailable
- Timeout too short for large files
- Ollama models not downloaded

**Solutions**:
1. **Verify AI Brain Service**:
   ```bash
   curl http://localhost:8001/
   ```

2. **Check Ollama Models**:
   ```bash
   ollama list
   ```
   Should show: `qwen3-vl:2b` and `mxbai-embed-large`

3. **Increase Timeout** (for large files):
   ```bash
   # In python-backend/.env
   AI_BRAIN_TIMEOUT=600.0  # 10 minutes
   ```

4. **Check Material Error Messages**:
   ```sql
   SELECT id, name, processing_status, error_message
   FROM materials
   WHERE processing_status = 'failed';
   ```

### Connection Timeout Errors

**Symptom**: "AI Brain service unavailable (connection error)"

**Causes**:
- AI Brain service not responding
- Network issues
- Firewall blocking connection

**Solutions**:
1. **Verify Network Connectivity**:
   ```bash
   ping localhost
   curl http://localhost:8001/
   ```

2. **Check Firewall Rules**:
   - Ensure port 8001 is not blocked
   - Check Windows Firewall / iptables

3. **Increase Retry Attempts**:
   ```bash
   # In python-backend/.env
   MAX_RETRY_ATTEMPTS=5
   RETRY_DELAY_SECONDS=3.0
   ```

### Configuration Not Loading

**Symptom**: Application uses default values instead of .env values

**Causes**:
- `.env` file not in correct location
- `.env` file has syntax errors
- Environment variables not exported

**Solutions**:
1. **Verify .env Location**:
   ```bash
   ls python-backend/.env
   ```
   Should exist in `python-backend/` directory

2. **Check .env Syntax**:
   - No spaces around `=`
   - No quotes needed for values
   - One variable per line

3. **Restart Application**:
   - Changes to .env require application restart
   - In development mode with `--reload`, changes are picked up automatically

### Validation Errors on Startup

**Symptom**: Application exits with "Configuration validation failed"

**Causes**:
- Required environment variables not set
- Invalid values for required variables

**Solutions**:
1. **Copy .env.example**:
   ```bash
   cp python-backend/.env.example python-backend/.env
   ```

2. **Fill in Required Values**:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`

3. **Check for Typos**:
   - Variable names are case-sensitive
   - URLs must start with `https://`

## Best Practices

### Development

```bash
# Use local AI Brain service
AI_BRAIN_ENDPOINT=http://localhost:8001

# Shorter timeout for faster feedback
AI_BRAIN_TIMEOUT=60.0

# Aggressive retries for development
MAX_RETRY_ATTEMPTS=3
RETRY_DELAY_SECONDS=1.0
```

### Production

```bash
# Use production AI Brain service
AI_BRAIN_ENDPOINT=https://ai-brain.production.com

# Longer timeout for reliability
AI_BRAIN_TIMEOUT=300.0

# Conservative retries to avoid overwhelming service
MAX_RETRY_ATTEMPTS=3
RETRY_DELAY_SECONDS=2.0
RETRY_BACKOFF_MULTIPLIER=2.0
```

### Testing

```bash
# Use test AI Brain service
AI_BRAIN_ENDPOINT=http://localhost:8001

# Short timeout for fast test execution
AI_BRAIN_TIMEOUT=30.0

# No retries for predictable test behavior
MAX_RETRY_ATTEMPTS=1
```

## Configuration Reference

### Complete .env Template

```bash
# =============================================================================
# StudyMate FastAPI Backend - Environment Configuration
# =============================================================================

# Rate Limiting
RATE_LIMIT_REQUESTS=15
RATE_LIMIT_WINDOW=60

# CORS
ALLOWED_ORIGINS=http://localhost:8080

# Supabase (REQUIRED)
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
SUPABASE_DB_PASSWORD=your_database_password_here

# AI Brain Service
AI_BRAIN_ENDPOINT=http://localhost:8001
AI_BRAIN_TIMEOUT=300.0

# Retry Configuration
MAX_RETRY_ATTEMPTS=3
RETRY_DELAY_SECONDS=2.0
RETRY_BACKOFF_MULTIPLIER=2.0
```

### Configuration Access in Code

```python
from config import config

# Access configuration values
endpoint = config.AI_BRAIN_ENDPOINT
timeout = config.AI_BRAIN_TIMEOUT
max_retries = config.MAX_RETRY_ATTEMPTS

# Configuration is validated on import
# No need to check for None or invalid values
```

## Related Documentation

- [AI Brain Client README](services/AI_BRAIN_CLIENT_README.md) - AI Brain client usage
- [Material Processing Service README](services/MATERIAL_PROCESSING_SERVICE_README.md) - Material processing details
- [.env.example](.env.example) - Environment variable template
- [README.md](README.md) - Main backend documentation
