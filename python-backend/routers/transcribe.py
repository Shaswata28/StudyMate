"""
Transcription router for handling audio transcription requests.
Forwards audio files to the AI Brain service for Whisper-based transcription.
"""

from fastapi import APIRouter, Request, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
import logging
import httpx
from typing import Optional

from middleware.rate_limiter import limiter
from config import config

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["transcription"])


@router.post("/transcribe")
@limiter.limit(f"{config.RATE_LIMIT_REQUESTS}/{config.RATE_LIMIT_WINDOW}seconds")
async def transcribe_audio(
    request: Request,
    audio: UploadFile = File(...)
):
    """
    Transcribe audio file using AI Brain's Whisper integration.
    
    Accepts an audio file, forwards it to the AI Brain service at /router endpoint,
    and returns the transcribed text.
    
    Args:
        request: FastAPI request object (needed for rate limiting)
        audio: Audio file to transcribe (max 25MB as per Whisper requirements)
        
    Returns:
        JSON response with transcribed text or error message
        
    Raises:
        HTTPException: For various error conditions (400, 500, 503)
        
    Requirements: 3.1, 5.1, 5.2
    """
    try:
        # Validate file was uploaded
        if not audio:
            logger.warning("No audio file provided in transcription request")
            return JSONResponse(
                status_code=400,
                content={
                    "text": "",
                    "success": False,
                    "error": "No audio file provided"
                }
            )
        
        # Check file size (25MB limit for Whisper)
        file_content = await audio.read()
        file_size_mb = len(file_content) / (1024 * 1024)
        
        if file_size_mb > 25:
            logger.warning(f"Audio file too large: {file_size_mb:.2f}MB")
            return JSONResponse(
                status_code=400,
                content={
                    "text": "",
                    "success": False,
                    "error": f"Audio file too large ({file_size_mb:.2f}MB). Maximum size is 25MB."
                }
            )
        
        logger.info(
            f"Transcription request received - "
            f"Filename: {audio.filename}, "
            f"Content-Type: {audio.content_type}, "
            f"Size: {file_size_mb:.2f}MB"
        )
        
        # Prepare multipart form data for AI Brain
        files = {
            "audio": (audio.filename, file_content, audio.content_type)
        }
        data = {
            "prompt": "Transcribe this audio"
        }
        
        # Forward to AI Brain service
        ai_brain_url = f"{config.AI_BRAIN_ENDPOINT}/router"
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    ai_brain_url,
                    files=files,
                    data=data
                )
                
                if response.status_code != 200:
                    logger.error(f"AI Brain service returned status {response.status_code}")
                    return JSONResponse(
                        status_code=503,
                        content={
                            "text": "",
                            "success": False,
                            "error": f"AI Brain service returned status {response.status_code}"
                        }
                    )
                
                # Parse AI Brain response
                response_data = response.json()
                transcribed_text = response_data.get("response", "") or response_data.get("text", "")
                
                logger.info(f"Transcription completed successfully - Text length: {len(transcribed_text)}")
                
                return JSONResponse(
                    status_code=200,
                    content={
                        "text": transcribed_text,
                        "success": True
                    }
                )
                
            except httpx.ConnectError as e:
                logger.error(f"Failed to connect to AI Brain service: {str(e)}")
                return JSONResponse(
                    status_code=503,
                    content={
                        "text": "",
                        "success": False,
                        "error": "AI Brain service is unavailable"
                    }
                )
                
            except httpx.TimeoutException as e:
                logger.error(f"Transcription request timed out: {str(e)}")
                return JSONResponse(
                    status_code=503,
                    content={
                        "text": "",
                        "success": False,
                        "error": "Transcription request timed out"
                    }
                )
                
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error in transcription endpoint: {type(e).__name__}: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "text": "",
                "success": False,
                "error": "Transcription failed"
            }
        )
