# AI Brain Service

A local AI service that orchestrates multiple specialized models for text generation, OCR, audio transcription, and embeddings.

## Overview

The AI Brain Service is a FastAPI application that provides a unified interface for multiple AI capabilities:

- **Text Generation**: Qwen 2.5 1.5B (persistent in VRAM)
- **Vision/OCR**: DeepSeek OCR (load on demand)
- **Audio Transcription**: Whisper Large-v3 (1.5B parameters, loaded in RAM)
- **Text Embeddings**: mxbai-embed-large (load on demand)

## Architecture

The service uses a "Persistent Core" architecture where the primary text generation model (Qwen 2.5 1.5B) remains loaded in VRAM indefinitely, while specialist models are loaded on demand and unloaded after use to conserve memory.

## Prerequisites

### 1. Ollama Installation

Install Ollama from [https://ollama.ai](https://ollama.ai)

**Linux/macOS:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows:**
Download and install from the Ollama website.

### 2. Pull Required Models

After installing Ollama, pull the required models:

```bash
# Core text generation model (1.5GB)
ollama pull qwen2.5:1.5b

# Vision/OCR model (~1GB)
ollama pull deepseek-ocr

# Embedding model (~670MB)
ollama pull mxbai-embed-large
```

### 3. Python Dependencies

Install Python 3.10 or higher, then set up a virtual environment and install the required packages:

**Using venv (recommended):**
```bash
cd ai-brain
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Without venv:**
```bash
cd ai-brain
pip install -r requirements.txt
```

**Note**: PyTorch installation may vary based on your system. For GPU support, visit [pytorch.org](https://pytorch.org) for specific installation instructions.

## Installation Script

For automated setup, use the provided installation script:

```bash
cd ai-brain
chmod +x install.sh
./install.sh
```

The script will:
1. Check if Ollama is installed
2. Verify Ollama service is running
3. Pull all required models (or verify they're already installed)
4. Create Python virtual environment
5. Install Python dependencies
6. Verify the installation

## Verification Script

After installation, verify that everything is working correctly:

```bash
cd ai-brain
chmod +x verify_setup.sh
./verify_setup.sh
```

The verification script will:
1. Check Ollama installation and service status
2. Verify all required models are installed
3. Check Python version (3.10+ recommended)
4. Verify virtual environment setup
5. Test all Python package imports
6. Validate brain.py syntax
7. Optionally test brain service startup
8. Check system resources (disk, RAM, GPU)

This comprehensive verification ensures all components are properly configured before starting the service.

## Usage

### Starting the Service

**Development Mode (with venv):**
```bash
cd ai-brain
source venv/bin/activate  # On Windows: venv\Scripts\activate
python brain.py
```

**Production Mode (with venv):**
```bash
cd ai-brain
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn brain:app --host 0.0.0.0 --port 8001
```

**Without venv:**
```bash
cd ai-brain
python brain.py
```

The service will start on `http://localhost:8001`

### API Endpoints

#### Health Check
```bash
GET /
```

Returns service status and configuration.

**Example:**
```bash
curl http://localhost:8001/
```

**Response:**
```json
{
  "status": "Active",
  "core_model": "qwen2.5:1.5b",
  "mode": "Persistent Core",
  "whisper_loaded": true
}
```

#### Text Generation / OCR / Audio Transcription
```bash
POST /router
```

Intelligent router that handles text, image, and audio requests.

**Parameters:**
- `prompt` (required): Text prompt
- `image` (optional): Image file for OCR
- `audio` (optional): Audio file for transcription

**Example - Text Generation:**
```bash
curl -X POST http://localhost:8001/router \
  -F "prompt=What is the capital of France?"
```

**Example - Image OCR:**
```bash
curl -X POST http://localhost:8001/router \
  -F "prompt=Extract text from this image" \
  -F "image=@document.jpg"
```

**Example - Audio Transcription:**
```bash
curl -X POST http://localhost:8001/router \
  -F "prompt=Transcribe this audio" \
  -F "audio=@recording.wav"
```

**Response:**
```json
{
  "response": "Generated text or extracted content",
  "model": "qwen2.5:1.5b"
}
```

#### Generate Embeddings
```bash
POST /utility/embed
```

Generate vector embeddings for text.

**Parameters:**
- `text` (required): Text to embed

**Example:**
```bash
curl -X POST http://localhost:8001/utility/embed \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world"}'
```

**Response:**
```json
{
  "embedding": [0.123, -0.456, 0.789, ...]
}
```

## Resource Requirements

### Minimum Requirements
- **VRAM**: 8GB (for Qwen 2.5 1.5B + temporary models)
- **RAM**: 6GB (for Whisper Large-v3)
- **Storage**: ~12GB (for all models)
- **CPU**: Multi-core recommended for concurrent requests

### Recommended Requirements
- **VRAM**: 12GB or more
- **RAM**: 8GB or more
- **GPU**: NVIDIA GPU with CUDA support for optimal performance

## Memory Management

The service implements intelligent VRAM management:

1. **Persistent Core**: Qwen 2.5 1.5B stays loaded indefinitely
2. **On-Demand Loading**: Specialist models load only when needed
3. **Automatic Cleanup**: Specialist models unload after each request
4. **CUDA Cache Clearing**: Frees GPU memory after specialist model use
5. **Garbage Collection**: Python garbage collection triggered after cleanup

## Troubleshooting

### Installation Issues

#### Ollama Not Installed
```
Error: Ollama is not installed
```

**Solution**: Install Ollama
```bash
# Linux/macOS
curl -fsSL https://ollama.ai/install.sh | sh

# Windows: Download from https://ollama.ai
```

#### Ollama Service Not Running
```
Error: Failed to connect to Ollama
```

**Solution**: Start Ollama service
```bash
ollama serve
```

#### Model Not Found
```
Error: model 'qwen2.5:1.5b' not found
```

**Solution**: Pull the missing model
```bash
ollama pull qwen2.5:1.5b
```

#### Python Version Too Old
```
Error: Python 3.10 or higher required
```

**Solution**: Install a newer Python version
- Use pyenv, conda, or download from python.org
- Ensure `python3 --version` shows 3.10 or higher

#### Virtual Environment Creation Failed
```
Error: Failed to create virtual environment
```

**Solution**: Install venv module
```bash
# Ubuntu/Debian
sudo apt-get install python3-venv

# macOS (usually included)
# Windows (usually included)
```

#### Pip Install Failed
```
Error: Failed to install Python dependencies
```

**Solutions**:
1. Upgrade pip: `pip install --upgrade pip`
2. Install build tools:
   - Ubuntu/Debian: `sudo apt-get install build-essential python3-dev`
   - macOS: `xcode-select --install`
   - Windows: Install Visual Studio Build Tools

### Runtime Issues

#### Out of VRAM
```
Error: CUDA out of memory
```

**Solutions**:
1. Close other GPU-intensive applications
2. Use a smaller model
3. Increase GPU memory allocation
4. Use CPU-only mode (slower)

#### Whisper Model Loading Failed
```
Warning: Failed to load Whisper model
```

**Solution**: Install whisper dependencies
```bash
pip install openai-whisper
```

#### Port Already in Use
```
Error: Address already in use (port 8001)
```

**Solutions**:
1. Stop the existing service on port 8001
2. Change the port in brain.py
3. Find and kill the process: `lsof -ti:8001 | xargs kill`

#### Brain Service Won't Start
```
Error: Brain service failed to start
```

**Solutions**:
1. Run the verification script: `./verify_setup.sh`
2. Check the logs for specific errors
3. Ensure all models are pulled
4. Verify Python dependencies are installed
5. Check that Ollama service is running

## Integration with Main Backend

The AI Brain Service is designed to be automatically started by the main backend. See the main backend documentation for integration details.

**Manual Integration Example:**
```python
import httpx

async def generate_ai_response(prompt: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8001/router",
            data={"prompt": prompt}
        )
        return response.json()
```

## Logging

The service logs all operations with timestamps:
- Model loading/unloading
- Request processing
- Errors and warnings
- Memory cleanup operations

Logs are written to stdout and can be redirected to a file:
```bash
python brain.py > brain.log 2>&1
```

## Performance Tips

1. **Keep Core Model Loaded**: The persistent core architecture ensures fast text generation
2. **Batch Requests**: Process multiple text requests sequentially for efficiency
3. **GPU Acceleration**: Use CUDA-enabled GPU for optimal performance
4. **Memory Monitoring**: Monitor VRAM usage to prevent out-of-memory errors

## Development

### Running Tests
```bash
pytest tests/
```

### Code Structure
- `brain.py`: Main FastAPI application
- `requirements.txt`: Python dependencies
- `install.sh`: Automated installation script

## License

This service is part of the main application. See the main project LICENSE file.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review Ollama documentation: [https://ollama.ai/docs](https://ollama.ai/docs)
3. Check the main project documentation
