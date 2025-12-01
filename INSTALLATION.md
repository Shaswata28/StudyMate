# StudyMate Installation Guide

This guide will help you set up the StudyMate project on your local machine.

## Prerequisites

Before running the installation script, ensure you have the following installed:

1. **Python 3.8 or higher**
   - Download from: https://www.python.org/downloads/
   - Verify installation: `python --version` or `python3 --version`

2. **Node.js 18 or higher** (includes npm)
   - Download from: https://nodejs.org/
   - Verify installation: `node --version`

## Quick Start

### Option 1: Automated Installation (Recommended)

#### On Windows:
```bash
# Double-click install.bat or run in Command Prompt:
install.bat
```

#### On macOS/Linux:
```bash
# Make the script executable (first time only):
chmod +x install.sh

# Run the installation script:
./install.sh
```

#### Using Python directly (All platforms):
```bash
python install_dependencies.py
```

### Option 2: Manual Installation

If the automated script doesn't work, follow these steps:

#### 1. Install Frontend Dependencies

```bash
# Install pnpm (if not already installed)
npm install -g pnpm

# Install frontend dependencies
pnpm install
```

#### 2. Install Python Backend Dependencies

```bash
# Navigate to backend directory
cd python-backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

After installation, you need to configure environment variables:

### 1. Root .env file

Copy `.env.example` to `.env` and update with your values:
```bash
cp .env.example .env
```

### 2. Backend .env file

Copy `python-backend/.env.example` to `python-backend/.env` and update with your values:
```bash
cp python-backend/.env.example python-backend/.env
```

Required environment variables:
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase anon/public key
- `SUPABASE_SERVICE_KEY`: Your Supabase service role key
- `GEMINI_API_KEY`: Your Google Gemini API key

## Running the Application

### Development Mode

#### Terminal 1 - Frontend:
```bash
pnpm dev
```
The frontend will be available at http://localhost:8080

#### Terminal 2 - Python Backend:
```bash
# Activate virtual environment first
cd python-backend

# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Run the backend server
uvicorn main:app --reload --port 8000
```
The backend API will be available at http://localhost:8000

### Production Build

```bash
# Build frontend
pnpm build

# Start production server
pnpm start
```

## Troubleshooting

### Python Issues

**Problem**: `python` command not found
- **Solution**: Try `python3` instead, or add Python to your PATH

**Problem**: Virtual environment creation fails
- **Solution**: Ensure you have `python-venv` package installed:
  ```bash
  # On Ubuntu/Debian:
  sudo apt-get install python3-venv
  ```

**Problem**: Permission denied when installing packages
- **Solution**: Make sure you're using the virtual environment, not system Python

### Node.js/pnpm Issues

**Problem**: `pnpm` command not found after installation
- **Solution**: Restart your terminal or add npm global bin to PATH

**Problem**: `EACCES` permission errors
- **Solution**: Configure npm to use a different directory:
  ```bash
  mkdir ~/.npm-global
  npm config set prefix '~/.npm-global'
  # Add to PATH: export PATH=~/.npm-global/bin:$PATH
  ```

### Database Issues

**Problem**: Cannot connect to Supabase
- **Solution**: 
  1. Verify your Supabase credentials in `python-backend/.env`
  2. Check that your Supabase project is active
  3. Ensure your IP is allowed in Supabase settings

### General Issues

**Problem**: Port already in use
- **Solution**: 
  - Frontend (8080): Change port in `vite.config.ts`
  - Backend (8000): Use `--port` flag: `uvicorn main:app --reload --port 8001`

**Problem**: Module not found errors
- **Solution**: 
  1. Delete `node_modules` and `pnpm-lock.yaml`, then run `pnpm install`
  2. For Python: Deactivate and reactivate venv, then reinstall requirements

## Verification

To verify your installation:

1. **Check Python dependencies**:
   ```bash
   cd python-backend
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip list
   ```

2. **Check frontend dependencies**:
   ```bash
   pnpm list
   ```

3. **Run tests**:
   ```bash
   # Frontend tests
   pnpm test

   # Backend tests (with venv activated)
   cd python-backend
   pytest
   ```

## Additional Resources

- [Project README](README.md)
- [Backend Documentation](python-backend/README.md)
- [Database Setup Guide](docs/SUPABASE_SETUP.md)
- [API Documentation](python-backend/API_ENDPOINTS.md)

## Getting Help

If you encounter issues not covered in this guide:

1. Check existing documentation in the `docs/` directory
2. Review error messages carefully
3. Ensure all prerequisites are properly installed
4. Try the manual installation steps
5. Check that all environment variables are correctly set

## Next Steps

After successful installation:

1. Review the [Database Schema](docs/database-schema.md)
2. Set up your Supabase database using the migration scripts
3. Explore the [API Endpoints](python-backend/API_ENDPOINTS.md)
4. Start developing!
