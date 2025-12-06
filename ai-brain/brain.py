"""
AI Brain Service - Local AI Model Orchestration

This FastAPI service manages multiple specialized AI models:
- Qwen 2.5 1.5B: Primary text generation (persistent in VRAM)
- DeepSeek OCR: Vision/OCR processing (load on demand)
- Whisper Large-v3: Audio transcription (1.5B parameters, loaded in RAM)
- mxbai-embed-large: Text embeddings (load on demand)
"""

import os
import gc
import logging
import tempfile
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import ollama
import torch
import fitz  # PyMuPDF for PDF processing
from PIL import Image
import io

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="AI Brain Service", version="1.0.0")

# Configure CORS to allow requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Model configuration
CORE_MODEL = "qwen2.5:1.5b"
VISION_MODEL = "qwen2.5vl:3b"
EMBEDDING_MODEL = "mxbai-embed-large"

# Whisper model (loaded in RAM)
whisper_model = None


def load_whisper_model():
    """Load Whisper Large-v3 model into RAM at startup"""
    global whisper_model
    
    try:
        import whisper
        logger.info("Attempting to load Whisper Large-v3 model into RAM...")
        logger.info("Note: This may take a few minutes on first run (downloading ~3GB)")
        whisper_model = whisper.load_model("large-v3")
        logger.info("✓ Whisper Large-v3 model loaded successfully - audio transcription enabled")
    except Exception as e:
        logger.warning(f"⚠ Whisper model not loaded: {e}")
        logger.warning("Audio transcription will be disabled")
        logger.warning("The brain service will continue without audio support")
        whisper_model = None


def is_pdf(file: UploadFile) -> bool:
    """Check if uploaded file is a PDF"""
    return (
        file.content_type == "application/pdf" or
        (file.filename and file.filename.lower().endswith('.pdf'))
    )


async def process_pdf_with_ocr(pdf_content: bytes, prompt: str) -> str:
    """
    Process PDF by converting pages to images and running OCR on each page.
    
    Args:
        pdf_content: PDF file content as bytes
        prompt: User prompt for context
        
    Returns:
        Combined extracted text from all pages
    """
    try:
        logger.info("Processing PDF document...")
        
        # Open PDF from bytes
        pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
        total_pages = pdf_document.page_count
        logger.info(f"PDF has {total_pages} pages")
        
        all_text = []
        
        # Process each page
        for page_num in range(total_pages):
            logger.info(f"Processing page {page_num + 1}/{total_pages}")
            
            # Get page
            page = pdf_document[page_num]
            
            # Convert page to image (PNG format, 300 DPI for good quality)
            pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
            img_bytes = pix.tobytes("png")
            
            # Process with DeepSeek OCR
            response = ollama.generate(
                model=VISION_MODEL,
                prompt=f"{prompt}\n\nPage {page_num + 1} of {total_pages}:",
                images=[img_bytes],
                keep_alive=0
            )
            
            page_text = response['response']
            all_text.append(f"--- Page {page_num + 1} ---\n{page_text}")
            logger.info(f"Page {page_num + 1}: Extracted {len(page_text)} characters")
        
        pdf_document.close()
        
        # Combine all pages
        combined_text = "\n\n".join(all_text)
        logger.info(f"PDF processing complete: {len(combined_text)} total characters from {total_pages} pages")
        
        return combined_text
        
    except Exception as e:
        logger.error(f"PDF processing error: {e}")
        raise


def cleanup_temporary_resources(model_name: Optional[str] = None):
    """
    Unload specialist models and clear VRAM.
    Never unloads the core Qwen 2.5 1.5B model.
    
    Args:
        model_name: Specific model to unload (optional)
    """
    if model_name and model_name == CORE_MODEL:
        logger.warning(f"Attempted to unload core model {CORE_MODEL} - ignoring")
        return
    
    try:
        if model_name:
            logger.info(f"Unloading specialist model: {model_name}")
            # Send keep_alive: 0 to Ollama to unload the model
            ollama.generate(model=model_name, prompt="", keep_alive=0)
        
        # Clear CUDA cache if available
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.info("CUDA cache cleared")
        
        # Trigger garbage collection
        gc.collect()
        logger.info("Garbage collection completed")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")


@app.on_event("startup")
async def startup_event():
    """Initialize the brain service on startup"""
    logger.info("Starting AI Brain Service...")
    
    # Check if Ollama is running
    try:
        ollama.list()
        logger.info("Ollama connection verified")
    except Exception as e:
        logger.error(f"Failed to connect to Ollama: {e}")
        logger.error("Please ensure Ollama is running on localhost:11434")
        raise RuntimeError("Ollama service not available")
    
    # Load core model with persistent keep_alive
    try:
        logger.info(f"Loading core model {CORE_MODEL} with persistent keep_alive...")
        ollama.generate(
            model=CORE_MODEL,
            prompt="Initialize",
            keep_alive=-1  # Keep loaded indefinitely
        )
        logger.info(f"Core model {CORE_MODEL} loaded and will remain in VRAM")
    except Exception as e:
        logger.error(f"Failed to load core model: {e}")
        raise RuntimeError(f"Failed to load core model {CORE_MODEL}")
    
    # Load Whisper model (optional - won't block startup if it fails)
    try:
        load_whisper_model()
    except Exception as e:
        logger.warning(f"Whisper loading skipped: {e}")
        logger.warning("Continuing without audio transcription support")
    
    logger.info("=" * 60)
    logger.info("AI Brain Service startup complete")
    logger.info(f"Configuration: Core Model={CORE_MODEL}, Mode=Persistent Core")
    logger.info(f"Audio Support: {'Enabled' if whisper_model else 'Disabled (Whisper not loaded)'}")
    logger.info("=" * 60)


@app.get("/")
def home():
    """Health check endpoint"""
    return {
        "status": "Active",
        "core_model": CORE_MODEL,
        "mode": "Persistent Core",
        "whisper_loaded": whisper_model is not None
    }


@app.post("/router")
async def intelligent_router(
    prompt: str = Form(...),
    image: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None)
):
    """
    Intelligent router that handles text, image, and audio requests.
    
    Args:
        prompt: Text prompt for the AI
        image: Optional image file for OCR processing
        audio: Optional audio file for transcription
    
    Returns:
        dict: Response containing generated text and model name
    """
    try:
        logger.info(f"Router request - prompt length: {len(prompt)}, "
                   f"has_image: {image is not None}, has_audio: {audio is not None}")
        
        # Handle audio transcription if audio file provided
        if audio:
            if whisper_model:
                try:
                    logger.info(f"Processing audio file: {audio.filename}")
                    # Save audio to temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
                        content = await audio.read()
                        temp_audio.write(content)
                        temp_audio_path = temp_audio.name
                    
                    # Transcribe audio
                    result = whisper_model.transcribe(temp_audio_path)
                    transcribed_text = result["text"]
                    logger.info(f"Audio transcribed: {transcribed_text[:100]}...")
                    
                    # Clean up temporary file
                    os.unlink(temp_audio_path)
                    
                    # Use transcribed text as prompt
                    prompt = transcribed_text
                    
                except Exception as e:
                    logger.error(f"Audio transcription failed: {e}")
                    # Continue with original prompt if transcription fails
            else:
                logger.warning("Audio file provided but Whisper model not loaded - skipping transcription")
                logger.warning("Using original text prompt instead")
        
        # Handle image/PDF OCR if file provided
        if image:
            try:
                logger.info(f"Processing file: {image.filename}")
                file_content = await image.read()
                
                # Check if it's a PDF
                if is_pdf(image):
                    logger.info("Detected PDF file - processing with multi-page OCR")
                    extracted_text = await process_pdf_with_ocr(file_content, prompt)
                else:
                    # Regular image processing
                    logger.info(f"Processing image with {VISION_MODEL}")
                    response = ollama.generate(
                        model=VISION_MODEL,
                        prompt=prompt,
                        images=[file_content],
                        keep_alive=0  # Unload immediately after use
                    )
                    extracted_text = response['response']
                
                logger.info(f"OCR extraction complete: {len(extracted_text)} characters")
                
                # Cleanup vision model
                cleanup_temporary_resources(VISION_MODEL)
                
                return {
                    "response": extracted_text,
                    "model": VISION_MODEL
                }
                
            except Exception as e:
                logger.error(f"File processing failed: {e}")
                return {
                    "response": f"Error processing file: {str(e)}",
                    "model": VISION_MODEL
                }
        
        # Default: Text generation with core model
        logger.info(f"Generating text response with {CORE_MODEL}")
        response = ollama.generate(
            model=CORE_MODEL,
            prompt=prompt,
            keep_alive=-1  # Keep core model loaded
        )
        
        generated_text = response['response']
        logger.info(f"Text generation complete: {len(generated_text)} characters")
        
        return {
            "response": generated_text,
            "model": CORE_MODEL
        }
        
    except Exception as e:
        logger.error(f"Router error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/utility/embed")
async def process_embedding(text: str):
    """
    Generate embedding vector for text.
    
    Args:
        text: Text to embed
    
    Returns:
        dict: Embedding vector
    """
    try:
        logger.info(f"Generating embedding for text length: {len(text)}")
        
        # Load embedding model with immediate unload
        response = ollama.embeddings(
            model=EMBEDDING_MODEL,
            prompt=text,
            keep_alive=0  # Unload immediately
        )
        
        embedding = response['embedding']
        logger.info(f"Embedding generated: {len(embedding)} dimensions")
        
        # Cleanup embedding model
        cleanup_temporary_resources(EMBEDDING_MODEL)
        
        return {"embedding": embedding}
        
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
