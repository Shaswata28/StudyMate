# StudyMate

An AI-powered study assistant application with React frontend and FastAPI backend.

## Quick Start

For detailed installation instructions, see [INSTALLATION.md](INSTALLATION.md).

### Quick Installation

**Windows:**
```bash
install.bat
```

**macOS/Linux:**
```bash
chmod +x install.sh
./install.sh
```

**All platforms:**
```bash
python install_dependencies.py
```

## Project Structure

- `client/` - React frontend application
- `python-backend/` - FastAPI backend server
- `docs/` - Project documentation
- `.kiro/specs/` - Feature specifications

## Documentation

- [Installation Guide](INSTALLATION.md) - Complete setup instructions
- [Database Schema](docs/database-schema.md) - Database structure
- [API Endpoints](python-backend/API_ENDPOINTS.md) - Backend API documentation
- [Supabase Setup](docs/SUPABASE_SETUP.md) - Database configuration

## Development

```bash
# Frontend (Terminal 1)
pnpm dev

# Backend (Terminal 2)
cd python-backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn main:app --reload
```

## Tech Stack

- **Frontend**: React 18, TypeScript, Vite, TailwindCSS, Radix UI
- **Backend**: FastAPI, Python 3.8+
- **Database**: Supabase (PostgreSQL)
- **AI**: Google Gemini API
- **Package Manager**: pnpm