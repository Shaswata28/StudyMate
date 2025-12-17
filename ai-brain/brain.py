"""
AI Brain Service - Local AI Model Orchestration
Optimized for Non-Blocking Async Execution
"""

import logging
import re
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
import ollama
import fitz  # PyMuPDF
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
CORE_MODEL = "Studymate-core"
VISION_MODEL = "qwen2.5vl:3b"
EMBEDDING_MODEL = "mxbai-embed-large"

# Initialize Async Client
client = ollama.AsyncClient()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup/shutdown in FastAPI."""
    # --- STARTUP ---
    logger.info("Starting AI Brain Service...")
    
    # 1. Verify Ollama Connection
    try:
        await client.list()
        logger.info("✅ Ollama connection verified")
    except Exception as e:
        logger.critical(f"❌ Failed to connect to Ollama: {e}")
        raise RuntimeError("Ollama service not available")
    
    # 2. Pre-load Core Model
    try:
        logger.info(f"🧠 Loading core model {CORE_MODEL} into VRAM...")
        await client.generate(model=CORE_MODEL, prompt="", keep_alive=-1)
        logger.info(f"✅ Core model loaded & locked in VRAM")
    except Exception as e:
        logger.error(f"❌ Failed to load core model: {e}")
    
    logger.info("=" * 60)
    logger.info("AI Brain Service startup complete")
    logger.info(f"Core Model: {CORE_MODEL} (persistent in VRAM)")
    logger.info(f"Vision Model: {VISION_MODEL} (load on demand)")
    logger.info(f"Embedding Model: {EMBEDDING_MODEL} (load on demand)")
    logger.info("=" * 60)
    
    yield
    
    # --- SHUTDOWN ---
    logger.info("🛑 Shutting down. Unloading models...")
    try:
        await client.generate(model=CORE_MODEL, prompt="", keep_alive=0)
    except:
        pass


app = FastAPI(title="AI Brain Service", version="1.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def is_pdf(file: UploadFile) -> bool:
    """Check if uploaded file is a PDF"""
    return (
        file.content_type == "application/pdf" or
        (file.filename and file.filename.lower().endswith('.pdf'))
    )


def clean_model_response(text: str) -> str:
    """
    Clean model output by removing training artifacts and reasoning leakage.
    
    Handles:
    - ### Instruction: blocks (model generating fake follow-up prompts)
    - User Context / [PROFILE] blocks leaked into output
    - Response: prefixes
    - Duplicate content
    """
    if not text:
        return text
    
    original_len = len(text)
    
    # 1. Cut off at any "### Instruction:" - model is hallucinating new prompts
    instruction_patterns = [
        r'\n\s*###\s*Instruction:.*',
        r'\n\s*### Instruction:.*',
        r'\n\s*\[INST\].*',
        r'\n\s*<\|im_start\|>user.*',
    ]
    for pattern in instruction_patterns:
        text = re.split(pattern, text, flags=re.IGNORECASE | re.DOTALL)[0]
    
    # 2. Cut off at "User Context" blocks (training format leaking)
    context_patterns = [
        r'\n\s*User Context \(Academic Info.*',
        r'\n\s*\[PROFILE\].*',
        r'\n\s*You are StudyMate\..*\[PROFILE\].*',
    ]
    for pattern in context_patterns:
        text = re.split(pattern, text, flags=re.IGNORECASE | re.DOTALL)[0]
    
    # 3. Remove "Response:" prefix if model outputs it
    text = re.sub(r'^Response:\s*', '', text.strip(), flags=re.IGNORECASE)
    
    # 4. Remove any trailing incomplete sentences after cutoff
    text = text.strip()
    if text and not text[-1] in '.!?:"\')]}':
        # Find last complete sentence
        last_punct = max(
            text.rfind('. '),
            text.rfind('.\n'),
            text.rfind('! '),
            text.rfind('!\n'),
            text.rfind('? '),
            text.rfind('?\n'),
        )
        if last_punct > len(text) * 0.5:  # Only trim if we keep >50% of content
            text = text[:last_punct + 1]
    
    # 5. Remove duplicate paragraphs
    text = remove_duplicate_content(text)
    
    if len(text) < original_len:
        logger.info(f"Cleaned response: {original_len} -> {len(text)} chars")
    
    return text.strip()


def remove_duplicate_content(text: str) -> str:
    """Remove duplicate/repeated content from model output."""
    if not text or len(text) < 200:
        return text
    
    paragraphs = text.split('\n\n')
    if len(paragraphs) < 2:
        return text
    
    seen = set()
    unique_paragraphs = []
    
    for para in paragraphs:
        normalized = para.strip().lower()
        if not normalized:
            continue
        if normalized in seen:
            continue
        
        is_duplicate = False
        for seen_para in seen:
            if len(normalized) > 50 and (normalized in seen_para or seen_para in normalized):
                is_duplicate = True
                break
        
        if not is_duplicate:
            seen.add(normalized)
            unique_paragraphs.append(para)
    
    return '\n\n'.join(unique_paragraphs)


def _cpu_bound_pdf_extraction(pdf_content: bytes) -> list[bytes]:
    """Synchronous PDF image extraction (CPU-bound)."""
    doc = fitz.open(stream=pdf_content, filetype="pdf")
    images = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
        img_bytes = pix.tobytes("png")
        images.append(img_bytes)
    
    doc.close()
    return images


async def process_pdf_pipeline(pdf_content: bytes, prompt: str) -> str:
    """Async PDF processing pipeline."""
    logger.info("📄 Parsing PDF (CPU Bound)...")
    
    images = await run_in_threadpool(_cpu_bound_pdf_extraction, pdf_content)
    total_pages = len(images)
    logger.info(f"📄 Extracted {total_pages} pages. Starting AI Vision analysis...")
    
    all_text = []
    
    for i, img_bytes in enumerate(images):
        try:
            logger.info(f"Processing page {i+1}/{total_pages}...")
            
            response = await client.generate(
                model=VISION_MODEL,
                prompt=f"{prompt}\n\nPage {i + 1} of {total_pages}:",
                images=[img_bytes],
                keep_alive="5m"
            )
            
            page_text = response['response']
            all_text.append(f"--- Page {i + 1} ---\n{page_text}")
            logger.info(f"✅ Page {i+1}/{total_pages} complete ({len(page_text)} chars)")
            
        except Exception as e:
            logger.error(f"❌ Error processing page {i+1}: {e}")
            all_text.append(f"--- Page {i + 1} ---\n[Error: {str(e)}]")
    
    await client.generate(model=VISION_MODEL, prompt="", keep_alive=0)
    logger.info(f"🎉 PDF processing complete: {total_pages} pages")
    
    return "\n\n".join(all_text)


@app.get("/")
def health_check():
    """Health check endpoint"""
    return {
        "status": "Active",
        "core_model": CORE_MODEL,
        "vision_model": VISION_MODEL,
        "embedding_model": EMBEDDING_MODEL,
        "mode": "Async Non-Blocking"
    }


@app.post("/vision")
async def vision_endpoint(
    prompt: str = Form(...),
    image: UploadFile = File(...)
):
    """Vision endpoint for processing images and PDFs."""
    try:
        logger.info(f"Vision request - prompt: {prompt[:50]}..., file: {image.filename}")
        
        file_content = await image.read()
        
        if is_pdf(image):
            logger.info(f"Detected PDF: {image.filename}")
            extracted_text = await process_pdf_pipeline(file_content, prompt)
        else:
            logger.info(f"Processing image: {image.filename}")
            response = await client.generate(
                model=VISION_MODEL,
                prompt=prompt,
                images=[file_content],
                keep_alive=0
            )
            extracted_text = response['response']
        
        logger.info(f"Vision processing complete: {len(extracted_text)} chars")
        
        return {
            "response": extracted_text,
            "model": VISION_MODEL
        }
    
    except Exception as e:
        logger.error(f"Vision Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
async def chat_endpoint(request: dict):
    """
    ChatML-based chat endpoint using ollama.chat() API.
    
    Expected format matches core model training:
    {
        "messages": [
            {"role": "system", "content": "You are StudyMate. \n[PROFILE]\n- Subject: X\n- grade: Y\n\n[COURSE MATERIALS]\n..."},
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "..."},
            ...
        ],
        "model": "Studymate-core"  # optional
    }
    """
    try:
        messages = request.get("messages", [])
        model = request.get("model", CORE_MODEL)
        
        if not messages:
            raise HTTPException(status_code=400, detail="No messages provided")
        
        logger.info(f"Chat request: {len(messages)} messages, model: {model}")
        
        response = await client.chat(
            model=model,
            messages=messages,
            options={
                "temperature": 0.4,
                "top_p": 0.85,
                "repeat_penalty": 1.3,
                "num_ctx": 4096,
                "num_predict": 1024,
                "stop": ["<|im_end|>", "<|endoftext|>"]
            }
        )
        
        response_text = response['message']['content']
        response_text = clean_model_response(response_text)
        
        logger.info(f"Chat response generated: {len(response_text)} chars")
        
        return {
            "response": response_text,
            "model": model
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/utility/embed")
async def process_embedding(text: str):
    """Generate embedding vector for text."""
    try:
        logger.info(f"Generating embedding for text ({len(text)} chars)")
        
        response = await client.embeddings(
            model=EMBEDDING_MODEL,
            prompt=text,
            keep_alive=0
        )
        
        embedding = response['embedding']
        logger.info(f"Embedding generated: {len(embedding)} dimensions")
        
        return {"embedding": embedding}
    
    except Exception as e:
        logger.error(f"Embedding Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
