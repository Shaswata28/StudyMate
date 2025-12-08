# AI Brain Service - Installation Guide

This guide covers the installation and verification of the AI Brain Service.

## Overview

The AI Brain Service requires:
1. **Ollama** - Local model serving infrastructure
2. **Python 3.10+** - Runtime environment
3. **Required Models** - qwen2.5:1.5b, deepseek-ocr, mxbai-embed-large
4. **Python Packages** - FastAPI, Uvicorn, Ollama client, Whisper, PyTorch, etc.

## Installation Methods

### Method 1: Automated Installation (Recommended)

The automated installation script handles all setup steps:

```bash
cd ai-brain
chmod +x install.sh
./install.sh
```

**What the script does:**
1. ✓ Checks if Ollama is installed
2. ✓ Verifies Ollama service is running (starts it if needed)
3. ✓ Pulls required Ollama models (or verifies they're already installed)
4. ✓ Checks Python installation (3.10+ required)
5. ✓ Creates Python virtual environment
6. ✓ Installs all Python dependencies from requirements.txt
7. ✓ Verifies installation by testing imports

**Time estimate:** 10-20 minutes (depending on internet speed for model downloads)

### Method 2: Manual Installation

See QUICKSTART.md for step-by-step manual installation instructions.

## Verification

After installation, verify everything is working:

```bash
cd ai-brain
chmod +x verify_setup.sh
./verify_setup.sh
```

**What the verification script checks:**
1. ✓ Ollama installation and version
2. ✓ Ollama service status
3. ✓ All required models (qwen2.5:1.5b, deepseek-ocr, mxbai-embed-large)
4. ✓ Python version (3.10+ recommended)
5. ✓ Virtual environment setup
6. ✓ All Python package imports (fastapi, uvicorn, ollama, whisper, torch, httpx)
7. ✓ CUDA availability (if GPU present)
8. ✓ Brain service files (brain.py syntax check)
9. ✓ Optional: Test brain service startup
10. ✓ System resources (disk space, RAM, GPU)

**Expected output:**
```
==========================================
✓ Verification PASSED
==========================================

All components are properly installed and configured!
```

## Troubleshooting Installation

### Common Issues

#### 1. Ollama Not Installed
**Error:** `Ollama is not installed`

**Solution:**
```bash
# Linux/macOS
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Download from https://ollama.ai
```

#### 2. Ollama Service Not Running
**Error:** `Ollama service is not running`

**Solution:**
```bash
ollama serve
```

#### 3. Model Download Failed
**Error:** `Failed to pull qwen2.5:1.5b`

**Solutions:**
- Check internet connection
- Verify Ollama service is running
- Try pulling manually: `ollama pull qwen2.5:1.5b`
- Check disk space (need ~10GB for all models)

#### 4. Python Version Too Old
**Error:** `Python 3.10 or higher required`

**Solution:**
- Install Python 3.10+ from python.org
- Or use pyenv/conda to manage Python versions
- Verify: `python3 --version`

#### 5. Virtual Environment Creation Failed
**Error:** `Failed to create virtual environment`

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install python3-venv

# Then retry
python3 -m venv venv
```

#### 6. Pip Install Failed
**Error:** `Failed to install Python dependencies`

**Solutions:**
1. Upgrade pip:
   ```bash
   pip install --upgrade pip
   ```

2. Install build tools:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install build-essential python3-dev
   
   # macOS
   xcode-select --install
   ```

3. For PyTorch GPU support, visit [pytorch.org](https://pytorch.org) for platform-specific instructions

#### 7. Import Errors During Verification
**Error:** `torch is not installed`

**Solution:**
```bash
# Activate virtual environment first
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Then install missing package
pip install torch
```

## Post-Installation

After successful installation and verification:

### 1. Start the Brain Service

```bash
cd ai-brain
source venv/bin/activate  # Activate venv
python brain.py
```

Expected output:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001
```

### 2. Test the Service

In a new terminal:
```bash
curl http://localhost:8001/
```

Expected response:
```json
{
  "status": "Active",
  "core_model": "qwen2.5:1.5b",
  "mode": "Persistent Core",
  "whisper_loaded": true
}
```

### 3. Integration with Main Backend

The brain service is designed to start automatically with the main backend. See the main project documentation for integration details.

## System Requirements

### Minimum Requirements
- **OS**: Linux, macOS, or Windows
- **VRAM**: 8GB (for Qwen 2.5 1.5B + temporary models)
- **RAM**: 6GB (for Whisper Large-v3)
- **Storage**: ~12GB (for all models)
- **CPU**: Multi-core recommended

### Recommended Requirements
- **VRAM**: 12GB or more
- **RAM**: 8GB or more
- **GPU**: NVIDIA GPU with CUDA support
- **Storage**: 20GB+ (for models and cache)

## Files Created During Installation

```
ai-brain/
├── brain.py                 # Main service (pre-existing)
├── requirements.txt         # Python dependencies (pre-existing)
├── README.md               # Full documentation (pre-existing)
├── QUICKSTART.md           # Quick start guide (pre-existing)
├── install.sh              # Automated installation script
├── verify_setup.sh         # Verification script
├── INSTALLATION_GUIDE.md   # This file
└── venv/                   # Virtual environment (created during install)
    ├── bin/                # Executables (Linux/macOS)
    ├── Scripts/            # Executables (Windows)
    └── lib/                # Installed packages
```

## Next Steps

1. ✓ Installation complete
2. ✓ Verification passed
3. → Start brain service: `python brain.py`
4. → Test endpoints (see README.md)
5. → Integrate with main backend (see main project docs)

## Support

For additional help:
- See README.md for detailed API documentation
- See QUICKSTART.md for manual setup steps
- Check Ollama documentation: https://ollama.ai/docs
- Review troubleshooting section above

## Script Reference

### install.sh
- **Purpose**: Automated installation of all dependencies
- **Usage**: `./install.sh`
- **Requirements**: Bash shell, internet connection
- **Time**: 10-20 minutes

### verify_setup.sh
- **Purpose**: Comprehensive verification of installation
- **Usage**: `./verify_setup.sh`
- **Requirements**: Bash shell, completed installation
- **Time**: 1-2 minutes

Both scripts provide colored output and clear error messages to guide you through any issues.
