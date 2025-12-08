#!/bin/bash

# AI Brain Service Startup Verification Script
# This script verifies that all components are properly installed and working

set -e  # Exit on error

echo "=========================================="
echo "AI Brain Service Verification"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Track verification status
VERIFICATION_PASSED=true

# Function to mark verification as failed
mark_failed() {
    VERIFICATION_PASSED=false
}

# 1. Verify Ollama Installation
echo "Step 1: Verifying Ollama installation..."
if command -v ollama &> /dev/null; then
    OLLAMA_VERSION=$(ollama --version 2>&1 | head -n 1)
    print_success "Ollama is installed: $OLLAMA_VERSION"
else
    print_error "Ollama is not installed"
    mark_failed
fi

# 2. Verify Ollama Service
echo ""
echo "Step 2: Verifying Ollama service..."
if ollama list &> /dev/null; then
    print_success "Ollama service is running"
else
    print_error "Ollama service is not running"
    print_info "Start with: ollama serve"
    mark_failed
fi

# 3. Verify Required Models
echo ""
echo "Step 3: Verifying required models..."

# Check Qwen 2.5 1.5B
if ollama list 2>/dev/null | grep -q "qwen2.5:1.5b"; then
    print_success "qwen2.5:1.5b is installed"
else
    print_error "qwen2.5:1.5b is not installed"
    print_info "Install with: ollama pull qwen2.5:1.5b"
    mark_failed
fi

# Check DeepSeek OCR
if ollama list 2>/dev/null | grep -q "deepseek-ocr"; then
    print_success "deepseek-ocr is installed"
else
    print_error "deepseek-ocr is not installed"
    print_info "Install with: ollama pull deepseek-ocr"
    mark_failed
fi

# Check mxbai-embed-large
if ollama list 2>/dev/null | grep -q "mxbai-embed-large"; then
    print_success "mxbai-embed-large is installed"
else
    print_error "mxbai-embed-large is not installed"
    print_info "Install with: ollama pull mxbai-embed-large"
    mark_failed
fi

# 4. Verify Python Installation
echo ""
echo "Step 4: Verifying Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    print_success "Python is installed: $PYTHON_VERSION"
    
    # Check Python version (need 3.10+)
    PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
    PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
    
    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
        print_success "Python version is 3.10 or higher"
    else
        print_warning "Python version is below 3.10 (recommended: 3.10+)"
    fi
else
    print_error "Python 3 is not installed"
    mark_failed
fi

# 5. Verify Virtual Environment
echo ""
echo "Step 5: Verifying virtual environment..."
if [ -d "venv" ]; then
    print_success "Virtual environment exists"
    
    # Check if we're in the virtual environment
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        print_success "Virtual environment is activated"
    else
        print_warning "Virtual environment is not activated"
        print_info "Activate with: source venv/bin/activate"
    fi
else
    print_warning "Virtual environment not found"
    print_info "Create with: python3 -m venv venv"
fi

# 6. Verify Python Dependencies
echo ""
echo "Step 6: Verifying Python dependencies..."

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found"
    mark_failed
else
    print_success "requirements.txt found"
fi

# Test critical imports
print_info "Testing Python package imports..."

# FastAPI
if python3 -c "import fastapi" 2>/dev/null; then
    print_success "fastapi is installed"
else
    print_error "fastapi is not installed"
    mark_failed
fi

# Uvicorn
if python3 -c "import uvicorn" 2>/dev/null; then
    print_success "uvicorn is installed"
else
    print_error "uvicorn is not installed"
    mark_failed
fi

# Ollama Python client
if python3 -c "import ollama" 2>/dev/null; then
    print_success "ollama (Python client) is installed"
else
    print_error "ollama (Python client) is not installed"
    mark_failed
fi

# Whisper
if python3 -c "import whisper" 2>/dev/null; then
    print_success "whisper is installed"
else
    print_error "whisper is not installed"
    mark_failed
fi

# PyTorch
if python3 -c "import torch" 2>/dev/null; then
    print_success "torch (PyTorch) is installed"
    
    # Check CUDA availability
    CUDA_AVAILABLE=$(python3 -c "import torch; print(torch.cuda.is_available())" 2>/dev/null)
    if [ "$CUDA_AVAILABLE" = "True" ]; then
        CUDA_VERSION=$(python3 -c "import torch; print(torch.version.cuda)" 2>/dev/null)
        print_success "CUDA is available (version: $CUDA_VERSION)"
    else
        print_warning "CUDA is not available (CPU-only mode)"
    fi
else
    print_error "torch (PyTorch) is not installed"
    mark_failed
fi

# httpx
if python3 -c "import httpx" 2>/dev/null; then
    print_success "httpx is installed"
else
    print_warning "httpx is not installed (optional)"
fi

# 7. Verify Brain Service Files
echo ""
echo "Step 7: Verifying brain service files..."

if [ -f "brain.py" ]; then
    print_success "brain.py found"
    
    # Check if brain.py has syntax errors
    if python3 -m py_compile brain.py 2>/dev/null; then
        print_success "brain.py has valid Python syntax"
    else
        print_error "brain.py has syntax errors"
        mark_failed
    fi
else
    print_error "brain.py not found"
    mark_failed
fi

if [ -f "README.md" ]; then
    print_success "README.md found"
else
    print_warning "README.md not found"
fi

# 8. Test Brain Service Startup (optional)
echo ""
echo "Step 8: Testing brain service startup (optional)..."
print_info "Attempting to start brain service for 5 seconds..."

# Start brain service in background
python3 brain.py > /tmp/brain_test.log 2>&1 &
BRAIN_PID=$!

# Wait for service to start
sleep 5

# Check if process is still running
if ps -p $BRAIN_PID > /dev/null 2>&1; then
    print_success "Brain service started successfully"
    
    # Try to connect to the service
    if command -v curl &> /dev/null; then
        if curl -s http://localhost:8001/ > /dev/null 2>&1; then
            print_success "Brain service is responding on port 8001"
        else
            print_warning "Brain service is running but not responding"
        fi
    fi
    
    # Stop the test service
    kill $BRAIN_PID 2>/dev/null
    wait $BRAIN_PID 2>/dev/null
    print_info "Test service stopped"
else
    print_error "Brain service failed to start"
    print_info "Check logs at: /tmp/brain_test.log"
    mark_failed
fi

# 9. System Resource Check
echo ""
echo "Step 9: Checking system resources..."

# Check available disk space
if command -v df &> /dev/null; then
    DISK_SPACE=$(df -h . | awk 'NR==2 {print $4}')
    print_info "Available disk space: $DISK_SPACE"
fi

# Check available RAM
if command -v free &> /dev/null; then
    AVAILABLE_RAM=$(free -h | awk 'NR==2 {print $7}')
    print_info "Available RAM: $AVAILABLE_RAM"
elif command -v vm_stat &> /dev/null; then
    # macOS
    print_info "RAM check: Use 'vm_stat' for details"
fi

# Check GPU (if nvidia-smi is available)
if command -v nvidia-smi &> /dev/null; then
    print_info "GPU detected:"
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null | while read line; do
        print_info "  $line"
    done
else
    print_warning "nvidia-smi not found (GPU check skipped)"
fi

# Final Summary
echo ""
echo "=========================================="
if [ "$VERIFICATION_PASSED" = true ]; then
    echo -e "${GREEN}✓ Verification PASSED${NC}"
    echo "=========================================="
    echo ""
    echo "All components are properly installed and configured!"
    echo ""
    echo "Next steps:"
    echo "  1. Start the brain service:"
    echo "     cd ai-brain"
    echo "     source venv/bin/activate  # If using venv"
    echo "     python brain.py"
    echo ""
    echo "  2. Test the service:"
    echo "     curl http://localhost:8001/"
    echo ""
    echo "  3. Start the main backend (in another terminal):"
    echo "     cd python-backend"
    echo "     python main.py"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Verification FAILED${NC}"
    echo "=========================================="
    echo ""
    echo "Some components are missing or not properly configured."
    echo "Please review the errors above and fix them."
    echo ""
    echo "Common fixes:"
    echo "  - Install missing models: ollama pull <model-name>"
    echo "  - Install Python packages: pip install -r requirements.txt"
    echo "  - Start Ollama service: ollama serve"
    echo ""
    echo "For detailed setup instructions, see README.md"
    echo ""
    exit 1
fi
