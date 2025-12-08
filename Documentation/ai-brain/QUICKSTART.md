# AI Brain Service - Quick Start Guide

## Automated Installation (Recommended)

For a fully automated setup, use the installation script:

**Linux/macOS:**
```bash
cd ai-brain
chmod +x install.sh
./install.sh
```

The script will automatically:
- Check Ollama installation
- Pull required models
- Create virtual environment
- Install Python dependencies
- Verify the installation

After running the install script, skip to step 7 below.

## Manual Setup Steps

### 1. Navigate to ai-brain directory
```bash
cd ai-brain
```

### 2. Create virtual environment
**Windows:**
```cmd
python -m venv venv
```

**Linux/macOS:**
```bash
python3 -m venv venv
```

### 3. Activate virtual environment
**Windows (Command Prompt):**
```cmd
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

**Linux/macOS:**
```bash
source venv/bin/activate
```

You should see `(venv)` prefix in your terminal prompt.

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

This will install:
- FastAPI & Uvicorn (web framework)
- Ollama (model client)
- Whisper (audio transcription)
- PyTorch (ML operations)
- Other required packages

### 5. Verify Ollama models (optional)
Check that required models are installed:
```bash
ollama list
```

You should see:
- qwen2.5:1.5b
- deepseek-ocr
- mxbai-embed-large

If any are missing, pull them:
```bash
ollama pull qwen2.5:1.5b
ollama pull deepseek-ocr
ollama pull mxbai-embed-large
```

### 6. Run verification script (recommended)
Verify that everything is properly installed:

**Linux/macOS:**
```bash
chmod +x verify_setup.sh
./verify_setup.sh
```

**Windows (Git Bash):**
```bash
bash verify_setup.sh
```

This will check:
- Ollama installation and service
- All required models
- Python version and packages
- Brain service files
- System resources

### 7. Start the brain service
```bash
python brain.py
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001
```

### 8. Test the service
Open a new terminal and test:
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

## Common Issues

### Virtual environment not activating (Windows PowerShell)
If you get an execution policy error:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Ollama not running
Start Ollama service:
```bash
ollama serve
```

### Port 8001 already in use
Change the port in brain.py or stop the process using port 8001.

### PyTorch installation issues
For GPU support, visit [pytorch.org](https://pytorch.org) for platform-specific installation instructions.

## Stopping the Service

Press `Ctrl+C` in the terminal where brain.py is running.

## Deactivating Virtual Environment

When done, deactivate the virtual environment:
```bash
deactivate
```

## Next Steps

Once the brain service is running, you can:
1. Integrate it with the main backend (see main project documentation)
2. Test the API endpoints (see README.md for examples)
3. Monitor logs for debugging

For detailed API documentation, see README.md
