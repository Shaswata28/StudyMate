"""
Chat router for handling AI chat requests.
Implements the POST /api/chat endpoint with validation, rate limiting, and error handling.
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
import logging

from models.schemas import ChatRequest, ChatResponse, ErrorResponse
from services.gemini_service import (
    gemini_service,
    GeminiAPIError,
    GeminiTimeoutError,
    GeminiServiceError
)
from middleware.rate_limiter import limiter
from config import config

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
@limiter.limit(f"{config.RATE_LIMIT_REQUESTS}/{config.RATE_LIMIT_WINDOW}seconds")
async def chat_endpoint(request: Request, chat_request: ChatRequest):
    """
    Handle chat requests from the frontend.
    
    Validates the request, calls the Gemini API with message and history,
    and returns the AI response with a timestamp.
    
    Args:
        request: FastAPI request object (needed for rate limiting)
        chat_request: Validated ChatRequest containing message and optional history
        
    Returns:
        ChatResponse with AI response and timestamp
        
    Raises:
        HTTPException: For various error conditions (400, 500, 503)
    """
    try:
        # Log incoming request
        logger.info(
            f"Chat request received - Message length: {len(chat_request.message)}, "
            f"History length: {len(chat_request.history)}, "
            f"Attachments: {len(chat_request.attachments)}"
        )
        
        # Call Gemini service with attachments
        response_text = gemini_service.generate_response(
            message=chat_request.message,
            history=chat_request.history if chat_request.history else None,
            attachments=chat_request.attachments if chat_request.attachments else None
        )
        
        # Create response with timestamp
        response = ChatResponse(
            response=response_text,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
        logger.info("Chat request completed successfully")
        return response
        
    except GeminiTimeoutError as e:
        # Handle timeout errors (503)
        logger.error(f"Timeout error: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "error": str(e),
                "code": "TIMEOUT_ERROR"
            }
        )
        
    except GeminiAPIError as e:
        # Handle Gemini API errors (503)
        logger.error(f"Gemini API error: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "error": str(e),
                "code": "GEMINI_API_ERROR"
            }
        )
        
    except GeminiServiceError as e:
        # Handle general service errors (500)
        logger.error(f"Gemini service error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Something went wrong. Please try again.",
                "code": "SERVICE_ERROR"
            }
        )
        
    except Exception as e:
        # Handle unexpected errors (500)
        logger.error(f"Unexpected error in chat endpoint: {type(e).__name__}: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Something went wrong. Please try again.",
                "code": "INTERNAL_ERROR"
            }
        )
