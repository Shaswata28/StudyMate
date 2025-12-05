#!/bin/bash

# AI Brain Service Installation Script
# This script installs all dependencies and sets up the AI Brain service

set -e  # Exit on error

echo "=========================================="
echo "AI Brain Service Installation"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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
    echo -e "ℹ $1"
}

# Check if Ollama is installed
echo "Step 1: Checking Ollama installation..."
if command -v ollama &> /dev/null; then
    print_success "Ollama is installed"
    OLLAMA_VERSION=$(ollama --version 2>&1 | head -n 1)
    print_info "Version: $OLLAMA_VERSION"
else
    print_error "Ollama is not installed"
    echo ""
    echo "Please install Ollama first:"
    echo "  Linux/macOS: curl -fsSL https://ollama.ai/install.sh | sh"
    echo "  Windows: Download from https://ollama.ai"
    echo ""
    exit 1
fi

# Check if Ollama service is running
echo ""
echo "Step 2: Checking Ollama service..."
if ollama list &> /dev/null; then
    print_success "Ollama service is running"
else
    print_warning "Ollama service is not running"
    echo "Starting Ollama service..."
    ollama serve &
    sleep 3
    if ollama list &> /dev/null; then
        print_success "Ollama service started"
    else
        print_error "Failed to start Ollama service"
        echo "Please start Ollama manually: ollama serve"
        exit 1
    fi
fi

# Pull required Ollama models
echo ""
echo "Step 3: Pulling required Ollama models..."
echo "This may take several minutes depending on your internet connection."
echo ""

# Check and pull Qwen 2.5 1.5B
print_info "Checking qwen2.5:1.5b (~1.5GB)..."
if ollama list | grep -q "qwen2.5:1.5b"; then
    print_success "qwen2.5:1.5b already installed"
else
    echo "Pulling qwen2.5:1.5b..."
    if ollama pull qwen2.5:1.5b; then
        print_success "qwen2.5:1.5b installed"
    else
        print_error "Failed to pull qwen2.5:1.5b"
        exit 1
    fi
fi

# Check and pull DeepSeek OCR
print_info "Checking deepseek-ocr (~1GB)..."
if ollama list | grep -q "deepseek-ocr"; then
    print_success "deepseek-ocr already installed"
else
    echo "Pulling deepseek-ocr..."
    if ollama pull deepseek-ocr; then
        print_success "deepseek-ocr installed"
    else
        print_error "Failed to pull deepseek-ocr"
        exit 1
    fi
fi

# Check and pull mxbai-embed-large
print_info "Checking mxbai-embed-large (~670MB)..."
if ollama list | grep -q "mxbai-embed-large"; then
    print_success "mxbai-embed-large already installed"
else
    echo "Pulling mxbai-embed-large..."
    if ollama pull mxbai-embed-large; then
        print_success "mxbai-embed-large installed"
    else
        print_error "Failed to pull mxbai-embed-large"
        exit 1
    fi
fi

# Check Python installation
echo ""
echo "Step 4: Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    print_success "Python is installed: $PYTHON_VERSION"
else
    print_error "Python 3 is not installed"
    echo "Please install Python 3.10 or higher"
    exit 1
fi

# Set up virtual environment and install Python dependencies
echo ""
echo "Step 5: Setting up Python virtual environment..."
if [ -d "venv" ]; then
    print_info "Virtual environment already exists"
else
    print_info "Creating virtual environment..."
    if python3 -m venv venv; then
        print_success "Virtual environment created"
    else
        print_error "Failed to create virtual environment"
        exit 1
    fi
fi

# Activate virtual environment
print_info "Activating virtual environment..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    print_success "Virtual environment activated"
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
    print_success "Virtual environment activated"
else
    print_error "Could not find activation script"
    exit 1
fi

# Install Python dependencies
echo ""
echo "Step 6: Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    print_info "Installing packages from requirements.txt..."
    if pip install -r requirements.txt; then
        print_success "Python dependencies installed"
    else
        print_error "Failed to install Python dependencies"
        echo "You may need to upgrade pip: pip install --upgrade pip"
        exit 1
    fi
else
    print_error "requirements.txt not found"
    echo "Please run this script from the ai-brain directory"
    exit 1
fi

# Verify installation
echo ""
echo "Step 7: Verifying installation..."

# Check if brain.py exists
if [ -f "brain.py" ]; then
    print_success "brain.py found"
else
    print_error "brain.py not found"
    exit 1
fi

# Test imports
print_info "Testing Python imports..."
python3 -c "import fastapi, uvicorn, ollama, whisper, torch" 2>/dev/null
if [ $? -eq 0 ]; then
    print_success "All Python packages imported successfully"
else
    print_warning "Some Python packages may not be properly installed"
fi

# Installation complete
echo ""
echo "=========================================="
echo -e "${GREEN}Installation Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Run the verification script to confirm everything is working:"
echo "     chmod +x verify_setup.sh"
echo "     ./verify_setup.sh"
echo ""
echo "  2. Activate the virtual environment:"
echo "     cd ai-brain"
echo "     source venv/bin/activate  # On Windows: venv\\Scripts\\activate"
echo ""
echo "  3. Start the AI Brain service:"
echo "     python brain.py"
echo ""
echo "  4. The service will be available at:"
echo "     http://localhost:8001"
echo ""
echo "  5. Test the service:"
echo "     curl http://localhost:8001/"
echo ""
echo "For more information, see README.md"
echo ""
