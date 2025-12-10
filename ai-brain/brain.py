"""
AI Brain Service - Local AI Model Orchestration

This FastAPI service manages multiple specialized AI models:
- StudyMate (Qwen 2.5 Fine-tuned): Primary text generation (persistent in VRAM)
- qwen 2.5vl: Vision/OCR processing (load on demand)
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

# --- CONFIGURATION CHANGES ---
CORE_MODEL = "studymate"        # Your fine-tuned model
VISION_MODEL = "qwen2.5vl:3b"   # Your vision model
EMBEDDING_MODEL = "mxbai-embed-large"


def is_pdf(file: UploadFile) -> bool:
    """Check if uploaded file is a PDF"""
    return (
        file.content_type == "application/pdf" or
        (file.filename and file.filename.lower().endswith('.pdf'))
    )


async def process_pdf_with_ocr(pdf_content: bytes, prompt: str) -> str:
    """
    Process PDF by converting pages to images and running OCR on each page.
    """
    try:
        logger.info("Processing PDF document...")
        
        # Open PDF from bytes
        pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
        total_pages = pdf_document.page_count
        logger.info(f"PDF has {total_pages} pages")
        
        all_text = []
        
        # Process each page with progress tracking
        for page_num in range(total_pages):
            try:
                logger.info(f"Processing page {page_num + 1}/{total_pages} - Starting OCR...")
                
                # Get page
                page = pdf_document[page_num]
                
                # Convert page to image (PNG format, 300 DPI for good quality)
                pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
                img_bytes = pix.tobytes("png")
                
                logger.info(f"Page {page_num + 1}: Image converted, sending to vision model...")
                
                # Process with DeepSeek OCR - this is the slow part
                response = ollama.generate(
                    model=VISION_MODEL,
                    prompt=f"{prompt}\n\nPage {page_num + 1} of {total_pages}:",
                    images=[img_bytes],
                    keep_alive=0
                )
                
                page_text = response['response']
                all_text.append(f"--- Page {page_num + 1} ---\n{page_text}")
                
                # Progress update
                progress_percent = ((page_num + 1) / total_pages) * 100
                logger.info(f"Page {page_num + 1}/{total_pages} complete: {len(page_text)} characters extracted ({progress_percent:.1f}% done)")
                
            except Exception as page_error:
                logger.error(f"Error processing page {page_num + 1}: {page_error}")
                # Continue with other pages instead of failing completely
                all_text.append(f"--- Page {page_num + 1} ---\n[Error processing this page: {str(page_error)}]")
                continue
        
        pdf_document.close()
        
        # Combine all pages
        combined_text = "\n\n".join(all_text)
        
        # Final summary
        successful_pages = len([text for text in all_text if not text.startswith("[Error")])
        logger.info(f"🎉 PDF processing complete!")
        logger.info(f"📊 Successfully processed {successful_pages}/{total_pages} pages")
        logger.info(f"📝 Total extracted text: {len(combined_text)} characters")
        
        return combined_text
        
    except Exception as e:
        logger.error(f"PDF processing error: {e}")
        raise


def cleanup_temporary_resources(model_name: Optional[str] = None):
    """
    Unload specialist models and clear VRAM.
    Never unloads the core StudyMate model.
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
    
    logger.info("=" * 60)
    logger.info("AI Brain Service startup complete")
    logger.info(f"Configuration: Core Model={CORE_MODEL}, Mode=Persistent Core")
    logger.info("=" * 60)


@app.get("/")
def home():
    """Health check endpoint"""
    return {
        "status": "Active",
        "core_model": CORE_MODEL,
        "mode": "Persistent Core"
    }


@app.post("/router")
async def intelligent_router(
    prompt: str = Form(...),
    image: Optional[UploadFile] = File(None)
):
    """
    Intelligent router that handles text and image requests.
    """
    try:
        logger.info(f"Router request - prompt length: {len(prompt)}, "
                   f"has_image: {image is not None}")
        
        # Handle image/PDF OCR if file provided
        if image:
            try:
                logger.info(f"Processing file: {image.filename}")
                file_content = await image.read()
                
                # Check if it's a PDF
                if is_pdf(image):
                    logger.info(f"Detected PDF file: {image.filename} - starting multi-page OCR processing...")
                    logger.info("⚠️  Large PDFs may take several minutes to process. Please wait...")
                    extracted_text = await process_pdf_with_ocr(file_content, prompt)
                    logger.info("✅ PDF processing completed successfully!")
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
        
        # Generate response with fine-tuned StudyMate model
        logger.info(f"Generating text response with {CORE_MODEL}")
        
        # IMPORTANT: StudyMate is fine-tuned on Alpaca format
        # If the prompt doesn't already contain Alpaca structure, wrap it
        if "### Instruction:" not in prompt and "### Input:" not in prompt:
            # This is a raw prompt - wrap it in Alpaca format
            alpaca_prompt = f"""Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
You are StudyMate, a helpful AI study assistant.

### Input:
{prompt}

### Response:
"""
            logger.info("Wrapped raw prompt in Alpaca format for fine-tuned model")
        else:
            # This is already in Alpaca format - use as-is
            alpaca_prompt = prompt
            logger.info("Using pre-formatted Alpaca prompt")
        
        response = ollama.generate(
            model=CORE_MODEL,
            prompt=alpaca_prompt,
            keep_alive=-1,
            options={
                # Minimal stop tokens - let fine-tuned model handle stopping naturally
                "stop": ["<|endoftext|>", "### Instruction:", "### Input:"],
                "temperature": 0.7,  # Slightly higher for more natural responses
                "num_ctx": 4096
            }
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
    # Configure uvicorn with longer timeout for large document processing
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8001, 
        log_level="info",
        timeout_keep_alive=300,  # 5 minutes keep-alive
        timeout_graceful_shutdown=30
    )