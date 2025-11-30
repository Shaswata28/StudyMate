"""
Chat router for handling AI chat requests with Supabase integration.
Implements chat endpoints with validation, rate limiting, error handling,
and chat history persistence to Supabase.
"""

from fastapi import APIRouter, Request, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import List, Optional
import logging

from models.schemas import ChatRequest, ChatResponse, ErrorResponse, Message
from services.gemini_service import (
    gemini_service,
    GeminiAPIError,
    GeminiTimeoutError,
    GeminiServiceError
)
from services.auth_service import get_current_user, get_current_user_optional, AuthUser
from services.supabase_client import get_user_client
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



@router.get("/courses/{course_id}/chat")
async def get_chat_history(
    course_id: str,
    user: AuthUser = Depends(get_current_user)
):
    """
    Get chat history for a specific course from Supabase.
    
    Retrieves all chat messages for the specified course, ordered chronologically.
    Only returns chat history for courses owned by the authenticated user.
    
    Args:
        course_id: UUID of the course
        user: Authenticated user from JWT token
        
    Returns:
        List of chat history records with message arrays
        
    Requirements: 7.1, 7.2, 7.4
    """
    try:
        client = get_user_client(user.access_token)
        
        # Verify course ownership
        course_result = client.table("courses").select("id").eq("id", course_id).eq("user_id", user.id).execute()
        if not course_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
        
        # Get chat history ordered by creation time (chronological)
        result = client.table("chat_history").select("*").eq("course_id", course_id).order("created_at", desc=False).execute()
        
        logger.info(f"Chat history retrieved for course: {course_id}, user: {user.id}")
        return result.data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chat history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat history"
        )


@router.post("/courses/{course_id}/chat", status_code=status.HTTP_201_CREATED)
async def save_chat_message(
    course_id: str,
    request: Request,
    chat_request: ChatRequest,
    user: AuthUser = Depends(get_current_user)
):
    """
    Save chat message to Supabase and get AI response.
    
    This endpoint combines the chat functionality with persistence:
    1. Verifies course ownership
    2. Sends message to Gemini AI
    3. Saves both user message and AI response to chat_history table
    
    The chat history is stored as a JSONB array of message objects.
    
    Args:
        course_id: UUID of the course
        request: FastAPI request object (for rate limiting)
        chat_request: Chat request with message and optional history
        user: Authenticated user from JWT token
        
    Returns:
        ChatResponse with AI response and timestamp
        
    Requirements: 7.1, 7.2, 7.4
    """
    try:
        client = get_user_client(user.access_token)
        
        # Verify course ownership
        course_result = client.table("courses").select("id").eq("id", course_id).eq("user_id", user.id).execute()
        if not course_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
        
        # Log incoming request
        logger.info(
            f"Chat request for course {course_id} - Message length: {len(chat_request.message)}, "
            f"History length: {len(chat_request.history)}, "
            f"Attachments: {len(chat_request.attachments)}"
        )
        
        # Call Gemini service with attachments
        response_text = gemini_service.generate_response(
            message=chat_request.message,
            history=chat_request.history if chat_request.history else None,
            attachments=chat_request.attachments if chat_request.attachments else None
        )
        
        # Prepare messages for storage
        user_message = {
            "role": "user",
            "content": chat_request.message
        }
        
        ai_message = {
            "role": "model",
            "content": response_text
        }
        
        # Save to chat_history table
        # Store as JSONB array: [user_message, ai_message]
        chat_result = client.table("chat_history").insert({
            "course_id": course_id,
            "history": [user_message, ai_message]
        }).execute()
        
        if not chat_result.data:
            logger.warning(f"Failed to save chat history for course: {course_id}")
        else:
            logger.info(f"Chat history saved for course: {course_id}, record: {chat_result.data[0]['id']}")
        
        # Create response with timestamp
        response = ChatResponse(
            response=response_text,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
        logger.info("Chat request completed successfully")
        return response
        
    except HTTPException:
        raise
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
